from __future__ import annotations

import re
from pathlib import Path

from qedsoft.models import VerificationDiagnostic, VerificationResult

from .tools import ExternalToolRunner


class LeanVerifier:
    """Verify generated Lean contracts when Lean4 is available."""

    def __init__(self, tool_runner: ExternalToolRunner | None = None) -> None:
        self.tool_runner = tool_runner or ExternalToolRunner()

    def verify(self, lean_path: Path, use_external_tools: bool = True) -> VerificationResult:
        content = lean_path.read_text(encoding="utf-8")
        diagnostics = self._static_diagnostics(content)
        metrics = {
            "theorems": len(re.findall(r"\btheorem\b", content)),
            "definitions": len(re.findall(r"\bdef\b", content)),
            "sorry_count": len(re.findall(r"\bsorry\b", content)),
        }

        raw_output = ""
        if use_external_tools and self.tool_runner.available("lean"):
            code, output = self.tool_runner.run(["lean", str(lean_path)], cwd=lean_path.parent)
            raw_output = output
            metrics["lean_exit_code"] = code
            if code != 0:
                diagnostics.append(
                    VerificationDiagnostic(
                        tool="lean",
                        severity="error",
                        message=output.strip()[:1000] or "Lean verification failed.",
                    )
                )
        elif use_external_tools:
            diagnostics.append(
                VerificationDiagnostic(
                    tool="lean",
                    severity="info",
                    message="Lean executable not found; generated contract received static checks only.",
                )
            )
            metrics["lean"] = "skipped"

        success = not any(diag.severity == "error" for diag in diagnostics)
        return VerificationResult(
            tool="lean",
            success=success,
            diagnostics=diagnostics,
            metrics=metrics,
            raw_output=raw_output,
        )

    def _static_diagnostics(self, content: str) -> list[VerificationDiagnostic]:
        diagnostics: list[VerificationDiagnostic] = []
        if content.count("(") != content.count(")"):
            diagnostics.append(
                VerificationDiagnostic(
                    tool="qedsoft-lean-static",
                    severity="error",
                    message="Unbalanced parentheses in Lean contract.",
                )
            )
        if "sorry" in content:
            diagnostics.append(
                VerificationDiagnostic(
                    tool="qedsoft-lean-static",
                    severity="warning",
                    message="Lean contract contains sorry placeholders.",
                    hint="Use QEDAI proof search to discharge these obligations.",
                )
            )
        return diagnostics
