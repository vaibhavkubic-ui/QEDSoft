import { CheckCircle2, XCircle, Activity, Cpu, GitBranch, Wrench } from 'lucide-react'
import type { QEDSoftResult } from '@/types/api'

export default function OverviewTab({ result }: { result: QEDSoftResult }) {
  const { model } = result.formalization
  const cm = result.bottleneck_report.coverage_metrics

  const stats = [
    { label: 'Requirements', value: cm.requirements, icon: <Activity className="w-4 h-4 text-indigo-400" /> },
    { label: 'Subgoals', value: cm.subgoals, icon: <GitBranch className="w-4 h-4 text-cyan-400" /> },
    { label: 'Signals Detected', value: Object.keys(model.signals).length, icon: <Cpu className="w-4 h-4 text-amber-400" /> },
    { label: 'Repair Actions', value: result.repair_actions.length, icon: <Wrench className="w-4 h-4 text-emerald-400" /> },
  ]

  return (
    <div className="space-y-6">
      {/* Success banner */}
      <div className={`flex items-center gap-3 p-4 rounded-xl border ${
        result.success
          ? 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300'
          : 'bg-red-950/40 border-red-800/50 text-red-300'
      }`}>
        {result.success
          ? <CheckCircle2 className="w-5 h-5 shrink-0" />
          : <XCircle className="w-5 h-5 shrink-0" />}
        <div>
          <div className="font-semibold">
            {result.success ? 'All verifiers passed — pipeline succeeded' : 'Pipeline completed with failures'}
          </div>
          <div className="text-xs opacity-70 mt-0.5">
            Top module: <code>{model.top_module}</code> · Clock: <code>{model.clock}</code> · Reset: <code>{model.reset}</code>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
            <div className="flex justify-center mb-2">{s.icon}</div>
            <div className="text-2xl font-bold text-white">{s.value}</div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Mapping coverage bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-slate-300 font-medium">Signal Mapping Coverage</span>
          <span className="text-sm font-bold text-white">{Math.round(cm.mapping_coverage * 100)}%</span>
        </div>
        <div className="h-2.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${cm.mapping_coverage === 1 ? 'bg-emerald-500' : cm.mapping_coverage >= 0.5 ? 'bg-amber-500' : 'bg-red-500'}`}
            style={{ width: `${cm.mapping_coverage * 100}%` }}
          />
        </div>
        <div className="text-xs text-slate-400 mt-1.5">
          {cm.requirements_with_signal_mapping} of {cm.requirements} requirements mapped to RTL signals
        </div>
      </div>

      {/* Verification results */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-slate-300 mb-3">Verifier Results</h3>
        <div className="space-y-2">
          {result.verification_results.map((vr, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
              <div className="flex items-center gap-2">
                {vr.success
                  ? <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  : <XCircle className="w-4 h-4 text-red-400" />}
                <span className="text-sm font-mono text-slate-300">{vr.tool}</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-500">
                {Object.entries(vr.metrics).slice(0, 3).map(([k, v]) => (
                  <span key={k}>{k}: <span className="text-slate-300">{String(v)}</span></span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Signals */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-slate-300 mb-3">Detected Signals</h3>
        <div className="flex flex-wrap gap-2">
          {Object.values(model.signals).map((s) => (
            <span key={s.name} className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${
              s.direction === 'input'
                ? 'bg-indigo-950/50 border-indigo-800/50 text-indigo-300'
                : s.direction === 'output'
                  ? 'bg-emerald-950/50 border-emerald-800/50 text-emerald-300'
                  : 'bg-slate-800 border-slate-700 text-slate-300'
            }`}>
              <span className="opacity-60">{s.direction}</span>
              <span className="font-mono">{s.name}</span>
              {s.width > 1 && <span className="opacity-50">[{s.width - 1}:0]</span>}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
