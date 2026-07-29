<template>
  <main class="relative text-surface-100 overflow-hidden">
    <!-- Header -->
    <header class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-[0_0_15px_rgba(var(--color-brand-600),0.5)]">
          <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        </div>
        <span class="text-lg font-bold tracking-tight text-white">MailShield AI</span>
      </div>
      <div>
        <InteractiveHoverButton
          class="!bg-white/10 hover:!bg-white/20 border-white/10 !text-white shadow-none backdrop-blur-md"
          @click="handleSignIn"
          :disabled="loading"
          :text="loading ? 'Connecting...' : 'Sign In'"
        />
      </div>
    </header>

    <!-- Hero Section -->
    <section class="relative z-10 pt-24 pb-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col items-center text-center">
      <div 
        v-motion :initial="fadeUp(0).initial" :enter="fadeUp(0).enter"
        class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-900/30 border border-brand-800/50 text-brand-300 text-sm font-medium mb-8"
      >
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-brand-500"></span>
        </span>
        Machine Learning Powered Security
      </div>
      
      <h1 
        v-motion :initial="fadeUp(150).initial" :enter="fadeUp(150).enter"
        class="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 text-transparent bg-clip-text bg-gradient-to-b from-white to-surface-400 max-w-4xl"
      >
        Intelligent threat detection for your inbox.
      </h1>
      
      <p 
        v-motion :initial="fadeUp(300).initial" :enter="fadeUp(300).enter"
        class="text-lg md:text-xl text-surface-400 max-w-2xl mb-12 leading-relaxed"
      >
        MailShield AI scans your Gmail using an advanced LinearSVC machine learning model to automatically categorize emails, block phishing attempts, and keep your inbox secure.
      </p>
      
      <div 
        v-motion :initial="fadeUp(450).initial" :enter="fadeUp(450).enter"
        class="flex flex-col sm:flex-row gap-4 items-center w-full justify-center max-w-md"
      >
        <ShimmerButton
          class="w-full sm:w-auto shadow-2xl"
          shimmer-color="rgba(255, 255, 255, 0.4)"
          shimmer-size="2px"
          border-radius="100px"
          shimmer-duration="3s"
          background="#000000"
          @click="handleSignIn"
          :disabled="loading"
        >
          <span class="flex items-center gap-2 text-white font-semibold text-lg whitespace-nowrap">
            {{ loading ? 'Connecting...' : 'Secure Your Inbox' }}
          </span>
        </ShimmerButton>
      </div>
      
      <p v-if="error" class="mt-6 text-sm text-red-400 bg-red-950/50 border border-red-900/50 px-4 py-2 rounded-lg max-w-md mx-auto">
        {{ error }}
      </p>
      <p class="mt-6 text-xs text-surface-500 max-w-sm">
        We only request <span class="text-surface-300">gmail.modify</span> & <span class="text-surface-300">gmail.labels</span>. We never store your emails.
      </p>
    </section>

    <!-- Features Grid -->
    <section class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-32">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        <!-- Feature 1 -->
        <div 
          v-motion :initial="fadeUp(0).initial" :visible-once="fadeUp(0).enter"
          class="bg-surface-900/50 backdrop-blur-md border border-surface-800 p-8 rounded-2xl hover:bg-surface-800/50 transition-colors duration-300 group"
        >
          <div class="w-12 h-12 rounded-xl bg-red-950/50 border border-red-900/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
            <svg class="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-white mb-3">Threat Mitigation</h3>
          <p class="text-surface-400 leading-relaxed text-sm">
            Instantly flags <span class="text-red-400 font-medium">Phishing</span> and <span class="text-amber-400 font-medium">Spam</span> attempts with deep textual analysis and TF-IDF vectorization.
          </p>
        </div>

        <!-- Feature 2 -->
        <div 
          v-motion :initial="fadeUp(150).initial" :visible-once="fadeUp(150).enter"
          class="bg-surface-900/50 backdrop-blur-md border border-surface-800 p-8 rounded-2xl hover:bg-surface-800/50 transition-colors duration-300 group"
        >
          <div class="w-12 h-12 rounded-xl bg-blue-950/50 border border-blue-900/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
            <svg class="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002 2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-white mb-3">Smart Categorization</h3>
          <p class="text-surface-400 leading-relaxed text-sm">
            Automatically sorts your inbox into 11 distinct labels including <span class="text-cyan-400 font-medium">Work</span>, <span class="text-teal-400 font-medium">Banking</span>, <span class="text-orange-400 font-medium">Promotions</span>, and <span class="text-purple-400 font-medium">Orders</span>.
          </p>
        </div>

        <!-- Feature 3 -->
        <div 
          v-motion :initial="fadeUp(300).initial" :visible-once="fadeUp(300).enter"
          class="bg-surface-900/50 backdrop-blur-md border border-surface-800 p-8 rounded-2xl hover:bg-surface-800/50 transition-colors duration-300 group"
        >
          <div class="w-12 h-12 rounded-xl bg-brand-950/50 border border-brand-900/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
            <svg class="w-6 h-6 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-white mb-3">Live Processing</h3>
          <p class="text-surface-400 leading-relaxed text-sm">
            Watch the ML model process your inbox in real-time. Server-Sent Events stream scan progress directly to a sleek terminal interface.
          </p>
        </div>

      </div>
    </section>

    <!-- Footer -->
    <footer class="relative z-10 border-t border-surface-800 py-8 text-center text-surface-500 text-sm">
      <p>Powered by Vue 3, FastAPI, and LinearSVC.</p>
    </footer>
  </main>
</template>

<script setup lang="ts">
import { useMotionPresets } from '~/composables/useMotionPresets'

definePageMeta({ layout: false })

const { login, checkAuth, authenticated } = useAuth()
const { fadeUp } = useMotionPresets()
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const error = ref<string | null>(null)

// On mount — if already authenticated, go to dashboard
onMounted(async () => {
  await checkAuth()
  if (authenticated.value) {
    await router.replace('/dashboard')
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
      await router.replace('/dashboard')
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

<style scoped>
@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}
.animate-shimmer {
  transform: translateX(-100%);
  animation: shimmer 2s infinite;
}
</style>
