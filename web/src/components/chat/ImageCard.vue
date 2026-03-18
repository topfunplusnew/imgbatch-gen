<template>
  <div class="relative group rounded-xl overflow-hidden aspect-[4/3] bg-surface-dark border border-border-dark">
    <img :src="imageUrl" :alt="altText" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />

    <!-- 悬浮操作栏 -->
    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
      <button class="p-2 bg-white/20 backdrop-blur-md rounded-lg hover:bg-white/40 text-white">
        <span class="material-symbols-outlined">download</span>
      </button>
      <button class="p-2 bg-white/20 backdrop-blur-md rounded-lg hover:bg-white/40 text-white">
        <span class="material-symbols-outlined">zoom_in</span>
      </button>
      <button class="p-2 bg-white/20 backdrop-blur-md rounded-lg hover:bg-white/40 text-white">
        <span class="material-symbols-outlined">brush</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';

defineProps({
  imageUrl: {
    type: String,
    required: true,
  },
  altText: {
    type: String,
    default: 'Generated image',
  },
});
</script>