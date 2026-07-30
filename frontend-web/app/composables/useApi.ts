/**
 * composables/useApi.ts
 * Central API abstraction. All HTTP calls to the FastAPI backend go through here.
 * Uses Nuxt's $fetch with the runtime-config apiBase, so it works in both
 * dev (proxied at /api) and production (set NUXT_PUBLIC_API_BASE=https://…).
 */

export interface ScanResult {
  msg_id: string
  sender: string
  subject: string
  ml_label: 'spam' | 'ham' | 'unknown'
  primary_label: string
  secondary_label: string | null
  confidence: number
  matched_rule: string
  layer: string
  status: 'labeled' | 'error'
}

export interface ScanResponse {
  total: number
  results: ScanResult[]
  summary: Record<string, number>
}

export interface PredictionResponse {
  label: string
  confidence: number
}

export interface AuthStatus {
  authenticated: boolean
  email?: string | null
  picture?: string | null
  name?: string | null
}

export function useApi() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase as string

  async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${base}${path}`
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail ?? `HTTP ${res.status}`)
    }
    return res.json() as Promise<T>
  }

  /** Check if user is authenticated */
  function getAuthStatus() {
    return apiFetch<AuthStatus>('/auth/status')
  }

  /** Get the Google OAuth authorization URL */
  function getAuthUrl() {
    return apiFetch<{ url: string }>('/auth/url')
  }

  /** Exchange an OAuth code for credentials */
  function submitCallback(code: string) {
    return apiFetch<AuthStatus>('/auth/callback', {
      method: 'POST',
      body: JSON.stringify({ code }),
    })
  }

  /** Log out — revokes token on server */
  function logout() {
    return apiFetch<AuthStatus>('/auth/logout', { method: 'POST' })
  }

  /** Create a streaming connection to the scan endpoint */
  function createScanStream(scanId: string): EventSource {
    const url = `${base}/scan/stream?scan_id=${scanId}`
    // Return the native EventSource object so the component can attach listeners
    return new EventSource(url)
  }

  /** Stop a running scan */
  function stopScan(scanId: string) {
    return apiFetch(`/scan/stop/${scanId}`, { method: 'POST' })
  }

  /** Predict a single message */
  function predictMessage(text: string) {
    return apiFetch<PredictionResponse>('/predict', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  }

  return {
    getAuthStatus,
    getAuthUrl,
    submitCallback,
    logout,
    createScanStream,
    stopScan,
    predictMessage,
  }
}
