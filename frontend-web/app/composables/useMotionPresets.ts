import { ref, onMounted } from 'vue'

export function useMotionPresets() {
  const isReducedMotion = ref(false)

  onMounted(() => {
    // Check if the user prefers reduced motion
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    isReducedMotion.value = mediaQuery.matches

    // Listen for changes
    mediaQuery.addEventListener('change', (e) => {
      isReducedMotion.value = e.matches
    })
  })

  // Fade Up (used for hero sections and scroll reveals)
  const fadeUp = (delay = 0) => {
    if (isReducedMotion.value) {
      return {
        initial: { opacity: 0 },
        enter: { opacity: 1, transition: { duration: 300, delay } }
      }
    }
    
    return {
      initial: {
        opacity: 0,
        y: 20,
      },
      enter: {
        opacity: 1,
        y: 0,
        transition: {
          type: 'spring',
          stiffness: 100,
          damping: 20,
          mass: 1,
          delay
        },
      },
    }
  }

  // Scale In (used for dashboard items popping in)
  const scaleIn = (delay = 0) => {
    if (isReducedMotion.value) {
      return {
        initial: { opacity: 0 },
        enter: { opacity: 1, transition: { duration: 300, delay } }
      }
    }

    return {
      initial: {
        opacity: 0,
        scale: 0.95,
      },
      enter: {
        opacity: 1,
        scale: 1,
        transition: {
          type: 'spring',
          stiffness: 150,
          damping: 15,
          mass: 1,
          delay
        },
      },
    }
  }

  // Subtle Lift Hover (used for cards)
  const hoverLift = () => {
    if (isReducedMotion.value) return {}

    return {
      hovered: {
        y: -4,
        scale: 1.01,
        transition: {
          type: 'spring',
          stiffness: 300,
          damping: 20
        }
      }
    }
  }

  return {
    isReducedMotion,
    fadeUp,
    scaleIn,
    hoverLift
  }
}
