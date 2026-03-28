<template>
  <div class="flex flex-col h-full bg-transparent">
    <div class="px-4 py-3 border-b border-border-dark flex items-center justify-between gap-3">
      <h3 class="text-sm font-bold text-slate-400 uppercase tracking-wider">历史记录</h3>
      <button
        @click="startNewConversation"
        :disabled="generatorStore.isStartingNewConversation"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg bg-primary-strong text-white hover:bg-primary-deep shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="开启新对话"
      >
        <span class="material-symbols-outlined !text-base">
          {{ generatorStore.isStartingNewConversation ? 'hourglass_empty' : 'add' }}
        </span>
        <span>{{ generatorStore.isStartingNewConversation ? '开启中...' : '新对话' }}</span>
      </button>
    </div>

    <div class="px-4 py-3 border-b border-border-dark space-y-2">
      <div class="flex items-center justify-between">
        <div class="relative flex-1">
          <span class="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-ink-500 !text-sm">search</span>
          <input
            v-model="historyStore.searchQuery"
            @input="historyStore.setSearchQuery($event.target.value)"
            type="text"
            placeholder="搜索会话..."
            class="w-full bg-white border border-border-dark rounded-lg pl-8 pr-3 py-2 text-xs focus:ring-1 focus:ring-primary focus:border-primary"
          >
        </div>
        <button
          @click="refreshHistory"
          class="ml-2 px-2 py-2 bg-white border border-border-dark rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-colors"
        >
          <span class="material-symbols-outlined text-ink-500 !text-sm">refresh</span>
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar px-4 py-3">
      <div class="space-y-2">
        <div
          v-for="session in historyStore.filteredSessions"
          :key="session.id"
          class="bg-white border border-border-dark rounded-lg p-3 hover:border-primary/50 transition-colors cursor-pointer shadow-lg"
          @click="viewSession(session)"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-semibold mb-1 truncate">{{ session.title }}</h3>
              <div class="flex items-center gap-2 text-[10px] text-ink-500">
                <span class="flex items-center gap-0.5">
                  <span class="material-symbols-outlined !text-xs">schedule</span>
                  {{ formatDateShort(session.createdAt) }}
                </span>
                <span class="flex items-center gap-0.5">
                  <span class="material-symbols-outlined !text-xs">image</span>
                  {{ session.imageCount }}
                </span>
              </div>
            </div>
            <button
              @click.stop="deleteSession(session.id)"
              class="ml-2 p-1 text-ink-500 hover:text-red-400 hover:bg-red-400/10 rounded transition-colors shrink-0"
            >
              <span class="material-symbols-outlined !text-sm">delete</span>
            </button>
          </div>
        </div>

        <div v-if="historyStore.filteredSessions.length === 0" class="text-center py-8 text-ink-500">
          <span class="material-symbols-outlined !text-4xl mb-2 block">history</span>
          <p class="text-xs">暂无历史记录</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useHistoryStore } from '@/store/useHistoryStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAppStore } from '@/store/useAppStore'
import { api } from '@/services/api'

const historyStore = useHistoryStore()
const generatorStore = useGeneratorStore()
const appStore = useAppStore()

onMounted(() => {
  historyStore.loadFromServer()
})

let refreshTimeout = null
watch(() => generatorStore.currentSessionId, (newSessionId, oldSessionId) => {
  if (refreshTimeout) {
    clearTimeout(refreshTimeout)
  }

  if (newSessionId && newSessionId !== oldSessionId) {
    refreshTimeout = setTimeout(() => {
      historyStore.refresh()
      refreshTimeout = null
    }, 2000)
  }
})

const formatDateShort = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  }
}

const refreshHistory = async () => {
  await historyStore.refresh()
}

const startNewConversation = async () => {
  appStore.setCurrentPage('agent')
  await generatorStore.startNewConversation()
}

const viewSession = async (session) => {
  if (session.loadedFromServer && (!session.messages || session.messages.length === 0)) {
    const result = await historyStore.loadSessionDetails(session.id)
    if (result) {
      session.messages = result.messages
      session.files = result.files || []
    }
  }

  generatorStore.messages = [...session.messages]
  generatorStore.currentSessionTitle = session.title
  generatorStore.currentSessionId = session.id
  generatorStore.model = session.model
  generatorStore.sessionSavedToHistory = true
  appStore.setCurrentView('chat')

  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const deleteSession = async (sessionId) => {
  if (confirm('确定要删除这个会话吗？')) {
    try {
      await api.deleteConversationHistory(sessionId)
    } catch (error) {
      console.warn('删除服务器记录失败:', error)
    }

    historyStore.deleteSession(sessionId)
  }
}
</script>
