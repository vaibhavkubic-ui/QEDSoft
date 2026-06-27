export interface Signal {
  name: string
  direction: 'input' | 'output' | 'inout' | 'internal' | 'unknown'
  width: number
  kind: string
  description: string
}

export interface Requirement {
  id: string
  text: string
  category: 'reset' | 'safety' | 'protocol' | 'temporal' | 'equivalence' | 'functional'
  signals: string[]
  latency_cycles: number | null
  confidence: number
  source: string
}

export interface VerificationSubgoal {
  id: string
  requirement_id: string
  statement: string
  artifact_type: 'sva' | 'lean' | 'both'
  signals: string[]
  assumptions: string[]
  priority: number
  confidence: number
}

export interface DesignModel {
  name: string
  top_module: string
  clock: string
  reset: string
  reset_active_low: boolean
  signals: Record<string, Signal>
  requirements: Requirement[]
  assumptions: string[]
}

export interface FormalizationBundle {
  model: DesignModel
  subgoals: VerificationSubgoal[]
  strategy: Record<string, unknown>
}

export interface Artifact {
  kind: 'sva' | 'bind' | 'lean' | 'lean_matlab' | 'lean_hdl' | 'lean_equivalence' | 'report' | 'metadata'
  path: string
  content: string
  metadata: Record<string, unknown>
}

export interface VerificationDiagnostic {
  tool: string
  severity: 'info' | 'warning' | 'error'
  message: string
  line: number | null
  hint: string | null
}

export interface VerificationResult {
  tool: string
  success: boolean
  diagnostics: VerificationDiagnostic[]
  metrics: Record<string, unknown>
  raw_output: string
}

export interface RepairAction {
  artifact_kind: string
  description: string
  applied: boolean
  diagnostics_resolved: number
}

export interface CoverageMetrics {
  requirements: number
  subgoals: number
  requirements_with_signal_mapping: number
  mapping_coverage: number
  low_confidence_requirements: number
}

export interface BottleneckReport {
  spec_ambiguity: string[]
  signal_mapping_gaps: string[]
  assertion_quality_risks: string[]
  toolchain_gaps: string[]
  coverage_metrics: CoverageMetrics
  recommendations: string[]
}

export interface QEDSoftResult {
  success: boolean
  output_dir: string
  formalization: FormalizationBundle
  artifacts: Artifact[]
  verification_results: VerificationResult[]
  repair_actions: RepairAction[]
  bottleneck_report: BottleneckReport
}

export interface VerifyRequest {
  spec_text: string
  rtl_text: string
  matlab_text: string
  top_module?: string
  clock?: string
  reset?: string
  reset_active_low?: boolean
  use_external_tools: boolean
  max_repair_rounds: number
  enable_source_to_lean: boolean
}
