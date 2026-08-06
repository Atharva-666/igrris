<template>
  <div>
    <ClientOnly>
      <SplashScreen @complete="appReady = true" />
    </ClientOnly>
    <div
      class="transition-opacity duration-700 ease-out"
      :class="appReady ? 'opacity-100' : 'opacity-0 pointer-events-none'"
    >
      <NuxtPage />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const appReady = ref(false)
</script>

<style>
/* Page transition animations */
.page-enter-active,
.page-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.page-enter-from {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.98);
}
</style>
