import Lenis from 'lenis'

export default defineNuxtPlugin((nuxtApp) => {
  if (process.server) return

  // Check for reduced motion
  const isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  // Detect mobile device (rough heuristic) to skip lenis on touch screens
  const isMobile = window.innerWidth <= 768 || 'ontouchstart' in window

  if (isReducedMotion || isMobile) {
    return // Skip Lenis initialization
  }

  // Initialize Lenis
  const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // smooth ease out
    orientation: 'vertical',
    gestureOrientation: 'vertical',
    smoothWheel: true,
    wheelMultiplier: 1,
    touchMultiplier: 2,
    infinite: false,
  })

  // Hook Lenis into Nuxt's requestAnimationFrame
  let isPaused = false

  function raf(time: number) {
    if (!isPaused) {
      lenis.raf(time)
    }
    requestAnimationFrame(raf)
  }

  requestAnimationFrame(raf)

  // Pause animations when tab is inactive to save CPU/GPU
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      isPaused = true
    } else {
      isPaused = false
    }
  })

  // Provide to app context
  nuxtApp.provide('lenis', lenis)
})
