'use client'
import { useState } from 'react'
import { AlertCircle } from 'lucide-react'
import InputForm from '@/components/InputForm'
import ResultsView from '@/components/ResultsView'
import type { QEDSoftResult } from '@/types/api'

export default function VerifyPage() {
  const [result, setResult] = useState<QEDSoftResult | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Run Verification</h1>
        <p className="text-slate-400">
          Paste your chip specification, RTL, and optional MATLAB model. QEDSoft generates
          SVA assertions, Lean4 contracts, and a coverage report automatically.
        </p>
      </div>

      <InputForm
        onResult={(r) => setResult(r as QEDSoftResult)}
        onError={setError}
        loading={loading}
        setLoading={setLoading}
      />

      {error && (
        <div className="mt-4 flex items-start gap-3 bg-red-950/40 border border-red-800/50 text-red-300 rounded-xl p-4 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {result && <ResultsView result={result} />}
    </div>
  )
}
