# QEDSoft

**Verifier-guided autoformalization for semiconductor RTL verification.**

QEDSoft takes a natural-language chip specification, optional RTL (SystemVerilog), and an optional MATLAB golden model, and automatically produces formal verification artifacts — SystemVerilog Assertions, Lean4 proof contracts, and a structured bottleneck report — ready for use with commercial EDA tools or Lean4.

Live API: **https://qedsoft-production.up.railway.app/docs**

---

## Table of Contents

- [What It Does](#what-it-does)
- [How It Works — Step by Step](#how-it-works--step-by-step)
- [Complete Architecture](#complete-architecture)
- [Three-Job Pipeline](#three-job-pipeline)
- [Data Models](#data-models)
- [Generated Artifacts](#generated-artifacts)
- [Industry Bottlenecks Targeted](#industry-bottlenecks-targeted)
- [Live API Usage](#live-api-usage)
- [Local Quickstart](#local-quickstart)
- [Deployment](#deployment)
- [Optional Toolchain](#optional-toolchain)
- [Project Layout](#project-layout)
- [Research Basis](#research-basis)
- [Next Engineering Steps](#next-engineering-steps)

---

## What It Does

Given this natural-language input:

```
Module fifo has clock clk and reset rst_n.
When reset is asserted, count must become zero.
The count must never exceed 16.
```

And this RTL:

```systemverilog
module fifo(input logic clk, input logic rst_n, output logic [4:0] count);
endmodule
```

QEDSoft automatically produces:

**SystemVerilog Assertions (`fifo_qedsoft_sva.sv`):**
```systemverilog
property qedsoft_req_001_reset;
  !rst_n |=> (count == '0);
endproperty
assert property (qedsoft_req_001_reset) else $error("QEDSoft violation: REQ-001");

property qedsoft_req_002_safety;
  disable iff (!rst_n) (!$isunknown(count));
endproperty
assert property (qedsoft_req_002_safety) else $error("QEDSoft violation: REQ-002");
```

**Lean4 Proof Contracts (`fifo_qedsoft_contract.lean`):**
```lean
theorem sg_001_reset_holds (t : Trace) : valid_inputs t -> sg_001_reset_property t
theorem sg_002_safety_holds (t : Trace) : valid_inputs t -> sg_002_safety_property t
```

Plus an SVA bind file, HDL-to-Lean4 structural model, equivalence obligation, Markdown report, and JSON result — all in one API call.

---

## How It Works — Step by Step

### Step 1: Input Ingestion

The pipeline accepts three inputs:

| Input | Required | Purpose |
|---|---|---|
| `spec_text` | Yes | Natural-language chip specification |
| `rtl_text` | No | SystemVerilog/HDL module source |
| `matlab_text` | No | MATLAB golden model function |

The `ProjectConfig` carries settings: clock name, reset polarity, max repair rounds, and whether to run external tools.

---

### Step 2: Signal Extraction (HardwareSpecParser)

The spec parser runs two extraction passes in parallel and merges the results:

**RTL port parsing** — regex over the SystemVerilog port list:
```
input logic clk         → Signal(name="clk",   direction="input",  width=1)
input logic rst_n       → Signal(name="rst_n",  direction="input",  width=1)
output logic [4:0] count → Signal(name="count", direction="output", width=5)
```

**Natural-language signal detection** — regex over the spec text looking for patterns like `"input N-bit signal_name"` or `"output register X"`.

Both sets are merged — RTL ports take priority. If a signal appears in both, the wider width wins.

---

### Step 3: Requirement Extraction (LLM-first, regex fallback)

Requirements are extracted using two strategies:

**Primary: LLM extraction** via `llm_client.py` (GWDG Chat-AI / Llama 3.1 70B):
- Sends the spec text and known signal names to the LLM
- Asks for a JSON array of requirements with category, signals, latency, and confidence
- Returns structured `Requirement` objects

**Fallback: Regex extraction** (used when LLM is unavailable or returns invalid JSON):
- Splits spec into sentences
- Filters for sentences containing keywords: `must`, `shall`, `never`, `when`, `within`, `after`, `reset`
- Classifies each sentence by category:

| Category | Keywords |
|---|---|
| `reset` | "reset" |
| `safety` | "never", "must not", "no" |
| `temporal` | "within N cycles", "after", "eventually" |
| `protocol` | "valid", "ready", "req", "ack", "grant" |
| `equivalence` | "equivalent", "same as", "matches" |
| `functional` | everything else |

Each requirement gets a confidence score (0.0–1.0) based on: signal mapping hits (+0.3), strong keywords like `must/shall` (+0.15), non-functional category (+0.15).

---

### Step 4: Subgoal Planning (QEDAIChipAutoformalizer)

Each requirement is converted into a `VerificationSubgoal` with a priority ranking:

| Category | Priority |
|---|---|
| reset | 10 (highest) |
| safety | 9 |
| protocol | 8 |
| temporal | 7 |
| equivalence | 6 |
| functional | 5 |

The autoformalizer produces a `FormalizationBundle` containing the `DesignModel` and ordered list of `VerificationSubgoal` objects.

---

### Step 5: Job 1 — Source to Lean4 (converters/)

If `enable_source_to_lean` is true:

**MATLAB → Lean4** (`MatlabToLeanConverter`):
- Parses MATLAB function signatures and scalar arithmetic
- Emits a Lean4 `structure` for state, `def step` for the transition function
- Supported subset: scalar arithmetic, if/else, basic assignments

**HDL → Lean4** (`HDLToLeanConverter`):
- Parses SystemVerilog module port declarations
- Emits `Input`, `State`, `Output` structures
- Generates a conservative `def step` skeleton (always-block semantics are a placeholder)

**Equivalence Obligation** (`EquivalenceSkeletonGenerator`):
- Generates a Lean4 entry point that imports both models
- Creates a `theorem qedai_verifier_entrypoint` as the proof target
- This is the hook for future QEDAI-driven proof search

---

### Step 6: Job 2 — Artifact Generation (generators/)

**SVA Generator** (`SVAGenerator`):
- For each subgoal, selects an SVA template based on category:

| Category | Template |
|---|---|
| reset | `!rst_n \|=> (signal == '0)` |
| safety | `disable iff (!rst_n) (invariant)` |
| temporal | `##[0:N] (condition)` |
| protocol | `req \|-> ##[1:4] ack` |
| functional | `disable iff (!rst_n) (known-value guard)` |

- Emits a full `module fifo_qedsoft_sva` with `default clocking` block
- Produces a companion `bind` file for zero-code RTL integration

**Lean4 Contract Generator** (`LeanContractGenerator`):
- Emits one `def sg_NNN_property` and `theorem sg_NNN_holds` per subgoal
- All proofs default to `trivial` — these are scaffolds for human/QEDAI refinement

---

### Step 7: Job 3 — Verification (verifiers/)

**SVASyntaxVerifier** (always runs):
- Counts `property`/`endproperty` blocks, assertions, and covers
- Checks for unbalanced parentheses
- Optionally runs `iverilog -g2012` for full syntax checking
- Optionally runs `verilator --lint-only` as a fallback linter

**LeanVerifier** (always runs in static mode):
- Counts theorems, definitions, and `sorry` uses
- Optionally runs `lean --check` on the generated `.lean` files

Each verifier returns a `VerificationResult` with `success`, `diagnostics[]`, and `metrics`.

---

### Step 8: SERA-VGP Repair Loop (repair/)

The repair engine runs up to `max_repair_rounds` times:

1. **Unbalanced parentheses** — counts `(` vs `)`, appends missing `)` tokens
2. **Unknown signal names** — fuzzy-matches diagnostic error symbols against known signals using `difflib` (cutoff 0.78), replaces mismatches in-place
3. **Manual-review guards** — replaces vacuous `1'b1` fallback properties with `!$isunknown(signal)` guards using the first output signal
4. **Missing endproperty** — detects unclosed `property` blocks, appends `endproperty`

After each repair round, the SVA verifier re-runs. The loop stops when no repairable issues remain or the round limit is reached.

---

### Step 9: Bottleneck Analysis & Reporting

**BottleneckAnalyzer** examines:
- `spec_ambiguity` — requirements with confidence < 0.5
- `signal_mapping_gaps` — requirements where no signals were mapped
- `assertion_quality_risks` — verification warnings from any tool
- `toolchain_gaps` — tools that were requested but not found
- `coverage_metrics` — `mapping_coverage = requirements_with_signal_mapping / total_requirements`

**MarkdownReportWriter** renders a human-readable `qedsoft_report.md`.

**FeedbackMemory** appends the result to a JSON memory file for future ranking improvement (the seed of the QEDAI VPH-AC feedback loop).

---

## Complete Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                             ENTRY POINTS                                    ║
╠══════════════════════╦═══════════════════════════╦═══════════════════════════╣
║   CLI (qedsoft)      ║   REST API (FastAPI)       ║   Docker Container        ║
║   cli.py             ║   api/server.py            ║   docker-compose.yml      ║
║                      ║   POST /verify             ║                           ║
║  qedsoft verify      ║   GET  /health             ║   uvicorn :8080           ║
║  qedsoft convert     ║                            ║                           ║
╚══════════════════════╩═══════════════════════════╩═══════════════════════════╝
                                    │
                                    ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ORCHESTRATOR  (orchestrator.py / QEDSoft)                ║
║                                                                              ║
║   Inputs: spec_text, rtl_text, matlab_text, ProjectConfig                   ║
║   Output: QEDSoftResult → artifacts + reports + verification_results        ║
╚══════════════════════════════════════════════════════════════════════════════╝
          │                        │                        │
          ▼                        ▼                        ▼
┌─────────────────┐   ┌────────────────────────┐   ┌────────────────────────┐
│   JOB 1         │   │   JOB 2                │   │   JOB 3                │
│  Source → Lean4 │   │  QEDAI Autoformalizer  │   │  Verify, Repair,       │
│  (converters/)  │   │  (formalizer/)         │   │  Report (verifiers/    │
│                 │   │                        │   │  repair/ reports/)     │
└────────┬────────┘   └───────────┬────────────┘   └───────────┬────────────┘
         │                        │                             │
         ▼                        ▼                             ▼

╔══════════════════════════════════════════════════════════════════════════════╗
║                         JOB 1 — SOURCE TO LEAN4                             ║
╠══════════════════╦═══════════════════╦══════════════════════════════════════╣
║ MatlabToLean     ║ HDLToLean         ║ EquivalenceSkeleton                  ║
║ Converter        ║ Converter         ║ Generator                            ║
║                  ║                   ║                                      ║
║ .m functions     ║ SystemVerilog     ║ Lean4 equivalence obligation         ║
║   ↓              ║ modules           ║ (MATLAB model ≡ HDL model)           ║
║ *_matlab_        ║   ↓               ║   ↓                                  ║
║  model.lean      ║ *_hdl_model.lean  ║ *_equivalence_obligation.lean        ║
╠══════════════════╩═══════════════════╩══════════════════════════════════════╣
║  converters/matlab_to_lean.py   converters/hdl_to_lean.py                  ║
║  converters/equivalence.py      converters/lean_expr.py                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                         JOB 2 — QEDAI AUTOFORMALIZER                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   HardwareSpecParser (formalizer/spec_parser.py)                            ║
║   ┌───────────────────────────────────────────────────────────┐             ║
║   │  LLM extraction (llm_client.py → GWDG Chat-AI / Llama)  │             ║
║   │     ↓ on failure                                         │             ║
║   │  Regex fallback (RTL port parsing + NL signal detection) │             ║
║   └───────────────────────────────────────────────────────────┘             ║
║          │                 │                  │                              ║
║          ▼                 ▼                  ▼                              ║
║     Signals            Requirements       Assumptions                        ║
║     (RTL ports +       (REQ-001…N,        (spec                              ║
║      NL mentions)       categories,        assumptions)                      ║
║                         confidence)                                          ║
║                                                                              ║
║   QEDAIChipAutoformalizer (formalizer/autoformalizer.py)                    ║
║   → builds FormalizationBundle { DesignModel, VerificationSubgoals }        ║
║                                                                              ║
║   Artifact Generators:                                                       ║
║   ┌─────────────────────────┬──────────────────────────┐                    ║
║   │ SVAGenerator            │ LeanContractGenerator    │                    ║
║   │ generators/sva_         │ generators/lean_         │                    ║
║   │ generator.py            │ generator.py             │                    ║
║   │                         │                          │                    ║
║   │ *_qedsoft_sva.sv        │ *_qedsoft_contract.lean  │                    ║
║   │ *_qedsoft_bind.sv       │                          │                    ║
║   └─────────────────────────┴──────────────────────────┘                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                    JOB 3 — VERIFY, REPAIR & DEPLOY                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │                        VERIFIERS                                    │    ║
║  │  SVASyntaxVerifier          LeanVerifier                            │    ║
║  │  verifiers/sva.py           verifiers/lean.py                       │    ║
║  │  Static checks (always)     Lean4 binary (optional)                 │    ║
║  │  iverilog lint (optional)   checks .lean contracts                  │    ║
║  │  verilator lint (optional)                                          │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                │ diagnostics                                 ║
║                                ▼                                             ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │                REPAIR LOOP (max N rounds)                           │    ║
║  │  StructuredRepairEngine  (repair/sera_vgp.py)                       │    ║
║  │  1. Balance parentheses                                             │    ║
║  │  2. Fuzzy-match unknown signal names (difflib, cutoff 0.78)         │    ║
║  │  3. Replace vacuous fallback guards with known-value checks         │    ║
║  │  4. Close unclosed property blocks                                  │    ║
║  │  → re-run verifier → repeat until clean or round limit hit          │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                │                                             ║
║                                ▼                                             ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │                   ANALYSIS & OUTPUT                                 │    ║
║  │  BottleneckAnalyzer (bottlenecks.py)                                │    ║
║  │  MarkdownReportWriter (reports.py) → qedsoft_report.md              │    ║
║  │  JSON serializer               → qedsoft_result.json               │    ║
║  │  FeedbackMemory (learning/memory.py) → memory JSON for ranking      │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                         SHARED DATA MODELS  (models.py)                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Signal → DesignModel → FormalizationBundle → QEDSoftResult                 ║
║  Requirement → VerificationSubgoal → Artifact → VerificationResult          ║
║  RepairAction → BottleneckReport → ProjectConfig                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                         OUTPUT ARTIFACTS                                     ║
╠═══════════════╦══════════════╦══════════════╦══════════════╦════════════════╣
║ *_sva.sv      ║ *_bind.sv    ║ *_contract   ║ *_matlab_    ║ *_equivalence_ ║
║               ║              ║   .lean      ║  model.lean  ║  obligation    ║
║ SystemVerilog ║ SVA bind     ║ Lean4        ║ MATLAB func  ║   .lean        ║
║ Assertions    ║ file         ║ contracts    ║ → Lean4      ║                ║
╠═══════════════╩══════════════╩══════════════╩══════════════╩════════════════╣
║             qedsoft_report.md                qedsoft_result.json            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Three-Job Pipeline

| Job | Module | Input | Output |
|---|---|---|---|
| **Job 1** Source → Lean4 | `converters/` | MATLAB `.m` + SystemVerilog | `*_matlab_model.lean`, `*_hdl_model.lean`, `*_equivalence_obligation.lean` |
| **Job 2** QEDAI Autoformalize | `formalizer/` + `generators/` | NL spec + RTL | `FormalizationBundle`, `*_sva.sv`, `*_bind.sv`, `*_contract.lean` |
| **Job 3** Verify + Repair | `verifiers/` + `repair/` + `reports/` | All artifacts | `qedsoft_report.md`, `qedsoft_result.json`, repaired SVA |

---

## Data Models

```
Signal
  name, direction, width, kind, description

Requirement
  id, text, category, signals[], latency_cycles, confidence, source

VerificationSubgoal
  id, requirement_id, statement, artifact_type, signals[], priority, confidence

DesignModel
  name, top_module, clock, reset, reset_active_low, signals{}, requirements[], assumptions[]

FormalizationBundle
  model: DesignModel
  subgoals: VerificationSubgoal[]
  strategy: dict

Artifact
  kind: sva | lean | lean_matlab | lean_hdl | lean_equivalence | bind | report | metadata
  path, content, metadata

VerificationResult
  tool, success, diagnostics[], metrics, raw_output

RepairAction
  artifact_kind, description, applied, diagnostics_resolved

BottleneckReport
  spec_ambiguity[], signal_mapping_gaps[], assertion_quality_risks[],
  toolchain_gaps[], coverage_metrics{}, recommendations[]

QEDSoftResult
  success, output_dir, formalization, artifacts[], verification_results[],
  repair_actions[], bottleneck_report
```

---

## Generated Artifacts

| Artifact | File | Used By |
|---|---|---|
| SVA module | `*_qedsoft_sva.sv` | JasperGold, Questa Formal, VC Formal, Xcelium, iverilog |
| SVA bind | `*_qedsoft_bind.sv` | EDA tools (zero-code RTL integration) |
| Lean4 contract | `*_qedsoft_contract.lean` | Lean4, future QEDAI proof search |
| MATLAB Lean4 model | `*_matlab_model.lean` | Lean4 equivalence checker |
| HDL Lean4 model | `*_hdl_model.lean` | Lean4 equivalence checker |
| Equivalence obligation | `*_equivalence_obligation.lean` | QEDAI verifier entrypoint |
| Markdown report | `qedsoft_report.md` | Human review, CI dashboards |
| JSON result | `qedsoft_result.json` | Feedback memory, downstream tooling |

---

## Industry Bottlenecks Targeted

| Bottleneck | How QEDSoft Addresses It |
|---|---|
| Specs are informal and ambiguous | LLM + regex extraction with confidence scoring |
| Signal names in specs don't match RTL | Fuzzy signal mapping with difflib |
| Assertion writing needs formal expertise | Automatic SVA generation from NL requirements |
| Formal tool diagnostics are not acted on | SERA-VGP automated repair loop |
| MATLAB and RTL verified in separate flows | Job 1 unifies both into Lean4 with equivalence obligation |
| Coverage hard to connect to requirements | `mapping_coverage` metric in bottleneck report |
| Proof attempts are thrown away | FeedbackMemory seeds future ranking |

---

## Live API Usage

**Base URL:** `https://qedsoft-production.up.railway.app`

### Health Check
```
GET /health
→ {"status": "ok"}
```

### Verify Endpoint
```
POST /verify
Content-Type: application/json
```

**Minimal request:**
```json
{
  "spec_text": "Module fifo has clock clk and reset rst_n. When reset is asserted, count must become zero.",
  "rtl_text": "module fifo(input logic clk, input logic rst_n, output logic [4:0] count); endmodule",
  "use_external_tools": false
}
```

**Full request with MATLAB:**
```json
{
  "spec_text": "Module fifo has clock clk and reset rst_n. When reset is asserted, count must become zero. The count must never exceed 16.",
  "rtl_text": "module fifo(input logic clk, input logic rst_n, output logic [4:0] count); endmodule",
  "matlab_text": "function [count_next] = fifo_step(wr_en, full, count)\nif wr_en && ~full\n  count_next = count + 1;\nelse\n  count_next = count;\nend\nend",
  "top_module": "fifo",
  "clock": "clk",
  "reset": "rst_n",
  "reset_active_low": true,
  "use_external_tools": false,
  "max_repair_rounds": 2,
  "enable_source_to_lean": true
}
```

**Response fields:**

| Field | Description |
|---|---|
| `success` | `true` if all verifiers passed |
| `formalization.model` | Extracted DesignModel with signals and requirements |
| `formalization.subgoals` | Prioritised verification subgoals |
| `artifacts` | All generated files with their content |
| `verification_results` | Per-tool pass/fail with metrics |
| `repair_actions` | Any automated SVA repairs applied |
| `bottleneck_report` | Coverage metrics and recommendations |

**Interactive Swagger UI:** `https://qedsoft-production.up.railway.app/docs`

---

## Local Quickstart

```powershell
python -m pip install -e ".[api]"
```

Run full verification:
```powershell
qedsoft verify --spec examples/fifo/spec.md --rtl examples/fifo/fifo.sv --out runs/fifo
```

With MATLAB model:
```powershell
qedsoft verify --spec examples/fifo/spec.md --rtl examples/fifo/fifo.sv --matlab examples/matlab/fifo_step.m --out runs/fifo_full
```

Static checks only (no external tools needed):
```powershell
qedsoft verify --spec examples/fifo/spec.md --rtl examples/fifo/fifo.sv --out runs/fifo --no-external-tools
```

Run Job 1 only (convert to Lean4):
```powershell
qedsoft convert --matlab examples/matlab/fifo_step.m --out runs/convert
qedsoft convert --hdl examples/fifo/fifo.sv --out runs/convert
```

---

## Deployment

### Railway (live)

Push to GitHub — Railway auto-deploys on every commit.

Required environment variables:
```
CHAT_AI_API_KEY    your GWDG or compatible OpenAI-format API key
CHAT_AI_ENDPOINT   https://chat-ai.academiccloud.de/v1
CHAT_AI_MODEL      meta-llama/Meta-Llama-3.1-70B-Instruct
```

### Docker

```powershell
docker compose up --build
```

Health check: `http://localhost:8080/health`

### Local API server

```powershell
pip install -e ".[api]"
uvicorn qedsoft.api.server:app --host 0.0.0.0 --port 8080
```

---

## Optional Toolchain

QEDSoft automatically detects and uses these when present:

| Tool | Purpose |
|---|---|
| `lean` | Lean4 contract checking |
| `iverilog -g2012` | SystemVerilog syntax and lint |
| `verilator --lint-only` | Fallback SVA linter |

Commercial tools (JasperGold, Questa Formal, VC Formal, Xcelium) can be integrated by adding a verifier class under `src/qedsoft/verifiers/`.

Set `use_external_tools: false` on Railway (no EDA tools installed in the container).

---

## Project Layout

```
src/qedsoft/
  api/              FastAPI server (POST /verify, GET /health)
  converters/       MATLAB and HDL to Lean4 source-model conversion
  formalizer/       NL spec parsing and QEDAI-style subgoal planning
  generators/       SVA and Lean4 artifact generation
  verifiers/        Static and optional external tool checks
  repair/           SERA-VGP-inspired structured repair engine
  learning/         Feedback memory seed (VPH-AC loop)
  orchestrator.py   End-to-end QEDSoft pipeline driver
  models.py         All shared dataclasses
  cli.py            CLI entry point (qedsoft verify / convert)
  reports.py        Markdown report renderer
  bottlenecks.py    Bottleneck analysis
  llm_client.py     GWDG Chat-AI / OpenAI-compatible LLM client
```

---

## Research Basis

QEDSoft's direction is influenced by:

- **CktFormalizer** — natural-language circuit generation through a Lean4-embedded HDL
- **Simulink-to-Why3** — theorem-proving-based control-system verification
- **FASiM** — Simulink-to-HOL Light translation for formal model analysis
- **Lean-SMT** — Lean4 automation for future bit-vector and arithmetic proof closure
- **QEDAI** — original autoformalization framework adapted from mathematical theorem proving to chip verification

---

## Next Engineering Steps

1. Add a signal dictionary file for alias mapping (`request → req`)
2. Expand MATLAB support to fixed-point, arrays, loops, and Simulink block graphs
3. Expand HDL support from structural skeletons to full always-block transition semantics
4. Replace Lean placeholder predicates with a full HDL/circuit semantics layer
5. Add formal-tool adapters for JasperGold, Questa Formal, VC Formal
6. Add seeded-bug mutation tests to measure bug-detection rate
7. Train or fine-tune the ranking policy using `qedsoft_result.json` memory
