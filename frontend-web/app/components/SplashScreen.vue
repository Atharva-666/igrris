<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="splash-container fixed inset-0 z-[999999] overflow-hidden bg-black select-none"
      :class="hiding ? 'splash-container--hiding pointer-events-none' : 'pointer-events-auto'"
      :aria-hidden="showSoundPrompt ? 'false' : 'true'"
    >
      <video
        ref="videoRef"
        class="splash-video"
        :class="{ 'splash-video--idle': showSoundPrompt }"
        src="/Igrris.mp4"
        playsinline
        preload="auto"
        disablePictureInPicture
        @ended="finishSplash"
        @error="finishSplash"
      />

      <Transition name="sound-prompt">
        <div
          v-if="showSoundPrompt"
          class="sound-prompt absolute inset-0 z-10 flex items-center justify-center bg-black/85 backdrop-blur-sm px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="splash-sound-title"
          aria-describedby="splash-sound-desc"
        >
          <div class="sound-prompt-card max-w-md w-full rounded-2xl border border-surface-700/80 bg-surface-950/95 p-6 sm:p-8 text-center shadow-2xl">
            <div class="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-brand-500/15 border border-brand-500/30">
              <svg class="h-7 w-7 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.536 8.464a5 5 0 010 7.072M18.364 5.636a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
            </div>
            <h2 id="splash-sound-title" class="text-lg sm:text-xl font-bold text-white mb-2">
              Enable sound?
            </h2>
            <p id="splash-sound-desc" class="text-sm text-surface-400 mb-6 leading-relaxed">
              Intro video includes audio. Browsers need your choice before playback with sound.
            </p>
            <div class="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                type="button"
                class="sound-btn sound-btn--primary"
                @click="startWithSound"
              >
                Enable sound
              </button>
              <button
                type="button"
                class="sound-btn sound-btn--secondary"
                @click="startMuted"
              >
                Continue muted
              </button>
            </div>
          </div>
        </div>
      </Transition>

      <div
        v-if="needsTapForSound"
        class="absolute inset-x-0 bottom-8 z-10 flex justify-center px-4 pointer-events-none"
      >
        <p class="rounded-full bg-black/70 border border-surface-600/80 px-4 py-2 text-sm text-surface-200 backdrop-blur-sm">
          Tap anywhere to play intro with sound
        </p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'

const SPLASH_SOUND_KEY = 'igrris-splash-sound'
const SPLASH_SOUND_GRANTED = 'granted'

const emit = defineEmits<{
  complete: []
}>()

const visible = ref(true)
const hiding = ref(false)
const showSoundPrompt = ref(false)
const needsTapForSound = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
let finished = false
let removeTapListener: (() => void) | null = null

function isSoundPermanentlyAllowed(): boolean {
  if (!import.meta.client) return false
  try {
    return localStorage.getItem(SPLASH_SOUND_KEY) === SPLASH_SOUND_GRANTED
  } catch {
    return false
  }
}

function rememberSoundAllowed() {
  if (!import.meta.client) return
  try {
    localStorage.setItem(SPLASH_SOUND_KEY, SPLASH_SOUND_GRANTED)
  } catch {
    /* localStorage unavailable */
  }
}

function clearTapListener() {
  removeTapListener?.()
  removeTapListener = null
}

function finishSplash() {
  if (finished) return
  finished = true
  clearTapListener()
  needsTapForSound.value = false
  showSoundPrompt.value = false

  hiding.value = true
  window.setTimeout(() => {
    visible.value = false
    emit('complete')
  }, 700)
}

async function waitForVideoReady(video: HTMLVideoElement) {
  if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) return
  await new Promise<void>((resolve) => {
    const onReady = () => {
      video.removeEventListener('canplay', onReady)
      resolve()
    }
    video.addEventListener('canplay', onReady, { once: true })
  })
}

function bindTapToPlayWithSound() {
  clearTapListener()

  const handler = () => {
    clearTapListener()
    needsTapForSound.value = false
    void playVideo(true)
  }

  document.addEventListener('pointerdown', handler, { capture: true, once: true })
  removeTapListener = () => {
    document.removeEventListener('pointerdown', handler, true)
  }
}

async function playVideo(withSound: boolean) {
  const video = videoRef.value
  if (!video || finished) return

  showSoundPrompt.value = false
  needsTapForSound.value = false
  clearTapListener()

  video.muted = !withSound
  video.volume = withSound ? 1 : 0
  video.currentTime = 0

  try {
    await video.play()
  } catch {
    if (withSound) {
      video.pause()
      if (isSoundPermanentlyAllowed()) {
        needsTapForSound.value = true
        bindTapToPlayWithSound()
        return
      }
      finishSplash()
      return
    }
    finishSplash()
  }
}

function startWithSound() {
  rememberSoundAllowed()
  showSoundPrompt.value = false
  void playVideo(true)
}

function startMuted() {
  showSoundPrompt.value = false
  void playVideo(false)
}

onMounted(async () => {
  if (!import.meta.client) return
  document.documentElement.style.backgroundColor = '#000000'

  await nextTick()
  const video = videoRef.value
  if (!video) {
    finishSplash()
    return
  }

  try {
    await waitForVideoReady(video)
  } catch {
    finishSplash()
    return
  }

  if (isSoundPermanentlyAllowed()) {
    await playVideo(true)
    return
  }

  showSoundPrompt.value = true
})

onBeforeUnmount(() => {
  clearTapListener()
})
</script>

<style scoped>
.splash-container {
  background-color: #000000 !important;
  color-scheme: dark !important;
  opacity: 1;
  transition: opacity 700ms ease-out;
}

.splash-container--hiding {
  opacity: 0;
}

.splash-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.splash-video--idle {
  visibility: hidden;
}

.sound-btn {
  @apply rounded-full px-5 py-2.5 text-sm font-semibold transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-950;
}

.sound-btn--primary {
  @apply bg-brand-600 text-white hover:bg-brand-500 border border-brand-500/50;
}

.sound-btn--secondary {
  @apply bg-surface-800/80 text-surface-200 hover:bg-surface-700 border border-surface-600/80;
}

.sound-prompt-enter-active,
.sound-prompt-leave-active {
  transition: opacity 300ms ease;
}

.sound-prompt-enter-from,
.sound-prompt-leave-to {
  opacity: 0;
}
</style>
