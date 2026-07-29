<template>
  <div class="relative min-h-screen bg-surface-950 text-surface-100 overflow-hidden aurora-container">
    
    <!-- SVG Filter Definition -->
    <svg class="absolute w-0 h-0 pointer-events-none" aria-hidden="true">
      <defs>
        <filter id="smoke-distortion" x="-20%" y="-20%" width="140%" height="140%">
          <!-- Fractal noise for organic smoke texture -->
          <feTurbulence 
            type="fractalNoise" 
            baseFrequency="0.003 0.02" 
            numOctaves="3" 
            seed="4" 
            result="noise"
          >
            <!-- Slowly animate the turbulence frequency for an ever-changing organic look -->
            <animate 
              attributeName="baseFrequency" 
              values="0.003 0.02; 0.005 0.025; 0.003 0.02" 
              dur="45s" 
              repeatCount="indefinite" 
            />
          </feTurbulence>
          <!-- Displace the graphics using the noise -->
          <feDisplacementMap 
            in="SourceGraphic" 
            in2="noise" 
            scale="150" 
            xChannelSelector="R" 
            yChannelSelector="G" 
          />
        </filter>
      </defs>
    </svg>

    <!-- Aurora Background Layer -->
    <div 
      v-if="!isReducedMotion"
      class="absolute inset-0 pointer-events-none smoke-wrapper overflow-hidden"
    >
      <!-- The layer that receives the SVG distortion -->
      <div 
        class="smoke-layer absolute inset-0"
        :style="smokeLayerStyle"
      >
        <!-- Organic Blobs (Monochrome) -->
        <div class="blob blob-1" :style="getBlobStyle(0.04, -0.02)"></div>
        <div class="blob blob-2" :style="getBlobStyle(-0.03, 0.03)"></div>
        <div class="blob blob-3" :style="getBlobStyle(0.02, 0.05)"></div>
        <div class="blob blob-4" :style="getBlobStyle(-0.04, -0.04)"></div>
        <div class="blob blob-5" :style="getBlobStyle(0.05, -0.01)"></div>
      </div>
      
      <!-- Overlay vignette & subtle noise texture to eliminate banding -->
      <div class="absolute inset-0 noise-overlay mix-blend-soft-light opacity-[0.15]"></div>
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-surface-950/40 to-surface-950 pointer-events-none"></div>
    </div>

    <!-- Content Slot -->
    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useMouse, useWindowScroll, useWindowSize } from '@vueuse/core'
import { useMotionPresets } from '~/composables/useMotionPresets'

const { isReducedMotion } = useMotionPresets()

// Interaction hooks
const { x, y } = useMouse({ type: 'client' })
const { y: scrollY } = useWindowScroll()
const { width, height } = useWindowSize()

// Smooth interpolated values for physics-like interaction
const smoothX = ref(0)
const smoothY = ref(0)
const smoothScroll = ref(0)

let rafId: number

const updatePhysics = () => {
  // Center origin
  const targetX = width.value > 0 ? (x.value - width.value / 2) : 0
  const targetY = height.value > 0 ? (y.value - height.value / 2) : 0

  // Lerp towards target for smoothness
  smoothX.value += (targetX - smoothX.value) * 0.03
  smoothY.value += (targetY - smoothY.value) * 0.03
  smoothScroll.value += (scrollY.value - smoothScroll.value) * 0.05

  rafId = requestAnimationFrame(updatePhysics)
}

onMounted(() => {
  if (!isReducedMotion.value) {
    rafId = requestAnimationFrame(updatePhysics)
  }
})

// Unmount is automatically handled for refs, but we'd clear raf in a real app if this unmounts often.
// Since it's a global background, it stays mounted.

// Compute subtle transform for the entire smoke layer based on scroll
const smokeLayerStyle = computed(() => {
  if (isReducedMotion.value) return {}
  return {
    transform: `translate3d(0, ${-smoothScroll.value * 0.15}px, 0)`
  }
})

// Compute subtle, independent parallax for each blob based on mouse movement
const getBlobStyle = (multiplierX: number, multiplierY: number) => {
  if (isReducedMotion.value) return {}
  return {
    transform: `translate3d(${smoothX.value * multiplierX}px, ${smoothY.value * multiplierY}px, 0)`
  }
}
</script>

<style scoped>
.aurora-container {
  background-color: #020617; /* surface-950 */
}

/* 
  The smoke-layer applies the heavy SVG displacement filter and large blur.
  We scale it up so the distorted edges don't bleed into the screen.
*/
.smoke-layer {
  width: 140%;
  height: 140%;
  top: -20%;
  left: -20%;
  /* Large blur combined with anisotropic noise creates the aurora beams */
  filter: url('#smoke-distortion') blur(60px);
  mix-blend-mode: screen;
  will-change: transform;
}

