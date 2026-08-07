<template>
  <!-- Stats cards strip -->
  <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-3">
    <div
      v-for="item in statItems"
      :key="item.label"
      class="card !p-3 sm:!p-4 flex flex-col gap-0.5 sm:gap-1 cursor-pointer hover:border-surface-700 transition-colors"
      :class="{ 'border-brand-700 ring-1 ring-brand-700': activeFilter === item.label }"
      @click="emit('filter', item.label === activeFilter ? '' : item.label)"
    >
      <p class="text-[11px] sm:text-xs text-surface-500 font-medium truncate">{{ item.label }}</p>
      <p class="text-xl sm:text-2xl font-semibold text-surface-100">{{ item.count }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  summary: Record<string, number>
  activeFilter: string
}>()

const emit = defineEmits<{ filter: [label: string] }>()

const LABEL_ORDER = [
  'Phishing', 'Spam', 'Security', 'Needs Review', 'Banking', 'Orders',
  'Work', 'Education', 'Promotions', 'Personal', 'Trusted',
]

const statItems = computed(() =>
  LABEL_ORDER
    .filter((l) => (props.summary[l] ?? 0) > 0)
    .map((l) => ({ label: l, count: props.summary[l] }))
)
</script>
