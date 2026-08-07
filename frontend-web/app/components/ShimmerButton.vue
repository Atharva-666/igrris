<template>
  <button
    type="button"
    :class="[
      'group relative inline-flex items-center justify-center overflow-hidden transition-transform duration-300',
      'hover:scale-[1.02] active:scale-[0.98]',
      $props.class
    ]"
    :style="{
      '--shimmer-color': shimmerColor,
      '--shimmer-size': shimmerSize,
      '--border-radius': borderRadius,
      '--shimmer-duration': shimmerDuration,
      '--bg': background,
      borderRadius: borderRadius
    }"
    v-bind="$attrs"
  >
    <div class="absolute inset-0 z-0 overflow-hidden" :style="{ borderRadius: borderRadius }">
      <!-- Rotating conic gradient (the shimmer) -->
      <div 
        class="absolute inset-[-100vh] transition-opacity duration-300 opacity-100 group-hover:opacity-100"
        :style="{
          background: 'conic-gradient(from 0deg, transparent 0 200deg, var(--shimmer-color) 360deg)',
          animation: `spin var(--shimmer-duration) linear infinite`
        }"
      ></div>
    </div>
    
    <!-- Inner mask to create the border effect -->
    <div 
      class="absolute z-10 transition-colors duration-300"
      :style="{
        top: 'var(--shimmer-size)',
        right: 'var(--shimmer-size)',
        bottom: 'var(--shimmer-size)',
        left: 'var(--shimmer-size)',
        background: 'var(--bg)',
        borderRadius: `calc(var(--border-radius) - var(--shimmer-size))`
      }"
    ></div>

    <!-- Content Slot -->
    <div class="relative z-20 flex items-center justify-center px-6 py-3">
      <slot />
    </div>
  </button>
</template>

<script setup lang="ts">
interface Props {
  shimmerColor?: string;
  shimmerSize?: string;
  borderRadius?: string;
  shimmerDuration?: string;
  background?: string;
  class?: any;
}

withDefaults(defineProps<Props>(), {
  shimmerColor: "#ffffff",
  shimmerSize: "20px",
  borderRadius: "100px",
  shimmerDuration: "4s",
  background: "rgba(2, 6, 23, 1)", // Default tailwind surface-950
});
</script>
