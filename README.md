
# QEDSoft

QEDSoft is a verifier-guided autoformalization framework for semiconductor RTL
verification. It adapts the original QEDAI architecture from mathematical theorem
proving to chip verification and now has a three-job product architecture:

1. **Job 1: Source to Lean4**
   - Converts supported MATLAB function subsets into Lean4 executable models.
   - Converts supported HDL/SystemVerilog structure into Lean4 transition skeletons.
   - Generates a Lean4 equivalence-obligation entry point for QEDAI.
2. **Job 2: QEDAI Verifier**
   - Converts natural-language chip specs into formal verification subgoals.
   - Emits Lean4 proof/contract obligations.
   - Checks generated Lean with Lean4 when available.
3. **Job 3: Artifact, Repair, and Deployment**
   - Generates SystemVerilog Assertions and bind files.
   - Runs static and optional external verification.
   - Applies SERA-VGP-inspired repair.
   - Produces Markdown/JSON reports and deploys via CLI/API/Docker.

## Architecture

```text
Natural-language spec + optional RTL + optional MATLAB
        |
        v
Job 1 Source-to-Lean
        |
        +-- MATLAB to Lean4 model
        +-- HDL to Lean4 model
        +-- Lean4 equivalence obligation
        |
        v
QEDAIChipAutoformalizer / Verifier
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
- MATLAB/Simulink golden models and RTL are often verified in separate flows.
- Verification coverage is hard to connect back to natural-language requirements.
- Proof and assertion attempts are often thrown away instead of becoming memory
  for future runs.

The current implementation is an industrial-product scaffold with a safe supported
subset. It is useful for prototypes, research, internal demos, and as a clean base
for integrating proprietary EDA tools. Full signoff-grade replacement requires
expanding the converters to complete MATLAB/Simulink and SystemVerilog semantics,
plus certified equivalence proofs.

## Local Quickstart

From this directory:

```powershell
python -m pip install -e .
qedsoft verify --spec examples/fifo/spec.md --rtl examples/fifo/fifo.sv --out runs/fifo
```

With MATLAB source-to-Lean enabled:

```powershell
qedsoft verify --spec examples/fifo/spec.md --rtl examples/fifo/fifo.sv --matlab examples/matlab/fifo_step.m --out runs/fifo_full
```

If you do not have Lean or HDL tools installed, run static checks only:

```powershell
qedsoft verify --spec examples/fifo/spec.md --rtl examples/fifo/fifo.sv --out runs/fifo --no-external-tools
```

Run Job 1 only:

```powershell
qedsoft convert --matlab examples/matlab/fifo_step.m --out runs/convert
qedsoft convert --hdl examples/fifo/fifo.sv --out runs/convert
```

Outputs:

- `runs/fifo/fifo_qedsoft_sva.sv`
- `runs/fifo/fifo_qedsoft_bind.sv`
- `runs/fifo/fifo_qedsoft_contract.lean`
- `runs/fifo_full/fifo_step_matlab_model.lean`
- `runs/fifo_full/fifo_hdl_model.lean`
- `runs/fifo_full/fifo_equivalence_obligation.lean`
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
  "matlab_text": "function [count_next] = fifo_step(wr_en, full, count)\nif wr_en && ~full\ncount_next = count + 1;\nelse\ncount_next = count;\nend\nend",
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

## Research Basis

QEDSoft's direction is influenced by:

- CktFormalizer: natural-language circuit generation through a Lean4-embedded HDL.
- Simulink-to-Why3 work for theorem-proving-based control-system verification.
- FASiM-style Simulink-to-HOL Light translation for formal model analysis.
- Lean-SMT and related Lean4 automation for future bit-vector/arithmetic proof closure.

The product gap QEDSoft targets is a unified MATLAB/HDL-to-Lean4 equivalence
pipeline with QEDAI-driven proof search and verifier-guided repair.

## Project Layout

```text
src/qedsoft/
  converters/       MATLAB/HDL to Lean4 source-model conversion
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
2. Expand MATLAB support from scalar functions to fixed-point, arrays, loops, and Simulink block graphs.
3. Expand HDL support from structural skeletons to full always-block transition semantics.
4. Replace Lean placeholder predicates with a full Lean HDL/circuit semantics layer.
5. Add formal-tool adapters for your lab or company flow.
6. Add seeded-bug mutation tests to measure bug-detection rate.
7. Train or fine-tune the ranking policy using `qedsoft_result.json` memory.

# QEDSoft

