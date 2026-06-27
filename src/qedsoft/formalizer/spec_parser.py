from __future__ import annotations

import json
import re
from dataclasses import dataclass

from qedsoft.models import DesignModel, Requirement, Signal


@dataclass
class ParsedSpec:
    model: DesignModel
    unmapped_mentions: list[str]


class HardwareSpecParser:
    """Extract a lightweight design model from natural language and RTL.

    LLM is used first for requirement extraction; regex is the fallback.
    """

    SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
    RTL_MODULE = re.compile(r"\bmodule\s+([A-Za-z_]\w*)\s*(?:#\s*\(.*?\))?\s*\((.*?)\)\s*;", re.S)
    RTL_PORT_LINE = re.compile(
        r"\b(input|output|inout)\b\s+(?:wire|logic|reg|signed|unsigned|\s)*"
        r"(?P<width>\[[^\]]+\])?\s*(?P<names>[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)",
        re.I,
    )
    NL_SIGNAL_LINE = re.compile(
        r"\b(?P<direction>input|output|inout|internal|register|reg)\b"
        r"(?:\s+(?P<width>\d+)[-\s]*bit)?\s+"
        r"(?P<name>[A-Za-z_]\w*)",
        re.I,
    )

    def parse(
        self,
        spec_text: str,
        rtl_text: str = "",
        design_name: str = "qedsoft_design",
        top_module: str | None = None,
        clock: str | None = None,
        reset: str | None = None,
        reset_active_low: bool | None = None,
    ) -> ParsedSpec:
        rtl_module, rtl_ports = self._extract_rtl_ports(rtl_text)
        nl_signals = self._extract_nl_signals(spec_text)

        signals = {signal.name: signal for signal in rtl_ports}
        for signal in nl_signals:
            existing = signals.get(signal.name)
            if existing is None:
                signals[signal.name] = signal
            elif signal.width > existing.width:
                existing.width = signal.width

        inferred_top = top_module or rtl_module or self._infer_design_name(spec_text) or design_name
        inferred_clock = clock or self._infer_clock(signals, spec_text)
        inferred_reset = reset or self._infer_reset(signals, spec_text)
        active_low = (
            reset_active_low
            if reset_active_low is not None
            else inferred_reset.endswith("_n") or "active low" in spec_text.lower()
        )

        requirements = self._extract_requirements(spec_text, signals)
        assumptions = self._extract_assumptions(spec_text)
        model = DesignModel(
            name=design_name,
            top_module=inferred_top,
            clock=inferred_clock,
            reset=inferred_reset,
            reset_active_low=active_low,
            signals=signals,
            requirements=requirements,
            assumptions=assumptions,
        )

        unmapped_mentions = self._find_unmapped_signal_mentions(requirements, signals)
        return ParsedSpec(model=model, unmapped_mentions=unmapped_mentions)

    # ------------------------------------------------------------------
    # Requirement extraction — LLM first, regex fallback
    # ------------------------------------------------------------------

    def _extract_requirements(self, spec_text: str, signals: dict[str, Signal]) -> list[Requirement]:
        llm_reqs = self._llm_extract_requirements(spec_text, signals)
        if llm_reqs:
            return llm_reqs
        return self._regex_extract_requirements(spec_text, signals)

    def _llm_extract_requirements(self, spec_text: str, signals: dict[str, Signal]) -> list[Requirement]:
        try:
            from qedsoft.llm_client import chat

            signal_names = ", ".join(signals.keys()) if signals else "none detected"
            prompt = (
                "Extract all formal verification requirements from this hardware specification.\n\n"
                f"Specification:\n{spec_text}\n\n"
                f"Available RTL signals: {signal_names}\n\n"
                "Return a JSON array where each object has:\n"
                '- "text": the requirement statement (string)\n'
                '- "category": one of "reset", "safety", "protocol", "temporal", "equivalence", "functional"\n'
                '- "signals": list of signal names from the available signals that are involved\n'
                '- "latency_cycles": integer or null\n'
                '- "confidence": float 0.0-1.0\n\n'
                "Return ONLY the JSON array, no explanation."
            )
            response = chat(
                prompt,
                system="You are a hardware verification engineer. Always respond with valid JSON only.",
            )
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r"```(?:json)?\n?", "", response).rstrip("`").strip()

            items = json.loads(response)
            requirements: list[Requirement] = []
            for index, item in enumerate(items, start=1):
                requirements.append(
                    Requirement(
                        id=f"REQ-{index:03d}",
                        text=item.get("text", ""),
                        category=item.get("category", "functional"),
                        signals=[s for s in item.get("signals", []) if s in signals],
                        latency_cycles=item.get("latency_cycles"),
                        confidence=float(item.get("confidence", 0.7)),
                    )
                )
            return requirements
        except Exception:
            return []

    def _regex_extract_requirements(self, spec_text: str, signals: dict[str, Signal]) -> list[Requirement]:
        requirements: list[Requirement] = []
        candidates: list[str] = []
        for part in self.SENTENCE_SPLIT.split(spec_text):
            text = re.sub(r"^\s*[-*]\s*", "", part.strip())
            if not text:
                continue
            lower = text.lower()
            if lower.startswith("module ") and " has clock " in lower:
                continue
            if any(
                keyword in lower
                for keyword in [
                    "must", "shall", "should", "never", "always", "within",
                    "after", "before", "when", "if ", "reset", "assume",
                ]
            ):
                if "assume" not in lower and "assumption" not in lower:
                    candidates.append(text)

        for index, text in enumerate(candidates, start=1):
            category = self._classify_requirement(text)
            referenced = self._map_signals(text, signals)
            latency = self._extract_latency(text)
            confidence = self._score_requirement(text, referenced, category)
            requirements.append(
                Requirement(
                    id=f"REQ-{index:03d}",
                    text=text,
                    category=category,
                    signals=referenced,
                    latency_cycles=latency,
                    confidence=confidence,
                )
            )
        return requirements

    # ------------------------------------------------------------------
    # RTL / NL signal extraction (unchanged)
    # ------------------------------------------------------------------

    def _extract_rtl_ports(self, rtl_text: str) -> tuple[str | None, list[Signal]]:
        if not rtl_text.strip():
            return None, []

        module_name = None
        port_blob = rtl_text
        module_match = self.RTL_MODULE.search(rtl_text)
        if module_match:
            module_name = module_match.group(1)
            port_blob = module_match.group(2)

        ports: list[Signal] = []
        for match in self.RTL_PORT_LINE.finditer(port_blob):
            width = self._width_from_range(match.group("width") or "")
            for raw_name in match.group("names").split(","):
                name = raw_name.strip()
                if name:
                    ports.append(
                        Signal(
                            name=name,
                            direction=match.group(1).lower(),  # type: ignore[arg-type]
                            width=width,
                            kind="logic",
                            description="extracted from RTL port list",
                        )
                    )
        return module_name, self._dedupe_signals(ports)

    def _extract_nl_signals(self, spec_text: str) -> list[Signal]:
        signals: list[Signal] = []
        for line in spec_text.splitlines():
            match = self.NL_SIGNAL_LINE.search(line)
            if not match:
                continue
            direction = match.group("direction").lower()
            if direction in {"register", "reg"}:
                direction = "internal"
            width = int(match.group("width") or "1")
            signals.append(
                Signal(
                    name=match.group("name"),
                    direction=direction,  # type: ignore[arg-type]
                    width=width,
                    description="extracted from natural-language spec",
                )
            )
        return self._dedupe_signals(signals)

    def _extract_assumptions(self, spec_text: str) -> list[str]:
        assumptions: list[str] = []
        for line in spec_text.splitlines():
            lower = line.lower()
            if "assume" in lower or "assumption" in lower:
                assumptions.append(line.strip(" -*"))
        return assumptions

    def _find_unmapped_signal_mentions(
        self, requirements: list[Requirement], signals: dict[str, Signal]
    ) -> list[str]:
        unmapped: set[str] = set()
        signal_names = set(signals)
        lower_signal_names = {name.lower() for name in signals}
        ignore = {
            "the", "when", "must", "shall", "should", "never", "always",
            "after", "before", "within", "cycles", "cycle", "reset",
            "asserted", "deasserted", "active", "high", "low",
        }
        for req in requirements:
            for token in re.findall(r"\b[A-Za-z_]\w*\b", req.text):
                if token in signal_names or token.lower() in lower_signal_names or token.lower() in ignore:
                    continue
                if "_" in token or token.lower().endswith(("en", "valid", "ready", "full", "empty")):
                    unmapped.add(token)
        return sorted(unmapped)

    def _map_signals(self, text: str, signals: dict[str, Signal]) -> list[str]:
        referenced: list[str] = []
        lowered = f" {text.lower()} "
        for name in signals:
            pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name.lower())}(?![A-Za-z0-9_])")
            if pattern.search(lowered):
                referenced.append(name)
        return referenced

    def _classify_requirement(self, text: str) -> str:
        lower = text.lower()
        if "reset" in lower:
            return "reset"
        if "never" in lower or "no " in lower or "must not" in lower:
            return "safety"
        if "within" in lower or "eventually" in lower or "after" in lower:
            return "temporal"
        if any(word in lower for word in ["valid", "ready", "req", "ack", "grant"]):
            return "protocol"
        if any(word in lower for word in ["equivalent", "same as", "matches"]):
            return "equivalence"
        return "functional"

    def _extract_latency(self, text: str) -> int | None:
        lower = text.lower()
        match = re.search(r"within\s+(\d+)\s+cycles?", lower)
        if match:
            return int(match.group(1))
        if "next cycle" in lower or "one cycle" in lower:
            return 1
        return None

    def _score_requirement(self, text: str, signals: list[str], category: str) -> float:
        score = 0.35
        if signals:
            score += 0.3
        if category != "functional":
            score += 0.15
        if any(keyword in text.lower() for keyword in ["must", "shall", "never", "within"]):
            score += 0.15
        if len(text.split()) > 28:
            score -= 0.1
        return max(0.05, min(0.95, score))

    def _infer_clock(self, signals: dict[str, Signal], spec_text: str) -> str:
        for candidate in ["clk", "clock", "aclk"]:
            if candidate in signals:
                return candidate
        match = re.search(r"\bclock\s+(?:signal\s+)?([A-Za-z_]\w*)", spec_text, re.I)
        return match.group(1) if match else "clk"

    def _infer_reset(self, signals: dict[str, Signal], spec_text: str) -> str:
        for candidate in ["rst_n", "reset_n", "rst", "reset", "aresetn"]:
            if candidate in signals:
                return candidate
        match = re.search(r"\breset\s+(?:signal\s+)?([A-Za-z_]\w*)", spec_text, re.I)
        return match.group(1) if match else "rst_n"

    def _infer_design_name(self, spec_text: str) -> str | None:
        match = re.search(r"\bmodule\s+([A-Za-z_]\w*)", spec_text, re.I)
        return match.group(1) if match else None

    def _width_from_range(self, width_range: str) -> int:
        if not width_range:
            return 1
        if re.search(r"[A-Za-z_]", width_range):
            return 1
        numbers = [int(value) for value in re.findall(r"\d+", width_range)]
        if len(numbers) >= 2:
            return abs(numbers[0] - numbers[1]) + 1
        return 1

    def _dedupe_signals(self, signals: list[Signal]) -> list[Signal]:
        merged: dict[str, Signal] = {}
        for signal in signals:
            if signal.name.lower() in {"input", "output", "inout", "logic", "wire", "reg"}:
                continue
            merged[signal.name] = signal
        return list(merged.values())
