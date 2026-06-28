'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Cpu } from 'lucide-react'

export default function Navbar() {
  const path = usePathname()
  const link = (href: string, label: string) => (
    <Link
      href={href}
      className={`text-sm px-3 py-1.5 rounded-md transition-colors ${
        path === href
          ? 'bg-indigo-600 text-white'
          : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
      }`}
    >
      {label}
    </Link>
  )
  return (
    <nav className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-semibold text-white">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <span>QEDSoft</span>
          <span className="text-xs text-slate-500 font-normal ml-1">v0.1.0</span>
        </Link>
        <div className="flex items-center gap-1">
          {link('/', 'Home')}
          {link('/verify', 'Verify')}
        </div>
      </div>
    </nav>
  )
}
