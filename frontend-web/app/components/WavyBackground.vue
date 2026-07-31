<template>
  <div :class="['relative min-h-screen w-full overflow-hidden flex flex-col', containerClass]">
    <canvas 
      class="fixed inset-0 z-0 w-full h-full pointer-events-none"
      id="canvas"
      ref="canvasRef"
      :style="{ filter: `blur(${blur}px)` }"
    ></canvas>
    <div :class="['relative z-10 flex-1 flex flex-col', $props.class]" v-bind="$attrs">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

interface Props {
  waveWidth?: number;
  blur?: number;
  speed?: 'slow' | 'fast';
  waveOpacity?: number;
  backgroundFill?: string;
  colors?: string[];
  containerClass?: string;
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  waveWidth: 100,
  blur: 23,
  speed: 'fast',
  waveOpacity: 0.45,
  backgroundFill: 'black',
  // Default to a sleek white/grey monochrome palette based on the user's previous request
  colors: () => ['#ffffff', '#e5e5e5', '#a3a3a3', '#737373', '#d4d4d4'],
});

const canvasRef = ref<HTMLCanvasElement | null>(null);
let ctx: CanvasRenderingContext2D | null = null;
let animationId: number;
let time = 0;

// Scroll state for scroll-driven animation
let scrollY = 0;
let targetScrollY = 0;

const handleScroll = () => {
  targetScrollY = window.scrollY || window.pageYOffset || 0;
};

const initCanvas = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  
  ctx = canvas.getContext('2d');
  if (!ctx) return;
  
  const resize = () => {
    // Handle high DPI displays for crisp rendering
    const dpr = window.devicePixelRatio || 1;
    canvas.width = window.innerWidth * dpr;
    canvas.height = window.innerHeight * dpr;
    ctx?.scale(dpr, dpr);
  };
  
  window.addEventListener('resize', resize);
  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();
  resize();
  draw();
};

const draw = () => {
  if (!ctx || !canvasRef.value) return;
  
  const w = window.innerWidth;
  const h = window.innerHeight;
  
  ctx.fillStyle = props.backgroundFill;
  ctx.fillRect(0, 0, w, h);
  
  ctx.globalAlpha = props.waveOpacity;
  
  // Smooth scroll interpolation (lerp)
  scrollY += (targetScrollY - scrollY) * 0.08;
  
  // Update time based on speed
  time += props.speed === 'fast' ? 0.002 : 0.001;
  
  // Scroll-driven phase shift & bounded Y parallax offset
  const scrollPhase = scrollY * 0.0015;
  // Bounded sinusoidal Y-parallax keeps waves gracefully centered around middle viewport at all scroll depths
  const scrollYParallax = Math.sin(scrollY * 0.0008) * (h * 0.12);
  
  // Draw each color line with independent frequencies, scattered placement, and scroll movement
  const totalColors = props.colors.length;
  for (let i = 0; i < totalColors; i++) {
    ctx.beginPath();
    ctx.lineWidth = props.waveWidth;
    ctx.strokeStyle = props.colors[i % totalColors];
    
    // Distinct per-line frequencies & phase for scattered crossover effect
    const freq1 = 0.0012 + i * 0.0004;
    const freq2 = 0.0022 - i * 0.0003;
    const phase = i * 1.5;
    
    // Spread center Y for each line and apply bounded vertical scroll parallax
    const lineParallax = scrollYParallax * (0.8 + i * 0.1);
    const centerY = (h * 0.5 + (i - (totalColors - 1) / 2) * (h * 0.1)) - lineParallax;
    
    // Expanded vertical height amplitude to match tall screen span
    const amp = h * 0.28;
    
    for (let x = 0; x <= w; x += 5) {
      // Wave shapes morph dynamically with scroll position and time
      const n = Math.sin(x * freq1 + time * (1 + i * 0.1) + phase + scrollPhase * (1 + i * 0.2)) + 
                0.4 * Math.cos(x * freq2 - time * 0.5 + phase * 0.7 - scrollPhase * 0.5);
      const y = centerY + n * amp;
      
      if (x === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
  }
  
  ctx.globalAlpha = 1.0; // Reset alpha
  animationId = requestAnimationFrame(draw);
};

onMounted(() => {
  initCanvas();
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
  if (animationId) {
    cancelAnimationFrame(animationId);
  }
});
</script>

<style scoped>
/* Ensure canvas does not block scroll/clicks */
canvas {
  pointer-events: none;
}
</style>
