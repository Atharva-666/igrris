import { inject } from '@vercel/analytics'

export default defineNuxtPlugin(() => {
  if (process.client) {
    inject({
      mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
    })
  }
})
