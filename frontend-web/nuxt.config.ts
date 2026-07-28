// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },

  // Use the app/ directory (Nuxt 3 default for minimal template)
  srcDir: 'app/',

  // Auto-import components, composables, utils
  components: [{ path: '~/components', pathPrefix: false }],

  // Global CSS
  css: ['~/assets/css/main.css'],

  // Tailwind CSS via @nuxtjs/tailwindcss module
  modules: ['@nuxtjs/tailwindcss'],

  // Dark mode default — handled by Tailwind 'class' strategy in tailwind.config
  app: {
    head: {
      title: 'MailShield AI',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        {
          name: 'description',
          content: 'MailShield AI — Intelligent Gmail security assistant powered by machine learning.',
        },
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
        },
      ],
    },
  },

  // Proxy API requests to the FastAPI server
  routeRules: {
    '/api/**': { proxy: 'http://localhost:8000/**' },
  },

  // Runtime config — public values are exposed to the browser
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? '/api',
    },
  },
})
