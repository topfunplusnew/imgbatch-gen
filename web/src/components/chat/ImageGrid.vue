<template>
  <div class="grid grid-cols-2 gap-3 mb-4">
    <ImageCard
        v-for="(img, index) in images"
        :key="index"
        :imageUrl="img.url"
        :altText="img.alt"
    />
  </div>
  <div class="flex items-center gap-4">
    <button class="text-slate-400 hover:text-primary transition-colors flex items-center gap-1.5 text-sm">
      <span class="material-symbols-outlined !text-lg">thumb_up</span> 有帮助
    </button>
    <button class="text-slate-400 hover:text-red-400 transition-colors flex items-center gap-1.5 text-sm">
      <span class="material-symbols-outlined !text-lg">thumb_down</span>
    </button>
    <button class="text-slate-400 hover:text-primary transition-colors flex items-center gap-1.5 text-sm ml-auto">
      <span class="material-symbols-outlined !text-lg">refresh</span> 重新生成
    </button>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import ImageCard from './ImageCard.vue'; // 引入 ImageCard 组件

defineProps({
  images: {
    type: Array,
    required: true,
  },
});
</script>