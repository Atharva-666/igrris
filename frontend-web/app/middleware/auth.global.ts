/**
 * middleware/auth.global.ts
 * Route guard — redirect unauthenticated users to /login.
 * Only runs on the client side (no server-side token check needed for MVP).
 */

export default defineNuxtRouteMiddleware(async (to) => {
  // Skip the guard on the landing page & proxy login page itself to avoid redirect loops
  if (to.path === '/' || to.path === '/login') return

  // Only run on client (token lives in server filesystem, not browser)
  if (process.server) return

  const config = useRuntimeConfig()
  const base = config.public.apiBase as string

  try {
    const res = await fetch(`${base}/auth/status`)
    if (!res.ok) throw new Error('not ok')
    const data = await res.json()
    if (!data.authenticated) {
      return navigateTo('/')
    }
  } catch {
    return navigateTo('/')
  }
})
