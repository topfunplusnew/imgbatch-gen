<template>
  <header class="h-14 md:h-16 border-b border-border-dark flex items-center justify-between px-4 md:px-8 bg-white/80 backdrop-blur-xl sticky top-0 z-10">
    <div class="flex items-center gap-2 md:gap-4 min-w-0">
      <div class="hidden md:flex items-center gap-2 min-w-0">
        <span class="text-sm font-medium text-slate-500 shrink-0">当前会话:</span>
        <span class="text-sm font-semibold truncate">{{ generatorStore.currentSessionTitle }}</span>
      </div>

      <button
        @click="$emit('openModelSelector')"
        class="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg border border-border-dark bg-white/90 hover:bg-primary/5 text-ink-950 shrink-0"
      >
        <span class="material-symbols-outlined !text-lg text-primary">auto_awesome</span>
        <span class="max-w-[120px] md:max-w-none truncate">{{ currentModelDisplay }}</span>
        <span class="material-symbols-outlined !text-lg text-ink-500">expand_more</span>
      </button>
    </div>

    <div class="flex items-center gap-2 md:gap-4">
      <button
        @click="$emit('toggleSettings')"
        class="lg:hidden flex items-center justify-center p-1.5 rounded-lg border border-border-dark bg-white/90 hover:bg-primary/5 text-ink-700"
      >
        <span class="material-symbols-outlined !text-xl">tune</span>
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const generatorStore = useGeneratorStore()

defineEmits(['openModelSelector', 'toggleSettings'])

const currentModelDisplay = computed(() => {
  return generatorStore.selectedModelInfo?.model_name || generatorStore.model || '选择模型'
})
</script>