.blob {
  position: absolute;
  border-radius: 50%;
  mix-blend-mode: screen;
  will-change: transform;
  /* Hardware acceleration */
  backface-visibility: hidden;
  perspective: 1000;
}

/* Ribbon 1 (Soft White) */
.blob-1 {
  background: radial-gradient(ellipse at 50% 50%, rgba(255, 255, 255, 0.25) 0%, transparent 70%);
  width: 150vw;
  height: 40vh;
  top: 15%;
  left: -20%;
  animation: aurora-sweep-1 28s ease-in-out infinite alternate;
}

/* Ribbon 2 (Silver) */
.blob-2 {
  background: radial-gradient(ellipse at 50% 50%, rgba(200, 200, 200, 0.15) 0%, transparent 65%);
  width: 180vw;
  height: 35vh;
  top: 40%;
  left: -30%;
  animation: aurora-sweep-2 34s ease-in-out infinite alternate-reverse;
}

/* Ribbon 3 (Light Grey) */
.blob-3 {
  background: radial-gradient(ellipse at 50% 50%, rgba(220, 220, 220, 0.2) 0%, transparent 70%);
  width: 160vw;
  height: 45vh;
  bottom: -10%;
  left: -15%;
  animation: aurora-sweep-3 31s ease-in-out infinite alternate;
}

/* Ribbon 4 (Darker Grey) */
.blob-4 {
  background: radial-gradient(ellipse at 50% 50%, rgba(150, 150, 150, 0.15) 0%, transparent 75%);
  width: 200vw;
  height: 50vh;
  top: -15%;
  right: -30%;
  animation: aurora-sweep-4 38s ease-in-out infinite alternate-reverse;
}

/* Ribbon 5 (Faint White) */
.blob-5 {
  background: radial-gradient(ellipse at 50% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 60%);
  width: 140vw;
  height: 30vh;
  bottom: 25%;
  right: -20%;
  animation: aurora-sweep-5 26s ease-in-out infinite alternate;
}

/* Complex organic sweep animations for aurora ribbons */
@keyframes aurora-sweep-1 {
  0%   { transform: translate(0, 0) scale(1) rotate(-15deg); }
  33%  { transform: translate(5%, -10%) scale(1.05) rotate(-10deg); }
  66%  { transform: translate(-5%, 15%) scale(0.95) rotate(-20deg); }
  100% { transform: translate(10%, -5%) scale(1.1) rotate(-12deg); }
}

@keyframes aurora-sweep-2 {
  0%   { transform: translate(0, 0) scale(1) rotate(-25deg); }
  33%  { transform: translate(-8%, 15%) scale(1.1) rotate(-18deg); }
  66%  { transform: translate(10%, -10%) scale(0.9) rotate(-30deg); }
  100% { transform: translate(-5%, 5%) scale(1.05) rotate(-22deg); }
}

@keyframes aurora-sweep-3 {
  0%   { transform: translate(0, 0) scale(1) rotate(15deg); }
  33%  { transform: translate(10%, -15%) scale(1.05) rotate(22deg); }
  66%  { transform: translate(-10%, 10%) scale(0.95) rotate(10deg); }
  100% { transform: translate(5%, -5%) scale(1.1) rotate(18deg); }
}

@keyframes aurora-sweep-4 {
  0%   { transform: translate(0, 0) scale(1) rotate(-10deg); }
  33%  { transform: translate(12%, 5%) scale(1.1) rotate(-5deg); }
  66%  { transform: translate(-8%, -15%) scale(0.9) rotate(-15deg); }
  100% { transform: translate(15%, 10%) scale(1.05) rotate(-8deg); }
}

@keyframes aurora-sweep-5 {
  0%   { transform: translate(0, 0) scale(1) rotate(25deg); }
  33%  { transform: translate(-5%, -12%) scale(0.95) rotate(18deg); }
  66%  { transform: translate(10%, 15%) scale(1.1) rotate(30deg); }
  100% { transform: translate(-10%, -8%) scale(1) rotate(20deg); }
}

/* Subtle noise texture */
.noise-overlay {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  /* Slight animation to make noise feel alive */
  animation: noise-shift 2s steps(4) infinite;
}

@keyframes noise-shift {
  0% { transform: translate(0, 0); }
  25% { transform: translate(1%, -1%); }
  50% { transform: translate(-1%, 1%); }
  75% { transform: translate(1%, 1%); }
  100% { transform: translate(0, 0); }
}
</style>
