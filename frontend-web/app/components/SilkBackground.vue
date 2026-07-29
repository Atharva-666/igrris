<template>
  <div class="relative min-h-screen overflow-hidden" :style="{ background: '#000' }">
    <!-- Silk Background Canvas -->
    <canvas
      ref="canvasRef"
      class="absolute inset-0 w-full h-full pointer-events-none"
      aria-hidden="true"
    ></canvas>
    <!-- Slot -->
    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  speed?: number
  scale?: number
  noiseIntensity?: number
  rotation?: number
  color?: string // hex like '#7b2ff7'
}

const props = withDefaults(defineProps<Props>(), {
  speed: 5,
  scale: 1,
  noiseIntensity: 1.5,
  rotation: 0,
  color: '#7b2ff7',
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let gl: WebGLRenderingContext | null = null
let program: WebGLProgram | null = null
let rafId: number
const t0 = performance.now()

// Convert hex color to normalized rgb
function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace('#', '')
  const r = parseInt(h.substring(0, 2), 16) / 255
  const g = parseInt(h.substring(2, 4), 16) / 255
  const b = parseInt(h.substring(4, 6), 16) / 255
  return [r, g, b]
}

// ── Silk shader (adapted from ShaderToy X3yXRd by Giorgi Azmaipharashvili, MIT) ──
const VERT = `
  attribute vec2 a_pos;
  void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }
`

const FRAG = `
  precision highp float;
  uniform float u_time;
  uniform vec2  u_resolution;
  uniform float u_speed;
  uniform float u_scale;
  uniform float u_noiseIntensity;
  uniform float u_rotation;
  uniform vec3  u_color;

  #define PI 3.14159265358979

  float noise(vec2 p) {
    return smoothstep(-0.5, 0.9, sin((p.x - p.y) * 555.0) * sin(p.y * 1444.0)) - 0.4;
  }

  mat2 rotate2D(float angle) {
    float s = sin(angle), c = cos(angle);
    return mat2(c, -s, s, c);
  }

  void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    // Center
    uv -= 0.5;
    // Correct aspect
    uv.x *= u_resolution.x / u_resolution.y;

    // Apply rotation
    uv = rotate2D(u_rotation) * uv;

    // Scale
    uv *= u_scale;

    float t = u_time * u_speed * 0.0001;

    float pattern = 0.0;
    float amplitude = 1.0;
    vec2 p = uv;

    // 6 layers of warped noise for the silk fabric effect
    for (int i = 0; i < 6; i++) {
      p += vec2(
        noise(p * 2.0 + vec2(t, -t)),
        noise(p * 2.0 + vec2(-t, t))
      ) * u_noiseIntensity * 0.15;
      pattern += noise(p) * amplitude;
      amplitude *= 0.55;
      p *= 2.0;
    }

    pattern = clamp(pattern, -1.0, 1.0);

    // Map pattern to colour
    // Silk uses the color as a tint with dark-to-bright range
    vec3 dark  = u_color * 0.05;
    vec3 mid   = u_color * 0.5;
    vec3 light = mix(u_color, vec3(1.0), 0.6);

    float t01 = (pattern + 1.0) * 0.5; // 0..1
    vec3 col = mix(dark, mid, smoothstep(0.0, 0.5, t01));
    col      = mix(col, light, smoothstep(0.5, 1.0, t01));

    gl_FragColor = vec4(col, 1.0);
  }
`

function compile(g: WebGLRenderingContext, type: number, src: string): WebGLShader | null {
  const s = g.createShader(type)!
  g.shaderSource(s, src)
  g.compileShader(s)
  if (!g.getShaderParameter(s, g.COMPILE_STATUS)) { console.error(g.getShaderInfoLog(s)); return null }
  return s
}

function initGL() {
  if (!canvasRef.value) return
  gl = canvasRef.value.getContext('webgl', { alpha: false, antialias: false })
  if (!gl) return

  const vs = compile(gl, gl.VERTEX_SHADER, VERT)
  const fs = compile(gl, gl.FRAGMENT_SHADER, FRAG)
  program = gl.createProgram()!
  gl.attachShader(program, vs!); gl.attachShader(program, fs!)
  gl.linkProgram(program)
  gl.useProgram(program)

  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]), gl.STATIC_DRAW)
  const loc = gl.getAttribLocation(program, 'a_pos')
  gl.enableVertexAttribArray(loc)
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)

  const uTime   = gl.getUniformLocation(program, 'u_time')
  const uRes    = gl.getUniformLocation(program, 'u_resolution')
  const uSpeed  = gl.getUniformLocation(program, 'u_speed')
  const uScale  = gl.getUniformLocation(program, 'u_scale')
  const uNoise  = gl.getUniformLocation(program, 'u_noiseIntensity')
  const uRot    = gl.getUniformLocation(program, 'u_rotation')
  const uColor  = gl.getUniformLocation(program, 'u_color')

  const loop = () => {
    if (!gl || !canvasRef.value) return
    const dpr = Math.min(devicePixelRatio || 1, 2)
    const w = Math.floor(canvasRef.value.clientWidth * dpr)
    const h = Math.floor(canvasRef.value.clientHeight * dpr)
    if (canvasRef.value.width !== w || canvasRef.value.height !== h) {
      canvasRef.value.width = w; canvasRef.value.height = h
      gl.viewport(0, 0, w, h)
    }
    const now = performance.now() - t0
    const [r, g_, b] = hexToRgb(props.color)
    gl.uniform1f(uTime, now)
    gl.uniform2f(uRes, w, h)
    gl.uniform1f(uSpeed, props.speed)
    gl.uniform1f(uScale, props.scale)
    gl.uniform1f(uNoise, props.noiseIntensity)
    gl.uniform1f(uRot, props.rotation)
    gl.uniform3f(uColor, r, g_, b)
    gl.drawArrays(gl.TRIANGLES, 0, 6)
    rafId = requestAnimationFrame(loop)
  }
  loop()
}

onMounted(() => initGL())
onUnmounted(() => {
  cancelAnimationFrame(rafId)
  gl?.getExtension('WEBGL_lose_context')?.loseContext()
})
</script>
