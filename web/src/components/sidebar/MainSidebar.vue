<template>
  <aside class="w-56 xl:w-64 flex flex-col border-r border-border-dark bg-white/90 backdrop-blur-xl shrink-0">
    <nav v-if="!hideLogo" class="px-4 pt-4 pb-3 space-y-1 shrink-0">
      <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 px-3">主菜单</div>

      <button
        :class="{
          'bg-white text-primary-strong border border-primary/25 shadow-sm font-medium': activeItem === 'agent',
          'text-ink-700 hover:bg-primary/5': activeItem !== 'agent'
        }"
        @click="setActive('agent')"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors text-left"
      >
        <span class="material-symbols-outlined">smart_toy</span>
        <span>图像工作室</span>
      </button>

      <button
        :class="{
          'bg-white text-primary-strong border border-primary/25 shadow-sm font-medium': activeItem === 'api',
          'text-ink-700 hover:bg-primary/5': activeItem !== 'api'
        }"
        @click="setActive('api')"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors text-left"
      >
        <span class="material-symbols-outlined">api</span>
        <span>API 配置</span>
      </button>

      <button
        :class="{
          'bg-white text-primary-strong border border-primary/25 shadow-sm font-medium': activeItem === 'async-tasks',
          'text-ink-700 hover:bg-primary/5': activeItem !== 'async-tasks'
        }"
        @click="setActive('async-tasks')"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors text-left"
      >
        <span class="material-symbols-outlined">schedule</span>
        <span>异步任务</span>
      </button>
    </nav>

    <div class="flex-1 overflow-hidden border-t border-border-dark">
      <HistoryPanel />
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import HistoryPanel from '../history/HistoryPanel.vue'

defineProps({
  hideLogo: { type: Boolean, default: false }
})

const appStore = useAppStore()
const activeItem = computed(() => appStore.currentPage)

const setActive = (item) => {
  appStore.setCurrentPage(item)
}
</script>
