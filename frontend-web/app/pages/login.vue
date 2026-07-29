<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="flex flex-col items-center gap-4 animate-fade-in">
      <div class="w-10 h-10 border-4 border-surface-800 border-t-brand-500 rounded-full animate-spin"></div>
      <p class="text-surface-400 text-sm font-medium">Authenticating...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const route = useRoute()
const router = useRouter()

onMounted(() => {
  // Google Cloud Console is strictly configured to redirect to /login
  // Since we moved the UI to /, we just forward the OAuth query parameters (like ?code=...) there!
  router.replace({ path: '/', query: route.query })
})
</script>
