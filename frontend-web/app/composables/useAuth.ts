/**
 * composables/useAuth.ts
 * Reactive auth state shared across the app.
 * On mount, checks /auth/status; provides login() and logout() helpers.
 */

import { useApi } from './useApi'

export function useAuth() {
  const api = useApi()
  const router = useRouter()

  const authenticated = useState<boolean>('auth.authenticated', () => false)
  const checking = useState<boolean>('auth.checking', () => true)

  /** Check auth status from server — call on app boot */
  async function checkAuth() {
    checking.value = true
    try {
      const status = await api.getAuthStatus()
      authenticated.value = status.authenticated
    } catch {
      authenticated.value = false
    } finally {
      checking.value = false
    }
  }

  /** Redirect to Google OAuth */
  async function login() {
    const { url } = await api.getAuthUrl()
    window.location.href = url
  }

  /** Call /auth/logout then navigate to login page */
  async function logout() {
    try {
      await api.logout()
    } finally {
      authenticated.value = false
      await router.push('/login')
    }
  }

  return {
    authenticated,
    checking,
    checkAuth,
    login,
    logout,
  }
}
