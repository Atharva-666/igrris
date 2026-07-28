<template>
  <div class="min-h-screen flex flex-col">

    <!-- ── Navbar ──────────────────────────────────────────────── -->
    <header class="sticky top-0 z-20 border-b border-surface-800 bg-surface-950/80 backdrop-blur-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
        <!-- Brand -->
        <div class="flex items-center gap-2.5 shrink-0">
          <div class="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <span class="text-sm font-semibold text-surface-100">MailShield AI</span>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <button
            v-if="!scanning"
            id="btn-scan"
            class="btn-primary"
            @click="startScan"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
            Scan Gmail
          </button>
          <button
            v-else
            id="btn-stop-scan"
            class="btn-primary !bg-red-600 hover:!bg-red-700 !border-red-500 !text-white"
            @click="handleStopScan"
            :disabled="stopping"
          >
            <svg v-if="!stopping" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ stopping ? 'Stopping…' : 'Stop Scan' }}
          </button>
          <button id="btn-logout" class="btn-ghost" @click="handleLogout">Sign out</button>
        </div>
      </div>
    </header>

    <!-- ── Main content ────────────────────────────────────────── -->
    <main class="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">

      <!-- Error banner -->
      <div v-if="scanError" class="mb-6 card border-red-900 bg-red-950/30 flex items-start gap-3 !p-4">
        <svg class="w-5 h-5 text-red-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div>
          <p class="text-sm font-medium text-red-300">Scan Error</p>
          <p class="text-sm text-red-400 mt-0.5">{{ scanError }}</p>
        </div>
        <button class="ml-auto btn-ghost !p-1" @click="scanError = null">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Scanning Live Terminal State -->
      <div v-if="scanning" class="mb-8 animate-fade-in">
        <div class="card !p-8 flex flex-col gap-6 w-full max-w-3xl mx-auto">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="relative">
                <div class="w-10 h-10 rounded-full border-2 border-surface-800 border-t-brand-500 animate-spin" />
              </div>
              <div>
                <p class="text-base font-medium text-surface-100">Scanning your inbox…</p>
                <p class="text-muted text-sm mt-0.5">Fetching emails, running ML model, and applying labels.</p>
              </div>
            </div>
            
            <div class="text-right tabular-nums">
              <p class="text-2xl font-semibold text-surface-100">
                <span class="text-brand-400">{{ scanProgress.current }}</span>
                <span class="text-surface-500 text-lg"> / {{ scanProgress.total || '?' }}</span>
              </p>
              <p class="text-muted text-xs uppercase tracking-wider mt-1">Processed</p>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="w-full h-2 bg-surface-800 rounded-full overflow-hidden">
            <div 
              class="h-full bg-brand-500 transition-all duration-300 ease-out"
              :style="{ width: scanProgress.total > 0 ? `${(scanProgress.current / scanProgress.total) * 100}%` : '0%' }"
            ></div>
          </div>

          <!-- Terminal -->
          <div class="bg-black/80 border border-surface-800 rounded-lg p-4 font-mono text-xs overflow-y-auto h-64 shadow-inner" ref="terminalEl">
            <div v-for="(log, idx) in scanLogs" :key="idx" class="text-surface-300 whitespace-pre-wrap leading-relaxed">
              <span class="text-surface-500 select-none mr-2">❯</span>{{ log }}
            </div>
            <!-- Blinking cursor -->
            <div class="text-surface-500 mt-1 animate-pulse">_</div>
          </div>
        </div>
      </div>

      <!-- Empty state (not yet scanned) -->
      <div v-else-if="!results.length && !scanError" class="animate-fade-in">
        <div class="card !p-12 flex flex-col items-center gap-4 text-center max-w-lg mx-auto">
          <div class="w-14 h-14 rounded-2xl bg-surface-800 flex items-center justify-center">
            <svg class="w-7 h-7 text-surface-500" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
          <div>
            <p class="text-base font-medium text-surface-100">No emails scanned yet</p>
            <p class="text-muted mt-1">Click <strong class="text-surface-300">Scan Gmail</strong> to analyse your inbox with the ML model.</p>
          </div>
          <button id="btn-scan-empty" class="btn-primary" @click="startScan">Scan Gmail</button>
        </div>
      </div>

      <!-- Results -->
      <template v-else-if="!scanning && results.length > 0">
        <!-- Stats strip -->
        <ScanStats
          v-if="scanSummary"
          :summary="scanSummary"
          :active-filter="activeFilter"
          class="mb-6 animate-slide-up"
          @filter="(l) => (activeFilter = l)"
        />

        <!-- Controls row -->
        <div class="flex flex-col sm:flex-row gap-3 mb-4">
          <!-- Search -->
          <div class="relative flex-1">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500 pointer-events-none" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35m0 0A7 7 0 104 10a7 7 0 0012.65 6.65z"/>
            </svg>
            <input
              id="input-search"
              v-model="searchQuery"
              class="input pl-9"
              placeholder="Search sender or subject…"
              type="text"
            />
          </div>

          <!-- Filter select -->
          <select
            id="select-filter"
            v-model="activeFilter"
            class="input sm:w-44"
          >
            <option value="">All labels</option>
            <option v-for="l in LABEL_ORDER" :key="l" :value="l">{{ l }}</option>
          </select>

          <!-- Result count -->
          <p class="text-muted self-center shrink-0 text-sm">
            {{ filteredResults.length }} of {{ results.length }} emails
          </p>
        </div>

        <!-- Table -->
        <div class="card !p-0 overflow-hidden animate-slide-up">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-surface-800 text-left">
                <th class="px-4 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider w-64">Sender</th>
                <th class="px-4 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">Subject</th>
                <th class="px-4 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider w-36 hidden sm:table-cell">Label</th>
                <th class="px-4 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider w-24 text-right hidden md:table-cell">Confidence</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="email in paginatedResults"
                :key="email.msg_id"
                class="border-b border-surface-800 last:border-0 hover:bg-surface-800/50 cursor-pointer transition-colors"
                @click="selectedEmail = email"
              >
                <td class="px-4 py-3 text-surface-300 truncate max-w-0 w-64">
                  <p class="truncate font-medium text-surface-200">{{ email.sender }}</p>
                </td>
                <td class="px-4 py-3 text-surface-400 truncate">
                  {{ email.subject || '(no subject)' }}
                </td>
                <td class="px-4 py-3 hidden sm:table-cell">
                  <LabelBadge :label="email.primary_label" />
                </td>
                <td class="px-4 py-3 text-right text-surface-500 hidden md:table-cell tabular-nums">
                  {{ email.confidence > 0 ? `${Math.round(email.confidence * 100)}%` : '—' }}
                </td>
              </tr>
              <tr v-if="!filteredResults.length">
                <td colspan="4" class="px-4 py-8 text-center text-muted">No emails match your filter.</td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 border-t border-surface-800">
            <button id="btn-prev-page" class="btn-ghost text-xs" :disabled="page === 1" @click="page--">← Previous</button>
            <p class="text-muted text-xs">Page {{ page }} of {{ totalPages }}</p>
            <button id="btn-next-page" class="btn-ghost text-xs" :disabled="page === totalPages" @click="page++">Next →</button>
          </div>
        </div>
      </template>
    </main>

    <!-- Email detail slide-over -->
    <EmailDetails :email="selectedEmail" @close="selectedEmail = null" />
  </div>
