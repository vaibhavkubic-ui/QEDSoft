import type { QEDSoftResult, VerifyRequest } from '@/types/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://qedsoft-production.up.railway.app'

export async function verify(request: VerifyRequest): Promise<QEDSoftResult> {
  const response = await fetch(`${API_URL}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API error ${response.status}: ${error}`)
  }
  return response.json()
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`)
    return response.ok
  } catch {
    return false
  }
}
