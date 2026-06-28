import Link from 'next/link'
import { ArrowRight, Cpu, FileCode2, GitBranch, BarChart3, Wrench } from 'lucide-react'

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



export default function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6">

      {/* Hero */}
      <section className="py-24 text-center">
        <h1 className="text-5xl sm:text-6xl font-bold text-white mb-6 leading-tight">
          Semiconductor RTL<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">
            Verification
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
          <button
            disabled
            className="inline-flex items-center gap-2 border border-slate-800 text-slate-500 px-6 py-3 rounded-lg cursor-not-allowed opacity-50 bg-slate-900/50"
          >
            API Docs
          </button>
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
        QEDSoft v0.1.0 · Deployed on Railway
      </footer>
    </div>
  )
}