</template>

<script setup lang="ts">
import type { ScanResult } from '~/composables/useApi'

const { authenticated, checking, checkAuth, logout } = useAuth()
const api = useApi()
const router = useRouter()

// Auth gate
onMounted(async () => {
  await checkAuth()
  if (!authenticated.value) {
    await router.replace('/login')
  }
})

// State
const scanning = ref(false)
const stopping = ref(false)
const scanError = ref<string | null>(null)
const currentScanId = ref<string | null>(null)
const eventSource = ref<EventSource | null>(null)

// SSE Stream data
const scanLogs = ref<string[]>([])
const scanProgress = ref({ current: 0, total: 0 })
const results = ref<ScanResult[]>([])
const scanSummary = ref<Record<string, number> | null>(null)

// UI
const terminalEl = ref<HTMLElement | null>(null)
const selectedEmail = ref<ScanResult | null>(null)
const searchQuery = ref('')
const activeFilter = ref('')
const page = ref(1)
const PAGE_SIZE = 25

const LABEL_ORDER = [
  'Phishing', 'Spam', 'Security', 'Needs Review', 'Banking', 'Orders',
  'Work', 'Education', 'Promotions', 'Personal', 'Trusted',
]

// Auto-scroll terminal
watch(scanLogs, () => {
  nextTick(() => {
    if (terminalEl.value) {
      terminalEl.value.scrollTop = terminalEl.value.scrollHeight
    }
  })
}, { deep: true })

