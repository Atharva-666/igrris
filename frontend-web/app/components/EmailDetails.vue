<template>
  <!-- Slide-over panel -->
  <Transition name="slide-panel">
    <aside
      v-if="email"
      class="fixed inset-y-0 right-0 w-full sm:max-w-lg bg-surface-900 border-l border-surface-800 z-50 flex flex-col shadow-2xl"
    >
      <!-- Header -->
      <div class="flex items-start justify-between gap-4 p-4 sm:p-6 border-b border-surface-800">
        <div class="min-w-0 flex-1">
          <h2 class="text-sm sm:text-base font-semibold text-surface-100 truncate">{{ email.subject || '(no subject)' }}</h2>
          <p class="text-muted text-xs sm:text-sm mt-0.5 truncate">{{ email.sender }}</p>
        </div>
        <button
          id="btn-close-detail"
          class="btn-ghost p-2 -mr-2 shrink-0"
          aria-label="Close"
          @click="emit('close')"
        >
          <!-- X icon -->
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 sm:space-y-6">

        <!-- Label & confidence row -->
        <div class="flex items-center gap-3 sm:gap-4 flex-wrap">
          <div>
            <p class="text-[10px] sm:text-xs font-medium text-surface-500 uppercase tracking-wider mb-1">Label</p>
            <LabelBadge :label="email.primary_label" />
          </div>
          <div v-if="email.secondary_label">
            <p class="text-[10px] sm:text-xs font-medium text-surface-500 uppercase tracking-wider mb-1">Secondary</p>
            <LabelBadge :label="email.secondary_label" />
          </div>
          <div v-if="email.confidence > 0">
            <p class="text-[10px] sm:text-xs font-medium text-surface-500 uppercase tracking-wider mb-1">Confidence</p>
            <div class="flex items-center gap-2">
              <div class="w-20 sm:w-24 h-1.5 bg-surface-800 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :class="confidenceBarColor"
                  :style="{ width: `${Math.round(email.confidence * 100)}%` }"
                />
              </div>
              <span class="text-xs sm:text-sm font-medium text-surface-200">{{ Math.round(email.confidence * 100) }}%</span>
            </div>
          </div>
        </div>

        <!-- Metadata grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
          <div class="card !p-3.5 sm:!p-4">
            <p class="text-[10px] sm:text-xs font-medium text-surface-500 uppercase tracking-wider mb-1">ML Prediction</p>
            <p class="text-xs sm:text-sm font-medium" :class="email.ml_label === 'spam' ? 'text-red-400' : 'text-green-400'">
              {{ email.ml_label === 'spam' ? '🚨 Spam' : email.ml_label === 'ham' ? '✓ Legitimate' : '? Unknown' }}
            </p>
          </div>
          <div class="card !p-3.5 sm:!p-4">
            <p class="text-[10px] sm:text-xs font-medium text-surface-500 uppercase tracking-wider mb-1">Classification</p>
            <p class="text-xs sm:text-sm text-surface-300">{{ email.layer === 'ml' ? 'ML Model' : email.layer === 'rules' ? 'Rule Engine' : email.layer }}</p>
          </div>
          <div class="card !p-3.5 sm:!p-4 sm:col-span-2">
            <p class="text-[10px] sm:text-xs font-medium text-surface-500 uppercase tracking-wider mb-1">Matched Rule</p>
            <p class="text-xs sm:text-sm text-surface-300 font-mono break-all">{{ email.matched_rule || '—' }}</p>
          </div>
        </div>

        <!-- Status badge -->
        <div class="flex items-center gap-2 pt-1">
          <div
            class="w-2 h-2 rounded-full shrink-0"
            :class="email.status === 'labeled' ? 'bg-green-500' : 'bg-red-500'"
          />
          <p class="text-xs sm:text-sm text-surface-400">
            {{ email.status === 'labeled' ? 'Label applied to Gmail' : 'Failed to apply label' }}
          </p>
        </div>
      </div>
    </aside>
  </Transition>

  <!-- Backdrop -->
  <Transition name="fade">
    <div
      v-if="email"
      class="fixed inset-0 bg-black/60 z-40 backdrop-blur-sm"
      @click="emit('close')"
    />
  </Transition>
</template>

<script setup lang="ts">
import type { ScanResult } from '~/composables/useApi'

defineProps<{ email: ScanResult | null }>()
const emit = defineEmits<{ close: [] }>()

const confidenceBarColor = computed(() => {
  // Note: we need to access it via prop — use a workaround via inject or just inline
  return 'bg-brand-500'
})
</script>

<style scoped>
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-panel-enter-from,
.slide-panel-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
