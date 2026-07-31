<template>
  <span 
    :class="[props.class, 'inline-block select-none font-mono transition-colors duration-300']"
    @mouseenter="triggerManualScramble"
  >
    <span 
      v-for="(char, index) in displayText" 
      :key="index"
      :class="{
        'text-red-500 font-semibold opacity-90 drop-shadow-[0_0_10px_rgba(239,68,68,0.85)]': isScrambled(index),
        'text-white': !isScrambled(index)
      }"
      class="transition-all duration-150 inline-block"
    >
      {{ char }}
    </span>
  </span>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  text?: string
  interval?: number       // Pause time in ms after decryption before next scramble (3000ms = 3s)
  scrambleSpeed?: number  // Delay in ms per animation tick (slow readable pacing)
  class?: string
  characters?: string
}>(), {
  text: 'Igrris',
  interval: 3000,
  scrambleSpeed: 70,
  class: '',
  characters: '!@#$%^&*()_+-=[]{}|;:,.<>?/~0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
})

const displayText = ref<string[]>(props.text.split(''))
const revealedIndices = ref<Set<number>>(new Set(props.text.split('').map((_, i) => i)))

let animationTimer: ReturnType<typeof setInterval> | null = null
let loopTimeout: ReturnType<typeof setTimeout> | null = null
let isAnimating = false

const isScrambled = (index: number) => !revealedIndices.value.has(index)

function getRandomChar(): string {
  const chars = props.characters
  return chars[Math.floor(Math.random() * chars.length)]
}

function startScrambleAnimation() {
  if (isAnimating) return
  isAnimating = true

  const targetChars = props.text.split('')
  const length = targetChars.length
  
  if (animationTimer) clearInterval(animationTimer)
  if (loopTimeout) clearTimeout(loopTimeout)

  revealedIndices.value.clear()
  
  let currentStep = 0
  const stepsPerChar = 3
  const maxSteps = length * stepsPerChar

  animationTimer = setInterval(() => {
    const revealCount = Math.floor((currentStep / maxSteps) * length)
    
    const newRevealed = new Set<number>()
    for (let i = 0; i < revealCount; i++) {
      newRevealed.add(i)
    }
    revealedIndices.value = newRevealed

    displayText.value = targetChars.map((char, index) => {
      if (char === ' ') return ' '
      if (newRevealed.has(index)) {
        return char
      }
      return getRandomChar()
    })

    currentStep++

    if (currentStep > maxSteps) {
      // Completed - return to original name style
      revealedIndices.value = new Set(targetChars.map((_, i) => i))
      displayText.value = [...targetChars]
      
      if (animationTimer) {
        clearInterval(animationTimer)
        animationTimer = null
      }
      isAnimating = false

      // Loop after interval (every 3 seconds later)
      loopTimeout = setTimeout(() => {
        startScrambleAnimation()
      }, props.interval)
    }
  }, props.scrambleSpeed)
}

function triggerManualScramble() {
  if (!isAnimating) {
    if (loopTimeout) clearTimeout(loopTimeout)
    startScrambleAnimation()
  }
}

onMounted(() => {
  // Initial delay before first scramble loop
  loopTimeout = setTimeout(() => {
    startScrambleAnimation()
  }, 1500)
})

onUnmounted(() => {
  if (animationTimer) clearInterval(animationTimer)
  if (loopTimeout) clearTimeout(loopTimeout)
})
</script>
