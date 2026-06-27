import Link from 'next/link'
import { ArrowRight, Cpu, FileCode2, GitBranch, ShieldCheck, Zap, BarChart3, Wrench } from 'lucide-react'

const jobs = [
  {
    icon: <GitBranch className="w-6 h-6 text-cyan-400" />,
    title: 'Job 1 — Source to Lean4',
    desc: 'Converts MATLAB golden models and SystemVerilog RTL into Lean4 transition skeletons with a formal equivalence obligation.',
    tags: ['MATLAB → Lean4', 'HDL → Lean4', 'Equivalence Proof'],
  },
  {
    icon: <FileCode2 className="w-6 h-6 text-indigo-400" />,
    title: 'Job 2 — QEDAI Autoformalize',
    desc: 'Extracts requirements from natural-language specs using LLM + regex fallback, then generates SVA assertions and Lean4 contracts.',
    tags: ['NL → Requirements', 'SVA Generation', 'Lean4 Contracts'],
  },
  {
    icon: <Wrench className="w-6 h-6 text-emerald-400" />,
    title: 'Job 3 — Verify, Repair & Report',
    desc: 'Runs static verification, applies SERA-VGP automated repair on failing assertions, and produces a full bottleneck report.',
    tags: ['Static SVA Check', 'Auto-Repair', 'Coverage Report'],
  },
]

const bottlenecks = [
  { icon: <Zap className="w-4 h-4" />, problem: 'Specs are informal and ambiguous', fix: 'LLM + regex extraction with confidence scoring' },
  { icon: <Zap className="w-4 h-4" />, problem: 'Signal names in specs don\'t match RTL', fix: 'Fuzzy signal mapping with difflib' },
  { icon: <Zap className="w-4 h-4" />, problem: 'SVA writing requires formal expertise', fix: 'Automatic SVA generation from NL requirements' },
  { icon: <Zap className="w-4 h-4" />, problem: 'Formal tool diagnostics are not acted on', fix: 'SERA-VGP automated repair loop' },
  { icon: <Zap className="w-4 h-4" />, problem: 'MATLAB and RTL verified in separate flows', fix: 'Job 1 unifies both into Lean4 equivalence proof' },
  { icon: <Zap className="w-4 h-4" />, problem: 'Verification coverage hard to trace to requirements', fix: 'mapping_coverage metric with REQ → SVA traceability' },
]

export default function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6">

      {/* Hero */}
      <section className="py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-indigo-950/60 border border-indigo-800/50 text-indigo-300 text-xs px-3 py-1.5 rounded-full mb-6">
          <Cpu className="w-3.5 h-3.5" />
          Semiconductor RTL Verification · Aligned with ISO 26262 / ASIL-D
        </div>
        <h1 className="text-5xl sm:text-6xl font-bold text-white mb-6 leading-tight">
          Natural Language<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">
            to Formal Verification
          </span>
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
          QEDSoft converts plain-English chip specs and SystemVerilog RTL into
          SystemVerilog Assertions, Lean4 proof contracts, and bottleneck reports —
          automatically.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link
            href="/verify"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-6 py-3 rounded-lg transition-colors"
          >
            Try it Live <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="https://qedsoft-production.up.railway.app/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white px-6 py-3 rounded-lg transition-colors"
          >
            API Docs
          </a>
        </div>

        {/* Stats */}
        <div className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl mx-auto">
          {[
            { label: 'Input', value: 'Plain English Spec' },
            { label: 'Output', value: 'SVA + Lean4' },
            { label: 'Repair', value: 'Auto SERA-VGP' },
            { label: 'Coverage', value: '100% Traceable' },
          ].map((s) => (
            <div key={s.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-slate-400 text-xs mb-1">{s.label}</div>
              <div className="text-white font-semibold text-sm">{s.value}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Three Jobs */}
      <section className="py-16">
        <h2 className="text-3xl font-bold text-white text-center mb-3">Three-Job Pipeline</h2>
        <p className="text-slate-400 text-center mb-12">End-to-end from specification to verified artifacts</p>
        <div className="grid md:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <div key={job.title} className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-600 transition-colors">
              <div className="mb-4">{job.icon}</div>
              <h3 className="font-semibold text-white mb-2">{job.title}</h3>
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">{job.desc}</p>
              <div className="flex flex-wrap gap-2">
                {job.tags.map((tag) => (
                  <span key={tag} className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded-md">{tag}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Industry Bottlenecks */}
      <section className="py-16">
        <h2 className="text-3xl font-bold text-white text-center mb-3">Industry Problems Solved</h2>
        <p className="text-slate-400 text-center mb-12">Built around verification pain points at companies like Infineon, NXP, Renesas</p>
        <div className="grid md:grid-cols-2 gap-4">
          {bottlenecks.map((b) => (
            <div key={b.problem} className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 flex gap-4">
              <div className="shrink-0 w-8 h-8 bg-red-950/60 border border-red-800/40 rounded-lg flex items-center justify-center text-red-400 mt-0.5">
                {b.icon}
              </div>
              <div>
                <div className="text-slate-300 font-medium text-sm mb-1">{b.problem}</div>
                <div className="text-emerald-400 text-sm flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                  {b.fix}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="py-16">
        <h2 className="text-3xl font-bold text-white text-center mb-12">How It Works</h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {[
            { step: '01', title: 'Paste Your Inputs', desc: 'Add your natural-language spec, optional RTL SystemVerilog, and optional MATLAB model.' },
            { step: '02', title: 'QEDSoft Formalizes', desc: 'LLM extracts requirements, maps signals, generates SVA properties and Lean4 contracts automatically.' },
            { step: '03', title: 'Review Artifacts', desc: 'Get SVA assertions, Lean4 proofs, coverage metrics, and bottleneck recommendations instantly.' },
          ].map((s) => (
            <div key={s.step} className="text-center">
              <div className="text-5xl font-black text-slate-800 mb-3">{s.step}</div>
              <h3 className="text-white font-semibold mb-2">{s.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 text-center">
        <div className="bg-gradient-to-r from-indigo-950/60 to-cyan-950/40 border border-indigo-800/30 rounded-2xl p-12">
          <BarChart3 className="w-10 h-10 text-indigo-400 mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-3">Ready to formalize your chip spec?</h2>
          <p className="text-slate-400 mb-8">Paste a spec and RTL — get SVA assertions in seconds.</p>
          <Link
            href="/verify"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-8 py-3 rounded-lg transition-colors"
          >
            Start Verification <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-slate-800 py-8 text-center text-slate-500 text-sm">
        QEDSoft v0.1.0 · Deployed on Railway ·{' '}
        <a href="https://github.com/vaibhavkubic-ui/QEDSoft" className="hover:text-slate-300 underline">GitHub</a>
      </footer>
    </div>
  )
}
