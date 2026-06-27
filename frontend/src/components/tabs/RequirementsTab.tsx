import type { QEDSoftResult, Requirement } from '@/types/api'

const CATEGORY_STYLES: Record<string, string> = {
  reset:       'bg-blue-950/60 border-blue-800/50 text-blue-300',
  safety:      'bg-red-950/60 border-red-800/50 text-red-300',
  protocol:    'bg-purple-950/60 border-purple-800/50 text-purple-300',
  temporal:    'bg-amber-950/60 border-amber-800/50 text-amber-300',
  equivalence: 'bg-cyan-950/60 border-cyan-800/50 text-cyan-300',
  functional:  'bg-slate-800 border-slate-700 text-slate-300',
}

const PRIORITY_LABEL: Record<number, string> = {
  10: 'P1',  9: 'P2',  8: 'P3',  7: 'P4',  6: 'P5',  5: 'P6',
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.8 ? 'bg-emerald-500' : value >= 0.5 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-8 text-right">{pct}%</span>
    </div>
  )
}

function ReqCard({ req, subgoal }: { req: Requirement; subgoal?: { priority: number } }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded">{req.id}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full border ${CATEGORY_STYLES[req.category] || CATEGORY_STYLES.functional}`}>
            {req.category}
          </span>
          {subgoal && (
            <span className="text-xs bg-indigo-950/60 border border-indigo-800/50 text-indigo-300 px-2 py-0.5 rounded-full">
              {PRIORITY_LABEL[subgoal.priority] || `P${subgoal.priority}`}
            </span>
          )}
        </div>
        <span className="text-xs text-slate-500 shrink-0">{req.source}</span>
      </div>

      <p className="text-slate-200 text-sm leading-relaxed">{req.text}</p>

      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-500">Confidence</span>
        <div className="flex-1"><ConfidenceBar value={req.confidence} /></div>
      </div>

      {req.signals.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {req.signals.map((s) => (
            <span key={s} className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded">{s}</span>
          ))}
        </div>
      )}

      {req.latency_cycles !== null && (
        <div className="text-xs text-amber-400">⏱ Latency: {req.latency_cycles} cycle{req.latency_cycles !== 1 ? 's' : ''}</div>
      )}
    </div>
  )
}

export default function RequirementsTab({ result }: { result: QEDSoftResult }) {
  const { model, subgoals } = result.formalization
  const subgoalMap = Object.fromEntries(subgoals.map((sg) => [sg.requirement_id, sg]))

  if (model.requirements.length === 0) {
    return (
      <div className="text-center py-16 text-slate-500">
        No requirements were extracted. Try providing a more detailed spec_text.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-300">{model.requirements.length} Requirements Extracted</h3>
        <div className="flex gap-2 flex-wrap">
          {Object.entries(
            model.requirements.reduce<Record<string, number>>((acc, r) => {
              acc[r.category] = (acc[r.category] || 0) + 1
              return acc
            }, {})
          ).map(([cat, count]) => (
            <span key={cat} className={`text-xs px-2 py-0.5 rounded-full border ${CATEGORY_STYLES[cat] || CATEGORY_STYLES.functional}`}>
              {cat}: {count}
            </span>
          ))}
        </div>
      </div>

      {model.requirements.map((req) => (
        <ReqCard key={req.id} req={req} subgoal={subgoalMap[req.id]} />
      ))}
    </div>
  )
}
