<template>
  <NuxtPage />
</template>

<script setup lang="ts">
// Dark mode is set via a blocking inline script in nuxt.config.ts <head>
// so the `dark` class is always present before the first paint — no flash.
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
