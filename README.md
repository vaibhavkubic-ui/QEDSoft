
# QEDSoft

QEDSoft is a verifier-guided autoformalization framework for semiconductor RTL
verification. It adapts the original QEDAI architecture from mathematical theorem
proving to chip verification:

- Natural-language chip specs become formal verification subgoals.
- Subgoals become SystemVerilog Assertions and Lean4 contract skeletons.
- Verifier feedback drives structured repair.
- Run memory records outcomes for future ranking and learning.

## Architecture

```text
Natural-language spec + optional RTL
        |
        v
QEDAIChipAutoformalizer
        |
        +-- signal extraction
        +-- requirement classification
        +-- requirement-to-subgoal planning
        |
        v
Artifact generators
        |
        +-- SystemVerilog Assertions
        +-- bind file
        +-- Lean4 contract
        |
        v
Verifiers
        |
        +-- static SVA checks
        +-- optional iverilog / Verilator
        +-- optional Lean4
        |
        v
SERA-VGP repair + bottleneck report
```

## What Industry Bottlenecks It Targets

QEDSoft is designed around common verification pain points:

- Specs are informal and ambiguous.
- Signal names in specs do not always match RTL names.
- Assertion writing requires scarce formal-verification expertise.
- Formal tools return useful diagnostics, but teams rarely turn them into an
  automated repair loop.
- Verification coverage is hard to connect back to natural-language requirements.
- Proof and assertion attempts are often thrown away instead of becoming memory
  for future runs.

The current implementation is an MVP. It is useful for prototypes, research,
internal demos, and as a clean base for integrating proprietary EDA tools.

## Local Quickstart

From this directory:

```powershell
python -m pip install -e .
qedsoft verify --spec examples/fifo/spec.md --rtl examples/fifo/fifo.sv --out runs/fifo
```

If you do not have Lean or HDL tools installed, run static checks only:

```powershell
qedsoft verify --spec examples/fifo/spec.md --rtl examples/fifo/fifo.sv --out runs/fifo --no-external-tools
```

Outputs:

- `runs/fifo/fifo_qedsoft_sva.sv`
- `runs/fifo/fifo_qedsoft_bind.sv`
- `runs/fifo/fifo_qedsoft_contract.lean`
- `runs/fifo/qedsoft_report.md`
- `runs/fifo/qedsoft_result.json`

## API Deployment

```powershell
python -m pip install -e ".[api]"
uvicorn qedsoft.api.server:app --host 0.0.0.0 --port 8080
```

Docker:

```powershell
docker compose up --build
```

Health check:

```powershell
curl http://localhost:8080/health
```

Verification request:

```json
{
  "spec_text": "Module fifo has clock clk and reset rst_n. When reset is asserted, count must become zero.",
  "rtl_text": "module fifo(input logic clk, input logic rst_n, output logic [4:0] count); endmodule",
  "top_module": "fifo",
  "use_external_tools": false
}
```

POST it to `/verify`.

## Optional Toolchain

QEDSoft automatically detects and uses these tools when present:

- `lean` for Lean4 contract checking
- `iverilog` for SystemVerilog syntax/lint checks
- `verilator` as a fallback SystemVerilog linter

Commercial tools such as JasperGold, Questa Formal, VC Formal, or Xcelium can
be integrated by adding another verifier class under `src/qedsoft/verifiers`.

## Project Layout

```text
src/qedsoft/
  formalizer/       spec extraction and QEDAI-style subgoal planning
  generators/       SVA and Lean artifact generation
  verifiers/        static and optional external tool checks
  repair/           SERA-VGP-inspired structured repair
  learning/         feedback memory seed
  api/              FastAPI deployment surface
  orchestrator.py   end-to-end QEDSoft pipeline
```

## Next Engineering Steps

1. Add a signal dictionary file for alias mapping, for example `request -> req`.
2. Replace Lean placeholder predicates with your Lean HDL semantics.
3. Add formal-tool adapters for your lab or company flow.
4. Add seeded-bug mutation tests to measure bug-detection rate.
5. Train or fine-tune the ranking policy using `qedsoft_result.json` memory.

# QEDSoft

