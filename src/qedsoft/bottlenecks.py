from __future__ import annotations

from qedsoft.models import BottleneckReport, FormalizationBundle, VerificationResult


class BottleneckAnalyzer:
    """Identify verification bottlenecks exposed by the generated flow."""

    def analyze(
        self,
        bundle: FormalizationBundle,
        verification_results: list[VerificationResult],
    ) -> BottleneckReport:
        model = bundle.model
        report = BottleneckReport()

        total_requirements = len(model.requirements)
        mapped_requirements = sum(1 for req in model.requirements if req.signals)
        low_confidence = [req for req in model.requirements if req.confidence < 0.6]
        report.coverage_metrics = {
            "requirements": total_requirements,
            "subgoals": len(bundle.subgoals),
            "requirements_with_signal_mapping": mapped_requirements,
            "mapping_coverage": round(mapped_requirements / total_requirements, 3)
            if total_requirements
            else 0.0,
            "low_confidence_requirements": len(low_confidence),
        }

        for req in low_confidence:
            report.spec_ambiguity.append(f"{req.id}: {req.text}")
        for mention in bundle.strategy.get("unmapped_mentions", []):
            report.signal_mapping_gaps.append(mention)

        for result in verification_results:
            for diagnostic in result.diagnostics:
                if diagnostic.severity == "warning":
                    report.assertion_quality_risks.append(f"{result.tool}: {diagnostic.message}")
                if diagnostic.severity == "info" and "not found" in diagnostic.message.lower():
                    report.toolchain_gaps.append(f"{result.tool}: {diagnostic.message}")
                if diagnostic.severity == "info" and "static checks only" in diagnostic.message.lower():
                    report.toolchain_gaps.append(f"{result.tool}: {diagnostic.message}")
                if diagnostic.severity == "error":
                    report.assertion_quality_risks.append(f"{result.tool}: {diagnostic.message}")

        report.recommendations = self._recommend(report)
        return report

    def _recommend(self, report: BottleneckReport) -> list[str]:
        recommendations: list[str] = []
        if report.spec_ambiguity:
            recommendations.append(
                "Clarify low-confidence requirements with explicit trigger, response, signal, and cycle bound."
            )
        if report.signal_mapping_gaps:
            recommendations.append(
                "Add a signal dictionary or RTL port comments so natural-language names map to HDL names."
            )
        if report.toolchain_gaps:
            recommendations.append(
                "Install Lean4 and an SV/formal tool such as iverilog, Verilator, or SymbiYosys for stronger checks."
            )
        if report.assertion_quality_risks:
            recommendations.append(
                "Review warning-bearing assertions before signoff; run seeded-bug mutation tests to measure bug catch rate."
            )
        if not recommendations:
            recommendations.append("No major bottleneck detected in this run.")
        return recommendations
