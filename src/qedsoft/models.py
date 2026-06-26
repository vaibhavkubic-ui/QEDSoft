from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


Direction = Literal["input", "output", "inout", "internal", "unknown"]
ArtifactKind = Literal["sva", "lean", "report", "bind", "metadata"]
Severity = Literal["info", "warning", "error"]


@dataclass
class Signal:
    name: str
    direction: Direction = "unknown"
    width: int = 1
    kind: str = "logic"
    description: str = ""


@dataclass
class Requirement:
    id: str
    text: str
    category: str
    signals: list[str] = field(default_factory=list)
    latency_cycles: int | None = None
    confidence: float = 0.5
    source: str = "natural_language"


@dataclass
class VerificationSubgoal:
    id: str
    requirement_id: str
    statement: str
    artifact_type: Literal["sva", "lean", "both"] = "both"
    signals: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    priority: int = 5
    confidence: float = 0.5


@dataclass
class DesignModel:
    name: str
    top_module: str
    clock: str = "clk"
    reset: str = "rst_n"
    reset_active_low: bool = True
    signals: dict[str, Signal] = field(default_factory=dict)
    requirements: list[Requirement] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    def port_names(self) -> list[str]:
        return [
            name
            for name, signal in self.signals.items()
            if signal.direction in {"input", "output", "inout"}
        ]


@dataclass
class FormalizationBundle:
    model: DesignModel
    subgoals: list[VerificationSubgoal]
    strategy: dict[str, Any] = field(default_factory=dict)


@dataclass
class Artifact:
    kind: ArtifactKind
    path: Path
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationDiagnostic:
    tool: str
    severity: Severity
    message: str
    line: int | None = None
    hint: str | None = None


@dataclass
class VerificationResult:
    tool: str
    success: bool
    diagnostics: list[VerificationDiagnostic] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    raw_output: str = ""


@dataclass
class RepairAction:
    artifact_kind: str
    description: str
    applied: bool
    diagnostics_resolved: int = 0


@dataclass
class BottleneckReport:
    spec_ambiguity: list[str] = field(default_factory=list)
    signal_mapping_gaps: list[str] = field(default_factory=list)
    assertion_quality_risks: list[str] = field(default_factory=list)
    toolchain_gaps: list[str] = field(default_factory=list)
    coverage_metrics: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ProjectConfig:
    top_module: str | None = None
    clock: str | None = None
    reset: str | None = None
    reset_active_low: bool | None = None
    use_external_tools: bool = True
    max_repair_rounds: int = 2
    memory_path: Path | None = None


@dataclass
class QEDSoftResult:
    success: bool
    output_dir: Path
    formalization: FormalizationBundle
    artifacts: list[Artifact]
    verification_results: list[VerificationResult]
    repair_actions: list[RepairAction]
    bottleneck_report: BottleneckReport

    def to_dict(self) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Path):
                return str(value)
            if hasattr(value, "__dataclass_fields__"):
                return {k: convert(v) for k, v in asdict(value).items()}
            if isinstance(value, list):
                return [convert(v) for v in value]
            if isinstance(value, dict):
                return {k: convert(v) for k, v in value.items()}
            return value

        return convert(self)
