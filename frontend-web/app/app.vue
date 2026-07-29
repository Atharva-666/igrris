<template>
  <WavyBackground>
    <NuxtPage />
  </WavyBackground>
</template>

<script setup lang="ts">
// Force dark mode on the <html> element at the root level
if (process.client) {
  document.documentElement.classList.add('dark')
}
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
