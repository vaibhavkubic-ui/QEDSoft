from __future__ import annotations

import json
from pathlib import Path

from qedsoft.bottlenecks import BottleneckAnalyzer
from qedsoft.formalizer import QEDAIChipAutoformalizer
from qedsoft.generators import LeanContractGenerator, SVAGenerator
from qedsoft.learning import FeedbackMemory
from qedsoft.models import Artifact, ProjectConfig, QEDSoftResult
from qedsoft.repair import StructuredRepairEngine
from qedsoft.reports import MarkdownReportWriter
from qedsoft.verifiers import LeanVerifier, SVASyntaxVerifier


class QEDSoft:
    """End-to-end QEDAI-powered chip verification orchestrator."""

    def __init__(self, config: ProjectConfig | None = None) -> None:
        self.config = config or ProjectConfig()
        self.autoformalizer = QEDAIChipAutoformalizer()
        self.sva_generator = SVAGenerator()
        self.lean_generator = LeanContractGenerator()
        self.sva_verifier = SVASyntaxVerifier()
        self.lean_verifier = LeanVerifier()
        self.repair_engine = StructuredRepairEngine()
        self.bottleneck_analyzer = BottleneckAnalyzer()
        self.report_writer = MarkdownReportWriter()

    def run_from_paths(
        self,
        spec_path: Path,
        rtl_path: Path | None = None,
        output_dir: Path | None = None,
    ) -> QEDSoftResult:
        spec_text = spec_path.read_text(encoding="utf-8")
        rtl_text = rtl_path.read_text(encoding="utf-8") if rtl_path else ""
        out_dir = output_dir or Path("runs") / spec_path.stem
        return self.run(
            spec_text=spec_text,
            rtl_text=rtl_text,
            output_dir=out_dir,
            design_name=spec_path.stem,
            rtl_path=rtl_path,
        )

    def run(
        self,
        spec_text: str,
        rtl_text: str = "",
        output_dir: Path | str = "runs/qedsoft",
        design_name: str = "qedsoft_design",
        rtl_path: Path | None = None,
    ) -> QEDSoftResult:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        formalization = self.autoformalizer.formalize(
            spec_text=spec_text,
            rtl_text=rtl_text,
            design_name=design_name,
            top_module=self.config.top_module,
            clock=self.config.clock,
            reset=self.config.reset,
            reset_active_low=self.config.reset_active_low,
        )

        sva_content, bind_content = self.sva_generator.generate(formalization)
        lean_content = self.lean_generator.generate(formalization)

        sva_path = output_dir / f"{formalization.model.top_module}_qedsoft_sva.sv"
        bind_path = output_dir / f"{formalization.model.top_module}_qedsoft_bind.sv"
        lean_path = output_dir / f"{formalization.model.top_module}_qedsoft_contract.lean"

        sva_path.write_text(sva_content, encoding="utf-8")
        bind_path.write_text(bind_content, encoding="utf-8")
        lean_path.write_text(lean_content, encoding="utf-8")

        artifacts = [
            Artifact(kind="sva", path=sva_path, content=sva_content),
            Artifact(kind="bind", path=bind_path, content=bind_content),
            Artifact(kind="lean", path=lean_path, content=lean_content),
        ]

        repair_actions = []
        verification_results = [
            self.sva_verifier.verify(
                sva_path,
                formalization.model,
                rtl_path=rtl_path,
                use_external_tools=self.config.use_external_tools,
            )
        ]

        for _round in range(max(0, self.config.max_repair_rounds)):
            current_sva_result = verification_results[-1]
            if current_sva_result.success and not self._has_repairable_warnings(current_sva_result):
                break
            repaired_sva, actions = self.repair_engine.repair_sva(
                sva_path.read_text(encoding="utf-8"),
                formalization.model,
                current_sva_result,
            )
            applied = [action for action in actions if action.applied]
            if not applied:
                break
            repair_actions.extend(applied)
            sva_path.write_text(repaired_sva, encoding="utf-8")
            artifacts[0] = Artifact(kind="sva", path=sva_path, content=repaired_sva)
            verification_results.append(
                self.sva_verifier.verify(
                    sva_path,
                    formalization.model,
                    rtl_path=rtl_path,
                    use_external_tools=self.config.use_external_tools,
                )
            )

        verification_results.append(
            self.lean_verifier.verify(lean_path, use_external_tools=self.config.use_external_tools)
        )

        bottleneck_report = self.bottleneck_analyzer.analyze(formalization, verification_results)
        success = all(result.success for result in verification_results)

        result = QEDSoftResult(
            success=success,
            output_dir=output_dir,
            formalization=formalization,
            artifacts=artifacts,
            verification_results=verification_results,
            repair_actions=repair_actions,
            bottleneck_report=bottleneck_report,
        )

        report_path = output_dir / "qedsoft_report.md"
        report_content = self.report_writer.render(result)
        report_path.write_text(report_content, encoding="utf-8")
        result.artifacts.append(Artifact(kind="report", path=report_path, content=report_content))

        metadata_path = output_dir / "qedsoft_result.json"
        metadata_content = json.dumps(result.to_dict(), indent=2)
        metadata_path.write_text(metadata_content, encoding="utf-8")
        result.artifacts.append(Artifact(kind="metadata", path=metadata_path, content=metadata_content))

        if self.config.memory_path:
            FeedbackMemory(self.config.memory_path).append_result(result)

        return result

    def _has_repairable_warnings(self, result) -> bool:
        return any(
            "manual-review fallback" in diagnostic.message
            or "may not map to a known RTL signal" in diagnostic.message
            for diagnostic in result.diagnostics
        )
