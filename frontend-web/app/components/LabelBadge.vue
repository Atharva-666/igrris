<template>
  <span
    class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border"
    :class="colorClass"
  >
    {{ label }}
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{ label: string }>()

const LABEL_COLORS: Record<string, string> = {
  Trusted:      'bg-green-950    text-green-400    border-green-900',
  Spam:         'bg-red-950      text-red-400      border-red-900',
  Phishing:     'bg-red-950      text-red-300      border-red-800',
  'Needs Review': 'bg-amber-950  text-amber-400    border-amber-900',
  Security:     'bg-blue-950     text-blue-400     border-blue-900',
  Banking:      'bg-teal-950     text-teal-400     border-teal-900',
  Orders:       'bg-purple-950   text-purple-400   border-purple-900',
  Promotions:   'bg-orange-950   text-orange-400   border-orange-900',
  Education:    'bg-cyan-950     text-cyan-400     border-cyan-900',
  Work:         'bg-indigo-950   text-indigo-400   border-indigo-900',
  Personal:     'bg-surface-800  text-surface-300  border-surface-700',
}

const colorClass = computed(
  () => LABEL_COLORS[props.label] ?? 'bg-surface-800 text-surface-300 border-surface-700',
)
</script>
