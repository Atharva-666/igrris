<template>
  <div :class="['relative min-h-screen w-full overflow-hidden flex flex-col', containerClass]">
    <canvas 
      class="absolute inset-0 z-0 w-full h-full pointer-events-none"
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
  waveWidth: 50,
  blur: 10,
  speed: 'fast',
  waveOpacity: 0.5,
  backgroundFill: 'black',
  // Default to a sleek white/grey monochrome palette based on the user's previous request
  colors: () => ['#ffffff', '#e5e5e5', '#a3a3a3', '#737373', '#d4d4d4'],
});

const canvasRef = ref<HTMLCanvasElement | null>(null);
let ctx: CanvasRenderingContext2D | null = null;
let animationId: number;
let time = 0;

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
  
  // Update time based on speed
  time += props.speed === 'fast' ? 0.002 : 0.001;
  
  // Draw each color line
  for (let i = 0; i < props.colors.length; i++) {
    ctx.beginPath();
    ctx.lineWidth = props.waveWidth;
    ctx.strokeStyle = props.colors[i % props.colors.length];
    
    // Draw the wavy line across the screen
    for (let x = 0; x <= w; x += 5) {
      // Use layered sine/cosine for an organic, non-repeating noise-like wave
      const n = Math.sin(x * 0.002 + time + i) * Math.cos(x * 0.001 - time * 0.5 + i * 0.5);
      const y = n * h * 0.3 + (h * 0.5);
      
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
