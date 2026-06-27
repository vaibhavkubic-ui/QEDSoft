import { AlertTriangle, CheckCircle2, Info, Lightbulb, Wrench } from 'lucide-react'
import type { QEDSoftResult } from '@/types/api'

function Section({ title, icon, items, emptyMsg, color }: {
  title: string
  icon: React.ReactNode
  items: string[]
  emptyMsg: string
  color: 'red' | 'amber' | 'blue' | 'emerald'
}) {
  const styles = {
    red:     { border: 'border-red-800/40',     bg: 'bg-red-950/30',     text: 'text-red-300',     icon: 'text-red-400' },
    amber:   { border: 'border-amber-800/40',   bg: 'bg-amber-950/30',   text: 'text-amber-300',   icon: 'text-amber-400' },
    blue:    { border: 'border-blue-800/40',    bg: 'bg-blue-950/30',    text: 'text-blue-300',    icon: 'text-blue-400' },
    emerald: { border: 'border-emerald-800/40', bg: 'bg-emerald-950/30', text: 'text-emerald-300', icon: 'text-emerald-400' },
  }[color]

  return (
    <div className={`border ${styles.border} ${styles.bg} rounded-xl p-5`}>
      <div className={`flex items-center gap-2 ${styles.icon} mb-3`}>
        {icon}
        <h3 className="font-medium text-sm">{title}</h3>
      </div>
      {items.length === 0 ? (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <CheckCircle2 className="w-4 h-4 text-emerald-500" /> {emptyMsg}
        </div>
      ) : (
        <ul className="space-y-2">
          {items.map((item, i) => (
            <li key={i} className={`text-sm ${styles.text} leading-relaxed flex gap-2`}>
              <span className="opacity-50 shrink-0">·</span>
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function BottleneckTab({ result }: { result: QEDSoftResult }) {
  const br = result.bottleneck_report

  return (
    <div className="space-y-4">
      <Section
        title="Spec Ambiguity"
        icon={<AlertTriangle className="w-4 h-4" />}
        items={br.spec_ambiguity}
        emptyMsg="No spec ambiguity detected"
        color="red"
      />
      <Section
        title="Signal Mapping Gaps"
        icon={<Info className="w-4 h-4" />}
        items={br.signal_mapping_gaps}
        emptyMsg="All requirements successfully mapped to signals"
        color="amber"
      />
      <Section
        title="Assertion Quality Risks"
        icon={<AlertTriangle className="w-4 h-4" />}
        items={br.assertion_quality_risks}
        emptyMsg="No assertion quality risks"
        color="amber"
      />
      <Section
        title="Toolchain Gaps"
        icon={<Wrench className="w-4 h-4" />}
        items={br.toolchain_gaps}
        emptyMsg="All required tools are available"
        color="blue"
      />
      <Section
        title="Recommendations"
        icon={<Lightbulb className="w-4 h-4" />}
        items={br.recommendations}
        emptyMsg="No recommendations"
        color="emerald"
      />

      {/* Repair actions */}
      {result.repair_actions.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
            <Wrench className="w-4 h-4 text-indigo-400" /> Auto-Repair Actions Applied
          </h3>
          <ul className="space-y-2">
            {result.repair_actions.map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span className="text-slate-300">{a.description}</span>
                <span className="text-xs text-slate-500 shrink-0">({a.diagnostics_resolved} fixed)</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
