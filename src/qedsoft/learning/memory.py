from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qedsoft.models import QEDSoftResult


class FeedbackMemory:
    """Small JSON memory for verifier outcomes.

    This is the deployable seed of QEDAI's Lean-feedback-aware memory and
    VPH-AC loop. A production version can replace this with a vector DB or RL
    replay buffer without changing the orchestrator contract.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_result(self, result: QEDSoftResult) -> None:
        data = self._load()
        data.setdefault("runs", []).append(
            {
                "success": result.success,
                "top_module": result.formalization.model.top_module,
                "requirements": len(result.formalization.model.requirements),
                "subgoals": len(result.formalization.subgoals),
                "artifacts": [str(artifact.path) for artifact in result.artifacts],
                "verification": [
                    {
                        "tool": item.tool,
                        "success": item.success,
                        "metrics": item.metrics,
                        "diagnostics": [diag.message for diag in item.diagnostics],
                    }
                    for item in result.verification_results
                ],
            }
        )
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"runs": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"runs": []}