// Filtering & pagination
const filteredResults = computed(() => {
  let list = results.value
  if (activeFilter.value) {
    list = list.filter((r) => r.primary_label === activeFilter.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(
      (r) =>
        r.sender.toLowerCase().includes(q) ||
        r.subject.toLowerCase().includes(q),
    )
  }
  return list
})

// Reset to first page whenever filter/search changes
watch([filteredResults], () => { page.value = 1 })

const totalPages = computed(() => Math.max(1, Math.ceil(filteredResults.value.length / PAGE_SIZE)))

const paginatedResults = computed(() =>
  filteredResults.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE),
)

function updateSummary() {
  const summary: Record<string, number> = {}
  for (const r of results.value) {
    const label = r.primary_label || 'Unknown'
    summary[label] = (summary[label] || 0) + 1
  }
  scanSummary.value = summary
}

// Scan lifecycle
function startScan() {
  // Reset state
  scanning.value = true
  stopping.value = false
  scanError.value = null
  selectedEmail.value = null
  results.value = []
  scanSummary.value = null
  scanLogs.value = ['Connecting to Gmail...']
  scanProgress.value = { current: 0, total: 0 }
  
  // Create unique scan ID
  currentScanId.value = crypto.randomUUID()
  
  // Start stream
  const es = api.createScanStream(currentScanId.value)
  eventSource.value = es
  
  es.addEventListener('log', (e) => {
    const data = JSON.parse(e.data)
    scanLogs.value.push(data.message)
    // Keep max 100 lines so it doesn't leak memory
    if (scanLogs.value.length > 100) scanLogs.value.shift()
  })
  
  es.addEventListener('progress', (e) => {
    const data = JSON.parse(e.data)
    scanProgress.value = data
  })
  
  es.addEventListener('start', (e) => {
    const data = JSON.parse(e.data)
    scanProgress.value.total = data.total
  })
  
  es.addEventListener('result', (e) => {
    const data = JSON.parse(e.data)
    results.value.push(data)
  })
  
  es.addEventListener('done', (e) => {
    const data = JSON.parse(e.data)
    if (data.status === 'cancelled') {
      scanError.value = 'Scan was cancelled.'
    }
    closeStream()
    updateSummary()
  })
  
  es.addEventListener('error', (e) => {
    const data = JSON.parse(e.data)
    scanError.value = data.message || 'Unknown stream error.'
    closeStream()
    updateSummary()
  })
  
  es.onerror = (e) => {
    console.error('SSE Error:', e)
    // If we're stopping, this error is expected when server closes connection
    if (!stopping.value) {
      scanError.value = 'Connection to server lost.'
    }
    closeStream()
    updateSummary()
  }
}

function closeStream() {
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
  scanning.value = false
  stopping.value = false
  currentScanId.value = null
}

async function handleStopScan() {
  if (!currentScanId.value) return
  stopping.value = true
  scanLogs.value.push('Sending stop signal to server...')
  
  try {
    await api.stopScan(currentScanId.value)
  } catch (err: unknown) {
    scanLogs.value.push('Error stopping scan: ' + (err as Error).message)
    stopping.value = false
  }
}

async function handleLogout() {
  await logout()
}

// Clean up
onUnmounted(() => {
  if (eventSource.value) {
    eventSource.value.close()
  }
})
</script>
