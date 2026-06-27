'use client'
import { useState } from 'react'
import { ChevronDown, ChevronUp, Loader2, Play } from 'lucide-react'
import type { VerifyRequest } from '@/types/api'

const EXAMPLE: VerifyRequest = {
  spec_text: 'Module fifo has clock clk and reset rst_n. When reset is asserted, count must become zero. The count must never exceed 16.',
  rtl_text: 'module fifo(input logic clk, input logic rst_n, output logic [4:0] count); endmodule',
  matlab_text: '',
  top_module: 'fifo',
  clock: 'clk',
  reset: 'rst_n',
  reset_active_low: true,
  use_external_tools: false,
  max_repair_rounds: 2,
  enable_source_to_lean: true,
}

interface Props {
  onResult: (result: unknown) => void
  onError: (msg: string) => void
  loading: boolean
  setLoading: (v: boolean) => void
}

export default function InputForm({ onResult, onError, loading, setLoading }: Props) {
  const [form, setForm] = useState<VerifyRequest>(EXAMPLE)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [activeTab, setActiveTab] = useState<'spec' | 'rtl' | 'matlab'>('spec')

  const set = (key: keyof VerifyRequest, value: unknown) =>
    setForm((f) => ({ ...f, [key]: value }))

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.spec_text.trim()) { onError('spec_text is required.'); return }
    setLoading(true)
    onError('')
    try {
      const { verify } = await import('@/lib/api')
      const result = await verify(form)
      onResult(result)
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const tabBtn = (id: typeof activeTab, label: string) => (
    <button
      type="button"
      onClick={() => setActiveTab(id)}
      className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
        activeTab === id
          ? 'border-indigo-500 text-indigo-400'
          : 'border-transparent text-slate-400 hover:text-slate-200'
      }`}
    >
      {label}
    </button>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Input tabs */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="flex border-b border-slate-800 px-4 pt-2 gap-1">
          {tabBtn('spec', 'Spec *')}
          {tabBtn('rtl', 'RTL / SystemVerilog')}
          {tabBtn('matlab', 'MATLAB (optional)')}
        </div>

        <div className="p-4">
          {activeTab === 'spec' && (
            <div>
              <label className="text-xs text-slate-400 mb-2 block">
                Natural-language chip specification
              </label>
              <textarea
                rows={7}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm text-slate-100 font-mono resize-none focus:outline-none focus:border-indigo-500 placeholder-slate-600"
                placeholder="Module fifo has clock clk and reset rst_n. When reset is asserted, count must become zero..."
                value={form.spec_text}
                onChange={(e) => set('spec_text', e.target.value)}
              />
            </div>
          )}
          {activeTab === 'rtl' && (
            <div>
              <label className="text-xs text-slate-400 mb-2 block">
                SystemVerilog module source (optional — improves signal extraction)
              </label>
              <textarea
                rows={7}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm text-slate-100 font-mono resize-none focus:outline-none focus:border-indigo-500 placeholder-slate-600"
                placeholder="module fifo(input logic clk, input logic rst_n, output logic [4:0] count); endmodule"
                value={form.rtl_text}
                onChange={(e) => set('rtl_text', e.target.value)}
              />
            </div>
          )}
          {activeTab === 'matlab' && (
            <div>
              <label className="text-xs text-slate-400 mb-2 block">
                MATLAB golden model (optional — enables Job 1 equivalence proof)
              </label>
              <textarea
                rows={7}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm text-slate-100 font-mono resize-none focus:outline-none focus:border-indigo-500 placeholder-slate-600"
                placeholder={"function [count_next] = fifo_step(wr_en, full, count)\nif wr_en && ~full\n  count_next = count + 1;\nelse\n  count_next = count;\nend\nend"}
                value={form.matlab_text}
                onChange={(e) => set('matlab_text', e.target.value)}
              />
            </div>
          )}
        </div>
      </div>

      {/* Advanced settings */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between px-4 py-3 text-sm text-slate-300 hover:text-white transition-colors"
        >
          <span>Advanced Settings</span>
          {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {showAdvanced && (
          <div className="border-t border-slate-800 p-4 grid grid-cols-2 gap-4">
            {[
              { key: 'top_module', label: 'Top Module', placeholder: 'fifo' },
              { key: 'clock', label: 'Clock Signal', placeholder: 'clk' },
              { key: 'reset', label: 'Reset Signal', placeholder: 'rst_n' },
            ].map(({ key, label, placeholder }) => (
              <div key={key}>
                <label className="text-xs text-slate-400 mb-1 block">{label}</label>
                <input
                  type="text"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                  placeholder={placeholder}
                  value={(form[key as keyof VerifyRequest] as string) || ''}
                  onChange={(e) => set(key as keyof VerifyRequest, e.target.value || undefined)}
                />
              </div>
            ))}
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Max Repair Rounds</label>
              <input
                type="number"
                min={0} max={5}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                value={form.max_repair_rounds}
                onChange={(e) => set('max_repair_rounds', Number(e.target.value))}
              />
            </div>
            <div className="col-span-2 flex flex-wrap gap-4">
              {[
                { key: 'reset_active_low', label: 'Reset Active Low' },
                { key: 'enable_source_to_lean', label: 'Enable Source to Lean4 (Job 1)' },
                { key: 'use_external_tools', label: 'Use External Tools (lean / iverilog)' },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    className="accent-indigo-500 w-4 h-4"
                    checked={Boolean(form[key as keyof VerifyRequest])}
                    onChange={(e) => set(key as keyof VerifyRequest, e.target.checked)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors"
      >
        {loading ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Running QEDSoft Pipeline…</>
        ) : (
          <><Play className="w-4 h-4" /> Run Verification</>
        )}
      </button>
    </form>
  )
}
