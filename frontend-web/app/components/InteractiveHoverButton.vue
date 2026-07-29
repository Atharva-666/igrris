<template>
  <button
    class="group relative cursor-pointer overflow-hidden rounded-full border border-surface-800 bg-surface-950 px-2 py-1 text-center font-semibold text-white transition-all duration-300 hover:border-transparent hover:bg-surface-900 disabled:opacity-50 disabled:cursor-not-allowed"
    :class="$props.class"
    v-bind="$attrs"
  >
    <!-- Background expansion circle on hover -->
    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div 
        class="h-8 w-8 translate-x-[-150%] rounded-full bg-white opacity-0 transition-all duration-500 ease-out group-hover:w-full group-hover:h-full group-hover:translate-x-0 group-hover:rounded-none group-hover:opacity-100" 
        :class="bgClass"
      />
    </div>
    
    <!-- Content container -->
    <div class="relative flex items-center justify-center gap-2 px-4 py-1.5 transition-colors duration-300 group-hover:text-black" :class="textHoverClass">
      <span class="transition-transform duration-300 group-hover:-translate-x-1 flex items-center gap-2">
        <slot>{{ text }}</slot>
      </span>
      <!-- Arrow icon -->
      <svg class="h-4 w-4 absolute right-4 opacity-0 transition-all duration-300 translate-x-2 group-hover:opacity-100 group-hover:translate-x-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
      </svg>
    </div>
  </button>
</template>

<script setup lang="ts">
interface Props {
  text?: string;
  class?: string;
  bgClass?: string;
  textHoverClass?: string;
}

withDefaults(defineProps<Props>(), {
  text: "Button",
  bgClass: "bg-white",
  textHoverClass: "group-hover:text-black",
});
</script>
