from __future__ import annotations

import difflib
import re

from qedsoft.models import DesignModel, RepairAction, VerificationResult


class StructuredRepairEngine:
    """Cost-ordered verifier-guided repair inspired by QEDAI SERA-VGP."""

    def repair_sva(
        self,
        content: str,
        model: DesignModel,
        verification_result: VerificationResult,
    ) -> tuple[str, list[RepairAction]]:
        actions: list[RepairAction] = []
        repaired = content

        repaired, action = self._repair_unbalanced_parentheses(repaired)
        if action:
            actions.append(action)

        repaired, action = self._repair_unknown_signal_names(repaired, model, verification_result)
        if action:
            actions.append(action)

        repaired, action = self._promote_manual_review_guards(repaired, model)
        if action:
            actions.append(action)

        repaired, action = self._repair_property_blocks(repaired)
        if action:
            actions.append(action)

        return repaired, actions

    def _repair_unbalanced_parentheses(self, content: str) -> tuple[str, RepairAction | None]:
        delta = content.count("(") - content.count(")")
        if delta <= 0:
            return content, None
        repaired = content
        for _ in range(delta):
            repaired += ")"
        return repaired, RepairAction(
            artifact_kind="sva",
            description=f"Balanced generated SVA by appending {delta} closing parenthesis token(s).",
            applied=True,
            diagnostics_resolved=1,
        )

    def _repair_unknown_signal_names(
        self,
        content: str,
        model: DesignModel,
        verification_result: VerificationResult,
    ) -> tuple[str, RepairAction | None]:
        known = list(model.signals)
        replacements: dict[str, str] = {}
        for diagnostic in verification_result.diagnostics:
            match = re.search(r"Symbol '([^']+)'", diagnostic.message)
            if not match:
                continue
            symbol = match.group(1)
            close = difflib.get_close_matches(symbol, known, n=1, cutoff=0.78)
            if close:
                replacements[symbol] = close[0]

        if not replacements:
            return content, None

        repaired = content
        for old, new in replacements.items():
            repaired = re.sub(rf"(?<![A-Za-z0-9_]){re.escape(old)}(?![A-Za-z0-9_])", new, repaired)

        return repaired, RepairAction(
            artifact_kind="sva",
            description=f"Mapped likely signal aliases: {replacements}.",
            applied=True,
            diagnostics_resolved=len(replacements),
        )

    def _promote_manual_review_guards(self, content: str, model: DesignModel) -> tuple[str, RepairAction | None]:
        if "manual-review-required" not in content:
            return content, None
        replacement_signal = self._first_output_signal(model) or self._first_non_clock_signal(model)
        if not replacement_signal:
            return content, None
        repaired = content.replace("1'b1", f"!$isunknown({replacement_signal})", 1)
        repaired = repaired.replace(
            "fallback: manual-review-required",
            f"fallback repaired to known-value guard on {replacement_signal}",
            1,
        )
        return repaired, RepairAction(
            artifact_kind="sva",
            description=f"Replaced a vacuous fallback property with a known-value guard on {replacement_signal}.",
            applied=True,
            diagnostics_resolved=1,
        )

    def _repair_property_blocks(self, content: str) -> tuple[str, RepairAction | None]:
        property_count = len(re.findall(r"^\s*property\b", content, flags=re.M))
        end_count = len(re.findall(r"^\s*endproperty\b", content, flags=re.M))
        if property_count <= end_count:
            return content, None
        repaired = content + "\n  endproperty\n"
        return repaired, RepairAction(
            artifact_kind="sva",
            description="Added a missing endproperty marker.",
            applied=True,
            diagnostics_resolved=1,
        )

    def _first_output_signal(self, model: DesignModel) -> str | None:
        for signal in model.signals.values():
            if signal.direction == "output":
                return signal.name
        return None

    def _first_non_clock_signal(self, model: DesignModel) -> str | None:
        for signal in model.signals.values():
            if signal.name not in {model.clock, model.reset}:
                return signal.name
        return None
