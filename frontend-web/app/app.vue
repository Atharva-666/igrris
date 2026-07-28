<template>
  <div>
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
// Force dark mode on the <html> element at the root level
if (process.client) {
  document.documentElement.classList.add('dark')
}
</script>
