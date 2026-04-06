<template>
  <div class="chat-history-sidebar">
    <!-- 顶部操作区 -->
    <div class="sidebar-header">
      <button
        class="new-chat-btn"
        :disabled="generatorStore.isStartingNewConversation"
        @click="startNewConversation"
      >
        <span class="material-symbols-outlined !text-lg">add</span>
        <span>{{ generatorStore.isStartingNewConversation ? '创建中...' : '新对话' }}</span>
      </button>
      <button class="icon-btn" title="收起侧边栏" @click="$emit('collapse')">
        <span class="material-symbols-outlined !text-xl">menu_open</span>
      </button>
    </div>

    <!-- 搜索框 -->
    <div class="sidebar-search">
      <span class="material-symbols-outlined search-icon !text-base">search</span>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索对话..."
        class="search-input"
      >
    </div>

    <!-- 对话列表 -->
    <div class="sidebar-list custom-scrollbar">
      <div v-if="historyStore.isLoading && groupedSessions.length === 0" class="empty-state">
        <div class="spinner"></div>
        <span class="text-xs text-ink-400">加载中...</span>
      </div>

      <div v-else-if="groupedSessions.length === 0" class="empty-state">
        <span class="material-symbols-outlined !text-3xl text-ink-300">chat_bubble_outline</span>
        <span class="text-xs text-ink-400">暂无对话记录</span>
      </div>

      <template v-else>
        <div v-for="group in groupedSessions" :key="group.label" class="session-group">
          <div class="group-label">{{ group.label }}</div>
          <div
            v-for="session in group.sessions"
            :key="session.id"
            class="session-item"
            :class="{ 'session-item--active': session.id === generatorStore.currentSessionId }"
            @click="switchToSession(session)"
          >
            <span class="session-title">{{ session.title || '未命名对话' }}</span>
            <button
              class="session-delete"
              title="删除"
              @click.stop="deleteSession(session.id)"
            >
              <span class="material-symbols-outlined !text-base">delete</span>
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useHistoryStore, type HistorySession } from '@/store/useHistoryStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAppStore } from '@/store/useAppStore'
import { api } from '@/services/api'

defineEmits<{
  collapse: []
}>()

const router = useRouter()
const historyStore = useHistoryStore()
const generatorStore = useGeneratorStore()
const appStore = useAppStore()

const searchQuery = ref('')

// 时间分组逻辑
interface SessionGroup {
  label: string
  sessions: HistorySession[]
}

const groupedSessions = computed<SessionGroup[]>(() => {
  const now = Date.now()
  const todayStart = new Date().setHours(0, 0, 0, 0)
  const yesterdayStart = todayStart - 86400000
  const weekStart = todayStart - 7 * 86400000
  const monthStart = todayStart - 30 * 86400000

  const query = searchQuery.value.trim().toLowerCase()
  let sessions = [...historyStore.sessions].sort(
    (a, b) => (b.updatedAt || b.createdAt) - (a.updatedAt || a.createdAt)
  )

  if (query) {
    sessions = sessions.filter(
      (s) =>
        s.title?.toLowerCase().includes(query) ||
        s.messages?.some((m) => String(m.content || '').toLowerCase().includes(query))
    )
  }

  const groups: Record<string, HistorySession[]> = {
    today: [],
    yesterday: [],
    week: [],
    month: [],
    older: [],
  }

  for (const session of sessions) {
    const ts = session.updatedAt || session.createdAt
    if (ts >= todayStart) groups.today.push(session)
    else if (ts >= yesterdayStart) groups.yesterday.push(session)
    else if (ts >= weekStart) groups.week.push(session)
    else if (ts >= monthStart) groups.month.push(session)
    else groups.older.push(session)
  }

  const labelMap: Record<string, string> = {
    today: '今天',
    yesterday: '昨天',
    week: '最近 7 天',
    month: '最近 30 天',
    older: '更早',
  }

  return Object.entries(groups)
    .filter(([, list]) => list.length > 0)
    .map(([key, list]) => ({ label: labelMap[key], sessions: list }))
})

