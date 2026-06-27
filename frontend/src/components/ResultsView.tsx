'use client'
import { useState } from 'react'
import type { QEDSoftResult } from '@/types/api'
import OverviewTab from './tabs/OverviewTab'
import RequirementsTab from './tabs/RequirementsTab'
import ArtifactsTab from './tabs/ArtifactsTab'
import CoverageTab from './tabs/CoverageTab'
import BottleneckTab from './tabs/BottleneckTab'

const TABS = [
  { id: 'overview',      label: 'Overview' },
  { id: 'requirements',  label: 'Requirements' },
  { id: 'artifacts',     label: 'Artifacts' },
  { id: 'coverage',      label: 'Coverage' },
  { id: 'bottleneck',    label: 'Bottleneck Report' },
] as const

type TabId = typeof TABS[number]['id']

export default function ResultsView({ result }: { result: QEDSoftResult }) {
  const [tab, setTab] = useState<TabId>('overview')

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Results</h2>
        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
          result.success ? 'bg-emerald-900/50 text-emerald-300' : 'bg-red-900/50 text-red-300'
        }`}>
          {result.success ? '✓ Success' : '✗ Failed'}
        </span>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-800 mb-6 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
              tab === t.id
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {t.label}
            {t.id === 'requirements' && (
              <span className="ml-1.5 text-xs bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded-full">
                {result.formalization.model.requirements.length}
              </span>
            )}
            {t.id === 'artifacts' && (
              <span className="ml-1.5 text-xs bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded-full">
                {result.artifacts.filter(a => !['report','metadata'].includes(a.kind)).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'overview'     && <OverviewTab     result={result} />}
      {tab === 'requirements' && <RequirementsTab result={result} />}
      {tab === 'artifacts'    && <ArtifactsTab    result={result} />}
      {tab === 'coverage'     && <CoverageTab      result={result} />}
      {tab === 'bottleneck'   && <BottleneckTab    result={result} />}
    </div>
  )
}
