from __future__ import annotations

import re
from pathlib import Path

from qedsoft.models import DesignModel, VerificationDiagnostic, VerificationResult

from .tools import ExternalToolRunner


class SVASyntaxVerifier:
    """Static SVA checks plus optional simulator/linter integration."""

    SIGNAL_TOKEN = re.compile(r"\b[A-Za-z_]\w*\b")

    def __init__(self, tool_runner: ExternalToolRunner | None = None) -> None:
        self.tool_runner = tool_runner or ExternalToolRunner()

    def verify(
        self,
        sva_path: Path,
        model: DesignModel,
        rtl_path: Path | None = None,
        use_external_tools: bool = True,
    ) -> VerificationResult:
        content = sva_path.read_text(encoding="utf-8")
        diagnostics = self._static_diagnostics(content, model)
        metrics = {
            "properties": len(re.findall(r"^\s*property\b", content, flags=re.M)),
            "assertions": len(re.findall(r"\bassert\s+property\b", content)),
            "covers": len(re.findall(r"\bcover\s+property\b", content)),
        }

        raw_output = ""
        if use_external_tools:
            external = self._run_external_lint(sva_path, rtl_path)
            if external:
                diagnostics.extend(external.diagnostics)
                metrics.update(external.metrics)
                raw_output = external.raw_output

        success = not any(diag.severity == "error" for diag in diagnostics)
        return VerificationResult(
            tool="qedsoft-sva-static",
            success=success,
            diagnostics=diagnostics,
            metrics=metrics,
            raw_output=raw_output,
        )

    def _static_diagnostics(self, content: str, model: DesignModel) -> list[VerificationDiagnostic]:
        diagnostics: list[VerificationDiagnostic] = []
        if content.count("(") != content.count(")"):
            diagnostics.append(
                VerificationDiagnostic(
                    tool="qedsoft-sva-static",
                    severity="error",
                    message="Unbalanced parentheses in generated SVA.",
                    hint="Run SERA repair or inspect property expressions.",
                )
            )

        property_count = len(re.findall(r"^\s*property\b", content, flags=re.M))
        endproperty_count = len(re.findall(r"^\s*endproperty\b", content, flags=re.M))
        if property_count != endproperty_count:
            diagnostics.append(
                VerificationDiagnostic(
                    tool="qedsoft-sva-static",
                    severity="error",
                    message=f"property/endproperty mismatch: {property_count}/{endproperty_count}.",
                )
            )

        if "manual-review-required" in content:
            diagnostics.append(
                VerificationDiagnostic(
                    tool="qedsoft-sva-static",
                    severity="warning",
                    message="At least one property used a manual-review fallback.",
                    hint="Clarify the requirement or add signal aliases to improve formalization.",
                )
            )

        known_symbols = set(model.signals) | {
            model.clock,
            model.reset,
            "property",
            "endproperty",
            "assert",
            "cover",
            "disable",
            "iff",
            "posedge",
            "logic",
            "input",
            "output",
            "inout",
            "module",
            "endmodule",
            "default",
            "clocking",
            "endclocking",
            "else",
            "error",
            "bind",
            "QEDSoft",
            "violation",
        }
        for line_no, line in enumerate(content.splitlines(), start=1):
            if line.strip().startswith("//"):
                continue
            for token in self.SIGNAL_TOKEN.findall(line):
                if token in known_symbols or token.startswith("qedsoft") or token[0].isdigit():
                    continue
                if token in {
                    "b0",
                    "b1",
                    "isunknown",
                    "rose",
                    "stable",
                    "past",
                    "default_nettype",
                    "wire",
                    "none",
                    "parameter",
                    "int",
                    "DEPTH",
                }:
                    continue
                if token.isupper() or token in {model.top_module, f"{model.top_module}_qedsoft_sva"}:
                    continue
                # Avoid noise from string literals.
                if f'"{token}' in line or f'{token}"' in line:
                    continue
                diagnostics.append(
                    VerificationDiagnostic(
                        tool="qedsoft-sva-static",
                        severity="warning",
                        message=f"Symbol '{token}' may not map to a known RTL signal.",
                        line=line_no,
                        hint="Check signal extraction or provide a better RTL/spec mapping.",
                    )
                )
        return diagnostics

    def _run_external_lint(
        self, sva_path: Path, rtl_path: Path | None
    ) -> VerificationResult | None:
        cwd = sva_path.parent
        if rtl_path and self.tool_runner.available("iverilog"):
            args = ["iverilog", "-g2012", "-t", "null", str(rtl_path), str(sva_path)]
            code, output = self.tool_runner.run(args, cwd=cwd)
            return self._external_result("iverilog", code, output)
        if self.tool_runner.available("verilator"):
            args = ["verilator", "--lint-only", "--sv", str(sva_path)]
            code, output = self.tool_runner.run(args, cwd=cwd)
            return self._external_result("verilator", code, output)
        return VerificationResult(
            tool="external-sva-lint",
            success=True,
            diagnostics=[
                VerificationDiagnostic(
                    tool="external-sva-lint",
                    severity="info",
                    message="No external SVA linter found; static checks only.",
                )
            ],
            metrics={"external_lint": "skipped"},
        )

    def _external_result(self, tool: str, code: int, output: str) -> VerificationResult:
        severity = "error" if code else "info"
        diagnostics = []
        if output.strip():
            diagnostics.append(
                VerificationDiagnostic(
                    tool=tool,
                    severity=severity,  # type: ignore[arg-type]
                    message=output.strip()[:1000],
                )
            )
        return VerificationResult(
            tool=tool,
            success=code == 0,
            diagnostics=diagnostics,
            metrics={f"{tool}_exit_code": code},
            raw_output=output,
        )
