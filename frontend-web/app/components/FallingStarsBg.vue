<template>
  <div ref="containerRef" :class="['relative overflow-hidden w-full h-full', props.class]">
    <canvas ref="canvasRef" class="absolute inset-0 pointer-events-none w-full h-full"></canvas>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  color?: string
  count?: number
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  color: '#ffffff',
  count: 80,
  class: '',
})

const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

let animationFrameId: number | null = null

interface Star {
  x: number
  y: number
  length: number
  speed: number
  opacity: number
  dx: number
  dy: number
  size: number
}

let stars: Star[] = []

function createStars(width: number, height: number) {
  stars = []
  const angle = (Math.PI / 180) * 45 // 45 degrees falling angle

  for (let i = 0; i < props.count; i++) {
    const speed = Math.random() * 3 + 1.5
    stars.push({
      x: Math.random() * (width + height) - height,
      y: Math.random() * height,
      length: Math.random() * 80 + 20,
      speed: speed,
      opacity: Math.random() * 0.8 + 0.2,
      dx: Math.cos(angle) * speed,
      dy: Math.sin(angle) * speed,
      size: Math.random() * 1.5 + 0.5,
    })
  }
}

function hexToRgb(hex: string) {
  let c = hex.replace('#', '')
  if (c.length === 3) {
    c = c.split('').map(char => char + char).join('')
  }
  const num = parseInt(c, 16)
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255,
  }
}

function render() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const width = canvas.width
  const height = canvas.height

  ctx.clearRect(0, 0, width, height)

  const rgb = hexToRgb(props.color)

  for (let i = 0; i < stars.length; i++) {
    const star = stars[i]

    // Move star
    star.x += star.dx
    star.y += star.dy

    // Reset if out of bounds
    if (star.x > width + 50 || star.y > height + 50) {
      star.x = Math.random() * (width + height) - height
      star.y = -50
      star.speed = Math.random() * 3 + 1.5
      star.length = Math.random() * 80 + 20
      star.opacity = Math.random() * 0.8 + 0.2
      const angle = (Math.PI / 180) * 45
      star.dx = Math.cos(angle) * star.speed
      star.dy = Math.sin(angle) * star.speed
    }

    // Draw tail gradient
    const tailX = star.x - Math.cos((Math.PI / 180) * 45) * star.length
    const tailY = star.y - Math.sin((Math.PI / 180) * 45) * star.length

    const gradient = ctx.createLinearGradient(tailX, tailY, star.x, star.y)
    gradient.addColorStop(0, `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0)`)
    gradient.addColorStop(1, `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${star.opacity})`)

    ctx.beginPath()
    ctx.moveTo(tailX, tailY)
    ctx.lineTo(star.x, star.y)
    ctx.strokeStyle = gradient
    ctx.lineWidth = star.size
    ctx.lineCap = 'round'
    ctx.stroke()

    // Draw glowing head point
    ctx.beginPath()
    ctx.arc(star.x, star.y, star.size * 0.8, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${star.opacity})`
    ctx.shadowBlur = 8
    ctx.shadowColor = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.8)`
    ctx.fill()
    ctx.shadowBlur = 0
  }

  animationFrameId = requestAnimationFrame(render)
}

function handleResize() {
  const container = containerRef.value
  const canvas = canvasRef.value
  if (!container || !canvas) return

  const rect = container.getBoundingClientRect()
  const w = rect.width || window.innerWidth
  const h = rect.height || window.innerHeight
  canvas.width = w
  canvas.height = h

  createStars(w, h)
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  render()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
  }
})

watch(() => [props.count, props.color], () => {
  if (containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect()
    createStars(rect.width, rect.height)
  }
})
</script>
