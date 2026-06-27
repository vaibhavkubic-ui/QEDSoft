'use client'
import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface Props {
  code: string
  language?: string
}

export default function CodeBlock({ code, language = 'verilog' }: Props) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group rounded-lg overflow-hidden border border-slate-700">
      <button
        onClick={copy}
        className="absolute top-2 right-2 z-10 p-1.5 bg-slate-800 hover:bg-slate-700 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
        title="Copy"
      >
        {copied
          ? <Check className="w-3.5 h-3.5 text-emerald-400" />
          : <Copy className="w-3.5 h-3.5 text-slate-400" />}
      </button>
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        customStyle={{ margin: 0, borderRadius: 0, fontSize: '0.78rem', maxHeight: '400px' }}
        showLineNumbers
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}
