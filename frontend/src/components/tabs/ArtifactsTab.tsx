'use client'
import { useState } from 'react'
import CodeBlock from '@/components/CodeBlock'
import type { QEDSoftResult, Artifact } from '@/types/api'

const KIND_LABELS: Record<string, string> = {
  sva:              'SVA Module',
  bind:             'SVA Bind',
  lean:             'Lean4 Contract',
  lean_matlab:      'MATLAB → Lean4',
  lean_hdl:         'HDL → Lean4',
  lean_equivalence: 'Equivalence Obligation',
  report:           'Markdown Report',
  metadata:         'JSON Metadata',
}

const KIND_LANG: Record<string, string> = {
  sva:              'verilog',
  bind:             'verilog',
  lean:             'haskell',
  lean_matlab:      'haskell',
  lean_hdl:         'haskell',
  lean_equivalence: 'haskell',
  report:           'markdown',
  metadata:         'json',
}

const SHOW_KINDS = ['sva', 'bind', 'lean', 'lean_matlab', 'lean_hdl', 'lean_equivalence']

export default function ArtifactsTab({ result }: { result: QEDSoftResult }) {
  const artifacts = result.artifacts.filter((a) => SHOW_KINDS.includes(a.kind))
  const [active, setActive] = useState<string>(artifacts[0]?.kind || '')

  const current = artifacts.find((a) => a.kind === active)

  return (
    <div className="space-y-4">
      {/* Kind selector */}
      <div className="flex flex-wrap gap-2">
        {artifacts.map((a) => (
          <button
            key={a.kind}
            onClick={() => setActive(a.kind)}
            className={`text-sm px-3 py-1.5 rounded-lg border transition-colors ${
              active === a.kind
                ? 'bg-indigo-600 border-indigo-500 text-white'
                : 'bg-slate-900 border-slate-700 text-slate-300 hover:border-slate-500'
            }`}
          >
            {KIND_LABELS[a.kind] || a.kind}
          </button>
        ))}
      </div>

      {current && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 font-mono">{current.path.split('/').pop()}</span>
            <span className="text-xs text-slate-500">{current.content.split('\n').length} lines</span>
          </div>
          <CodeBlock
            code={current.content}
            language={KIND_LANG[current.kind] || 'text'}
          />
          {current.kind === 'lean_equivalence' && (
            <div className="text-xs text-amber-400/80 bg-amber-950/30 border border-amber-800/30 rounded-lg px-3 py-2">
              ⚠ This is a proof scaffold. Replace <code>trivial</code> with real proof terms once the MATLAB + HDL models are fully implemented.
            </div>
          )}
        </div>
      )}

      {artifacts.length === 0 && (
        <div className="text-center py-16 text-slate-500">No artifacts generated.</div>
      )}
    </div>
  )
}
