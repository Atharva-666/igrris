<template>
  <main class="min-h-screen flex items-center justify-center px-4">
    <div class="w-full max-w-sm animate-fade-in">

      <!-- Logo + brand -->
      <div class="flex flex-col items-center mb-10">
        <div class="w-12 h-12 rounded-xl bg-brand-600 flex items-center justify-center mb-4 shadow-lg">
          <!-- Shield SVG icon -->
          <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        </div>
        <h1 class="text-xl font-semibold text-surface-100 tracking-tight">MailShield AI</h1>
        <p class="text-surface-400 text-sm mt-1 text-center leading-relaxed">
          Intelligent Gmail security.<br />Powered by machine learning.
        </p>
      </div>

      <!-- Sign in card -->
      <div class="card">
        <h2 class="text-base font-medium text-surface-100 mb-1">Sign in to continue</h2>
        <p class="text-muted mb-6">Connect your Gmail account to scan and classify your inbox.</p>

        <button
          id="btn-google-signin"
          class="btn-primary w-full justify-center"
          :disabled="loading"
          @click="handleSignIn"
        >
          <!-- Google G icon -->
          <svg v-if="!loading" class="w-4 h-4 shrink-0" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          <svg v-else class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ loading ? 'Redirecting…' : 'Continue with Google' }}
        </button>

        <!-- Error message -->
        <p v-if="error" class="mt-4 text-sm text-red-400 text-center">{{ error }}</p>
      </div>

      <!-- Footer note -->
      <p class="text-center text-muted mt-6 text-xs">
        Only <code class="text-surface-300">gmail.modify</code> &amp; <code class="text-surface-300">gmail.labels</code> permissions are requested.
        No emails are stored.
      </p>
    </div>
  </main>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { login, checkAuth, authenticated } = useAuth()
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const error = ref<string | null>(null)

// On mount — if already authenticated, go to dashboard
onMounted(async () => {
  await checkAuth()
  if (authenticated.value) {
    await router.replace('/')
    return
  }

  // Handle OAuth callback: Google redirects back with ?code=...
  const code = route.query.code as string | undefined
  if (code) {
    loading.value = true
    error.value = null
    try {
      const api = useApi()
      await api.submitCallback(code)
      // Clean URL then navigate to dashboard
      await router.replace('/')
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Authentication failed. Please try again.'
      loading.value = false
    }
  }
})

async function handleSignIn() {
  loading.value = true
  error.value = null
  try {
    await login()
    // login() does window.location.href redirect — no further action needed
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Failed to start sign-in. Is the API server running?'
    loading.value = false
  }
}
</script>
