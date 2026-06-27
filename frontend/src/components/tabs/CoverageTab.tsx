'use client'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'
import type { QEDSoftResult } from '@/types/api'

const CATEGORY_COLORS: Record<string, string> = {
  reset:       '#60a5fa',
  safety:      '#f87171',
  protocol:    '#c084fc',
  temporal:    '#fbbf24',
  equivalence: '#22d3ee',
  functional:  '#94a3b8',
}

export default function CoverageTab({ result }: { result: QEDSoftResult }) {
  const cm = result.bottleneck_report.coverage_metrics
  const reqs = result.formalization.model.requirements

  const pct = Math.round(cm.mapping_coverage * 100)

  const donutData = [
    { name: 'Mapped', value: cm.requirements_with_signal_mapping },
    { name: 'Unmapped', value: cm.requirements - cm.requirements_with_signal_mapping },
  ]

  const categoryData = Object.entries(
    reqs.reduce<Record<string, number>>((acc, r) => {
      acc[r.category] = (acc[r.category] || 0) + 1
      return acc
    }, {})
  ).map(([name, count]) => ({ name, count }))

  const confidenceData = reqs.map((r) => ({
    name: r.id,
    confidence: Math.round(r.confidence * 100),
    category: r.category,
  }))

  return (
    <div className="space-y-6">
      {/* Top stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Requirements', value: cm.requirements },
          { label: 'Signal Mapped', value: cm.requirements_with_signal_mapping },
          { label: 'Mapping Coverage', value: `${pct}%` },
          { label: 'Low Confidence', value: cm.low_confidence_requirements },
        ].map((s) => (
          <div key={s.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-white">{s.value}</div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Donut: mapping coverage */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Signal Mapping Coverage</h3>
          {cm.requirements === 0 ? (
            <div className="text-center text-slate-500 py-8 text-sm">No requirements</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={donutData}
                  cx="50%" cy="50%"
                  innerRadius={60} outerRadius={90}
                  dataKey="value"
                  startAngle={90} endAngle={-270}
                >
                  <Cell fill="#6366f1" />
                  <Cell fill="#1e293b" />
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" fill="#fff" fontSize={28} fontWeight="bold">
                  {pct}%
                </text>
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Bar: requirements by category */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Requirements by Category</h3>
          {categoryData.length === 0 ? (
            <div className="text-center text-slate-500 py-8 text-sm">No categories</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={categoryData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                  cursor={{ fill: '#1e293b' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {categoryData.map((entry) => (
                    <Cell key={entry.name} fill={CATEGORY_COLORS[entry.name] || '#6366f1'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Confidence per requirement */}
      {confidenceData.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Confidence per Requirement</h3>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={confidenceData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} unit="%" />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                cursor={{ fill: '#1e293b' }}
                formatter={(v: number) => [`${v}%`, 'Confidence']}
              />
              <Bar dataKey="confidence" radius={[4, 4, 0, 0]}>
                {confidenceData.map((entry, i) => (
                  <Cell key={i} fill={entry.confidence >= 80 ? '#10b981' : entry.confidence >= 50 ? '#f59e0b' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
