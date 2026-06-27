import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/Navbar'

export const metadata: Metadata = {
  title: 'QEDSoft — RTL Verification',
  description: 'Verifier-guided autoformalization for semiconductor RTL verification.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  )
}
