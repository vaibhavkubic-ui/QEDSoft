from __future__ import annotations

import json

from qedsoft.models import QEDSoftResult


class MarkdownReportWriter:
    def render(self, result: QEDSoftResult) -> str:
        model = result.formalization.model
        lines = [
            "# QEDSoft Verification Report",
            "",
            f"- Top module: `{model.top_module}`",
            f"- Clock: `{model.clock}`",
            f"- Reset: `{model.reset}` ({'active low' if model.reset_active_low else 'active high'})",
            f"- Signals: {len(model.signals)}",
            f"- Requirements: {len(model.requirements)}",
            f"- Subgoals: {len(result.formalization.subgoals)}",
            f"- Overall success: `{result.success}`",
            "",
            "## Generated Artifacts",
            "",
        ]
        for artifact in result.artifacts:
            lines.append(f"- `{artifact.kind}`: `{artifact.path}`")

        lines.extend(["", "## Verification Results", ""])
        for verification in result.verification_results:
            lines.append(f"### {verification.tool}")
            lines.append(f"- Success: `{verification.success}`")
            lines.append(f"- Metrics: `{json.dumps(verification.metrics)}`")
            for diagnostic in verification.diagnostics:
                location = f" line {diagnostic.line}" if diagnostic.line else ""
                lines.append(f"- {diagnostic.severity.upper()}{location}: {diagnostic.message}")
            lines.append("")

        lines.extend(["## Bottleneck Report", ""])
        report = result.bottleneck_report
        lines.append(f"- Coverage: `{json.dumps(report.coverage_metrics)}`")
        self._section(lines, "Spec Ambiguity", report.spec_ambiguity)
        self._section(lines, "Signal Mapping Gaps", report.signal_mapping_gaps)
        self._section(lines, "Assertion Quality Risks", report.assertion_quality_risks)
        self._section(lines, "Toolchain Gaps", report.toolchain_gaps)
        self._section(lines, "Recommendations", report.recommendations)

        lines.extend(["", "## QEDAI Architecture Mapping", ""])
        for key, value in result.formalization.strategy.get("qedai_mapping", {}).items():
            lines.append(f"- `{key}`: {value}")
        lines.append("")
        return "\n".join(lines)

    def _section(self, lines: list[str], title: str, values: list[str]) -> None:
        lines.extend(["", f"### {title}", ""])
        if not values:
            lines.append("- None")
            return
        for value in values:
            lines.append(f"- {value}")
