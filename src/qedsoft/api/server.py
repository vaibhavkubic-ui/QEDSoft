from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError as exc:
    raise RuntimeError(
        "FastAPI dependencies are not installed. Install with `pip install -e .[api]`."
    ) from exc

from qedsoft.models import ProjectConfig
from qedsoft.orchestrator import QEDSoft


class VerifyRequest(BaseModel):
    spec_text: str
    rtl_text: str = ""
    matlab_text: str = ""
    top_module: str | None = None
    clock: str | None = None
    reset: str | None = None
    reset_active_low: bool | None = None
    use_external_tools: bool = False
    max_repair_rounds: int = 2
    enable_source_to_lean: bool = True


app = FastAPI(
    title="QEDSoft",
    description="Verifier-guided autoformalization for semiconductor RTL verification.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/verify")
def verify(request: VerifyRequest) -> dict[str, Any]:
    config = ProjectConfig(
        top_module=request.top_module,
        clock=request.clock,
        reset=request.reset,
        reset_active_low=request.reset_active_low,
        use_external_tools=request.use_external_tools,
        max_repair_rounds=request.max_repair_rounds,
        enable_source_to_lean=request.enable_source_to_lean,
    )
    with tempfile.TemporaryDirectory(prefix="qedsoft_api_") as tmp:
        result = QEDSoft(config).run(
            spec_text=request.spec_text,
            rtl_text=request.rtl_text,
            matlab_text=request.matlab_text,
            output_dir=Path(tmp) / "run",
            design_name=request.top_module or "api_design",
        )
        return result.to_dict()