async function switchToSession(session: HistorySession) {
  if (session.loadedFromServer && (!session.messages || session.messages.length === 0)) {
    const result = await historyStore.loadSessionDetails(session.id)
    if (result) {
      session.messages = result.messages
      session.files = result.files || []
    }
  }

  generatorStore.messages = session.messages.map((m) => ({
    ...m,
    images: m.images ? [...m.images] : [],
    files: m.files ? [...m.files] : [],
  }))
  generatorStore.currentSessionTitle = session.title
  generatorStore.currentSessionId = session.id
  generatorStore.model = session.model
  generatorStore.sessionSavedToHistory = true
  generatorStore.prompt = ''
  generatorStore.clearAttachments()

  appStore.setSelectedCreation(null)
  appStore.clearSelectedCase()
  appStore.setCurrentView('chat')

  // 如果不在首页，导航到首页显示聊天
  if (router.currentRoute.value.path !== '/') {
    router.push('/')
  }
}

async function deleteSession(sessionId: string) {
  if (!confirm('确定要删除这条对话吗？')) return
  try {
    await api.deleteConversationHistory(sessionId)
    historyStore.deleteSession(sessionId)
  } catch (error) {
    console.error('删除对话失败:', error)
  }
}

async function startNewConversation() {
  router.push('/')
  appStore.setCurrentView('chat')
  await generatorStore.startNewConversation()
}

onMounted(() => {
  historyStore.loadFromServer()
})
</script>

<style scoped>
.chat-history-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f9fafb;
  border-right: 1px solid rgba(15, 23, 42, 0.08);
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.new-chat-btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: white;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(15, 23, 42, 0.78);
  cursor: pointer;
  transition: all 150ms ease;
}

.new-chat-btn:hover {
  background: rgba(15, 23, 42, 0.04);
  border-color: rgba(15, 23, 42, 0.2);
}

.new-chat-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  border: none;
  background: transparent;
  color: rgba(15, 23, 42, 0.5);
  cursor: pointer;
  transition: all 150ms ease;
}

.icon-btn:hover {
  background: rgba(15, 23, 42, 0.06);
  color: rgba(15, 23, 42, 0.8);
}

.sidebar-search {
  position: relative;
  padding: 0.5rem 0.75rem;
}

.search-icon {
  position: absolute;
  left: 1.15rem;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(15, 23, 42, 0.35);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.45rem 0.6rem 0.45rem 2rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: white;
  font-size: 0.78rem;
  color: rgba(15, 23, 42, 0.85);
  outline: none;
  transition: border-color 150ms ease;
}

.search-input::placeholder {
  color: rgba(15, 23, 42, 0.35);
}

.search-input:focus {
  border-color: rgba(15, 23, 42, 0.25);
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.25rem 0.5rem 1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 3rem 1rem;
}

.spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid rgba(15, 23, 42, 0.1);
  border-top-color: rgba(15, 23, 42, 0.6);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.session-group {
  margin-bottom: 0.25rem;
}

.group-label {
  padding: 0.6rem 0.5rem 0.3rem;
  font-size: 0.68rem;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  user-select: none;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 120ms ease;
  position: relative;
}

.session-item:hover {
  background: rgba(15, 23, 42, 0.05);
}

.session-item--active {
  background: rgba(15, 23, 42, 0.08);
}

.session-item--active:hover {
  background: rgba(15, 23, 42, 0.1);
}

.session-title {
  flex: 1;
  min-width: 0;
  font-size: 0.82rem;
  color: rgba(15, 23, 42, 0.78);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.session-item--active .session-title {
  color: rgba(15, 23, 42, 0.92);
  font-weight: 500;
}

.session-delete {
  display: none;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 0.35rem;
  border: none;
  background: transparent;
  color: rgba(15, 23, 42, 0.35);
  cursor: pointer;
  transition: all 120ms ease;
}

.session-item:hover .session-delete {
  display: flex;
}

.session-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* Scrollbar */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(15, 23, 42, 0.12) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.12);
  border-radius: 999px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(15, 23, 42, 0.22);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
