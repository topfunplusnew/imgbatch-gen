<template>
  <div class="flex h-full flex-col bg-white">
    <div class="flex items-center justify-between border-b border-border-dark px-4 py-3 shrink-0">
      <div class="min-w-0">
        <h3 class="text-base font-bold text-ink-950">历史记录</h3>
        <p class="mt-0.5 text-xs text-ink-500">查看生成历史和对话历史</p>
      </div>
      <button
        type="button"
        class="rounded-lg p-1 text-ink-500 transition-colors hover:bg-gray-100 hover:text-ink-950"
        @click="handleClose"
      >
        <span class="material-symbols-outlined !text-xl">close</span>
      </button>
    </div>

    <div class="border-b border-border-dark px-4 py-3 shrink-0">
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="history-tab"
          :class="{ 'history-tab--active': activeTab === 'generations' }"
          @click="activeTab = 'generations'"
        >
          <span class="material-symbols-outlined !text-lg">image</span>
          <span>生成历史</span>
        </button>
        <button
          type="button"
          class="history-tab"
          :class="{ 'history-tab--active': activeTab === 'conversations' }"
          @click="activeTab = 'conversations'"
        >
          <span class="material-symbols-outlined !text-lg">chat</span>
          <span>对话历史</span>
        </button>
      </div>
    </div>

    <div v-if="activeTab === 'generations'" class="flex min-h-0 flex-1 flex-col">
      <div class="flex items-center justify-between gap-3 border-b border-border-dark px-4 py-3 shrink-0">
        <div class="flex items-center gap-2">
          <select
            v-model="generationStatus"
            class="rounded-lg border border-border-dark bg-white px-3 py-2 text-xs text-ink-700 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            @change="reloadGenerationRecords"
          >
            <option value="">全部状态</option>
            <option value="completed">成功</option>
            <option value="failed">失败</option>
          </select>
          <span class="text-xs text-ink-400">共 {{ generationTotalCount }} 条</span>
        </div>
        <button
          type="button"
          class="inline-flex items-center gap-1 rounded-lg border border-border-dark px-2.5 py-2 text-xs text-ink-600 transition-colors hover:bg-gray-50 hover:text-ink-950"
          @click="reloadGenerationRecords"
        >
          <span class="material-symbols-outlined !text-sm">refresh</span>
          <span>刷新</span>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar px-4 py-4">
        <div v-if="generationLoading && generationRecords.length === 0" class="history-empty-state">
          <div class="history-spinner"></div>
          <p class="text-sm text-ink-500">生成历史加载中...</p>
        </div>

        <div v-else-if="generationRecords.length === 0" class="history-empty-state">
          <span class="material-symbols-outlined !text-5xl text-ink-300">image</span>
          <p class="text-sm text-ink-500">暂无生成记录</p>
          <p class="text-xs text-ink-400">开始创作后，历史会展示在这里</p>
        </div>

        <div v-else class="space-y-3">
          <button
            v-for="record in generationRecords"
            :key="record.id"
            type="button"
            class="generation-item"
            @click="openGenerationRecord(record)"
          >
            <div class="generation-item__thumb">
              <img
                v-if="record.image_urls && record.image_urls.length > 0"
                :src="resolveImageSrc(record.image_urls[0])"
                :alt="record.prompt"
                class="h-full w-full object-cover"
                @error="handleImageFallback"
              >
              <div v-else class="generation-item__thumb-empty">
                <span class="material-symbols-outlined !text-3xl">image</span>
              </div>
            </div>

            <div class="min-w-0 flex-1 text-left">
              <div class="flex flex-wrap items-center gap-2">
                <span class="history-status-pill" :class="statusPillClassMap[record.status]">
                  {{ generationStatusTextMap[record.status] || record.status }}
                </span>
                <span class="history-type-pill">
                  {{ record.type === 'chat' ? '对话生成' : '异步任务' }}
                </span>
                <span class="text-[11px] text-ink-400">{{ formatRelativeTime(record.timestamp || record.created_at) }}</span>
              </div>

              <p class="mt-2 line-clamp-2 text-sm font-medium text-ink-800">
                {{ record.prompt || '无提示词' }}
              </p>

              <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ink-500">
                <span>{{ record.model || '未知模型' }}</span>
                <span v-if="record.image_urls?.length">图片 {{ record.image_urls.length }} 张</span>
                <span v-if="record.provider">{{ record.provider }}</span>
              </div>
            </div>

            <span class="material-symbols-outlined shrink-0 text-ink-300">chevron_right</span>
          </button>
        </div>

        <div v-if="generationHasMore && generationRecords.length > 0" class="mt-4 text-center">
          <button
            type="button"
            class="rounded-lg border border-border-dark px-4 py-2 text-sm text-ink-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="generationLoading"
            @click="loadGenerationRecords()"
          >
            {{ generationLoading ? '加载中...' : '加载更多' }}
          </button>
        </div>
      </div>
    </div>

    <div v-else class="flex min-h-0 flex-1 flex-col md:flex-row">
      <div class="flex min-h-0 flex-1 flex-col border-b border-border-dark md:w-[42%] md:border-b-0 md:border-r">
        <div class="flex items-center gap-2 border-b border-border-dark px-4 py-3 shrink-0">
          <div class="relative min-w-0 flex-1">
            <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-400 !text-sm">search</span>
            <input
              v-model="conversationQuery"
              type="text"
              placeholder="搜索对话标题或内容"
              class="w-full rounded-lg border border-border-dark bg-white py-2 pl-8 pr-3 text-xs text-ink-700 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
          </div>
          <button
            type="button"
            class="inline-flex items-center justify-center rounded-lg border border-border-dark p-2 text-ink-500 transition-colors hover:bg-gray-50 hover:text-ink-950"
            @click="refreshConversations"
          >
            <span class="material-symbols-outlined !text-sm">refresh</span>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar px-4 py-4">
          <div v-if="historyStore.isLoading && filteredConversationSessions.length === 0" class="history-empty-state">
            <div class="history-spinner"></div>
            <p class="text-sm text-ink-500">对话历史加载中...</p>
          </div>

          <div v-else-if="filteredConversationSessions.length === 0" class="history-empty-state">
            <span class="material-symbols-outlined !text-5xl text-ink-300">forum</span>
            <p class="text-sm text-ink-500">暂无对话历史</p>
            <p class="text-xs text-ink-400">发起对话后，可在这里回看历史</p>
          </div>

          <div v-else class="space-y-2">
            <button
              v-for="session in filteredConversationSessions"
              :key="session.id"
              type="button"
              class="conversation-item"
              :class="{ 'conversation-item--active': session.id === selectedConversationId }"
              @click="selectConversation(session.id)"
            >
              <div class="min-w-0 flex-1 text-left">
                <div class="flex items-start justify-between gap-3">
                  <p class="truncate text-sm font-medium text-ink-800">{{ session.title || '未命名对话' }}</p>
                  <span class="shrink-0 text-[11px] text-ink-400">{{ formatRelativeTime(session.updatedAt || session.createdAt) }}</span>
                </div>
                <p class="mt-1 line-clamp-2 text-xs leading-relaxed text-ink-500">
                  {{ getSessionPreview(session) }}
                </p>
                <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ink-400">
                  <span>{{ session.messageCount || session.messages.length || 0 }} 条消息</span>
                  <span v-if="session.imageCount">{{ session.imageCount }} 张图</span>
                  <span v-if="session.totalFiles">{{ session.totalFiles }} 个文件</span>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>

      <div class="flex min-h-0 flex-[1.25] flex-col">
        <div v-if="selectedConversation" class="flex h-full min-h-0 flex-col">
          <div class="border-b border-border-dark px-4 py-4 shrink-0">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="min-w-0">
                <h4 class="truncate text-base font-semibold text-ink-950">{{ selectedConversation.title || '未命名对话' }}</h4>
                <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-500">
                  <span>{{ formatFullTime(selectedConversation.updatedAt || selectedConversation.createdAt) }}</span>
                  <span>{{ selectedConversation.messageCount || selectedConversation.messages.length || 0 }} 条消息</span>
                  <span v-if="selectedConversation.imageCount">{{ selectedConversation.imageCount }} 张图片</span>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="rounded-lg border border-border-dark px-3 py-2 text-sm text-ink-700 transition-colors hover:bg-gray-50"
                  @click="openConversationInChat(selectedConversation.id)"
                >
                  在聊天区打开
                </button>
                <button
                  type="button"
                  class="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-500 transition-colors hover:bg-red-50"
                  @click="removeConversation(selectedConversation.id)"
                >
                  删除
                </button>
              </div>
            </div>
          </div>

          <div class="flex-1 overflow-y-auto custom-scrollbar bg-gray-50/50 px-4 py-4">
            <div class="space-y-3">
              <div
                v-for="message in selectedConversation.messages"
                :key="message.id"
                class="flex"
                :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
              >
                <div
                  class="max-w-[92%] rounded-2xl px-3 py-2.5 shadow-sm"
                  :class="message.role === 'user'
                    ? 'bg-white border border-border-dark text-ink-900'
                    : 'bg-primary/6 border border-primary/10 text-ink-800'"
                >
                  <div class="mb-1 flex items-center gap-2 text-[11px] text-ink-400">
                    <span>{{ message.role === 'user' ? '您' : 'AI 助手' }}</span>
                    <span v-if="message.createdAt">{{ formatClockTime(message.createdAt) }}</span>
                  </div>
                  <p class="whitespace-pre-wrap break-words text-sm leading-relaxed">{{ message.content || '暂无内容' }}</p>

                  <div
                    v-if="message.images && message.images.length > 0"
                    class="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3"
                  >
                    <img
                      v-for="(image, index) in message.images"
                      :key="`${message.id}-image-${index}`"
                      :src="resolveImageSrc(image.url)"
                      :alt="image.alt || `图片 ${index + 1}`"
                      class="w-full h-auto rounded-xl border border-border-dark object-contain"
                      @error="handleImageFallback"
                    >
                  </div>

                  <div
                    v-if="message.files && message.files.length > 0"
                    class="mt-3 flex flex-wrap gap-2"
                  >
                    <span
                      v-for="(file, index) in message.files"
                      :key="`${message.id}-file-${index}`"
                      class="inline-flex max-w-full items-center gap-1 rounded-full border border-border-dark bg-white/80 px-2.5 py-1 text-[11px] text-ink-500"
                    >
                      <span class="material-symbols-outlined !text-sm">attach_file</span>
                      <span class="truncate">{{ file.original_filename || '附件' }}</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="history-empty-state h-full">
          <span class="material-symbols-outlined !text-5xl text-ink-300">chat</span>
          <p class="text-sm text-ink-500">选择一条对话历史</p>
          <p class="text-xs text-ink-400">右侧将展示完整消息内容</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type UnifiedGenerationRecord } from '@/services/api'
import { useAppStore } from '@/store/useAppStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useHistoryStore, type HistorySession } from '@/store/useHistoryStore'
import { handleImageFallback, resolveImageSrc } from '@/utils/imageFallback'

const props = defineProps<{
  onClose?: (() => void) | null
}>()

const appStore = useAppStore()
const generatorStore = useGeneratorStore()
const historyStore = useHistoryStore()

const activeTab = ref<'generations' | 'conversations'>('generations')

const generationRecords = ref<UnifiedGenerationRecord[]>([])
const generationLoading = ref(false)
const generationHasMore = ref(true)
const generationOffset = ref(0)
const generationStatus = ref('')
const generationTotalCount = ref(0)
const generationLimit = 18

const conversationQuery = ref('')
const selectedConversationId = ref<string | null>(null)

const generationStatusTextMap: Record<string, string> = {
  pending: '排队中',
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
}

const statusPillClassMap: Record<string, string> = {
  pending: 'history-status-pill--pending',
  processing: 'history-status-pill--processing',
  completed: 'history-status-pill--completed',
  failed: 'history-status-pill--failed',
}

const filteredConversationSessions = computed(() => {
  const query = conversationQuery.value.trim().toLowerCase()
  const sessions = [...historyStore.sessions].sort((a, b) => (b.updatedAt || b.createdAt) - (a.updatedAt || a.createdAt))

  if (!query) return sessions

  return sessions.filter((session) => {
    const titleMatched = session.title?.toLowerCase().includes(query)
    const messageMatched = session.messages?.some((message) =>
      String(message.content || '').toLowerCase().includes(query)
    )
    return titleMatched || messageMatched
  })
})

const selectedConversation = computed<HistorySession | null>(() => {
  if (!selectedConversationId.value) return null
  return historyStore.sessions.find((session) => session.id === selectedConversationId.value) || null
})

watch(
  filteredConversationSessions,
  (sessions) => {
    if (!sessions.length) {
      selectedConversationId.value = null
      return
    }

    if (!selectedConversationId.value || !sessions.some((session) => session.id === selectedConversationId.value)) {
      selectedConversationId.value = sessions[0].id
      selectConversation(sessions[0].id)
    }
  },
  { immediate: true }
)

async function loadGenerationRecords(reset = false) {
  if (generationLoading.value) return

  generationLoading.value = true
  try {
    const nextOffset = reset ? 0 : generationOffset.value
    const records = await api.getUnifiedGenerationHistory(
      generationLimit,
      nextOffset,
      generationStatus.value || undefined
    )

    if (reset) {
      generationRecords.value = records
      generationOffset.value = records.length
    } else {
      generationRecords.value.push(...records)
      generationOffset.value += records.length
    }

    generationHasMore.value = records.length === generationLimit

    const countData = await api.getUnifiedGenerationHistoryCount(generationStatus.value || undefined)
    generationTotalCount.value = countData.count
  } catch (error) {
    console.error('加载生成历史失败:', error)
  } finally {
    generationLoading.value = false
  }
}

function reloadGenerationRecords() {
  generationHasMore.value = true
  generationOffset.value = 0
  loadGenerationRecords(true)
}

async function refreshConversations() {
  const currentSelection = selectedConversationId.value
  await historyStore.refresh()

  if (currentSelection && historyStore.sessions.some((session) => session.id === currentSelection)) {
    await selectConversation(currentSelection)
  }
}

async function selectConversation(sessionId: string) {
  selectedConversationId.value = sessionId

  const session = historyStore.sessions.find((item) => item.id === sessionId)
  if (!session) return

  if (session.loadedFromServer && (!session.messages || session.messages.length === 0)) {
    await historyStore.loadSessionDetails(session.id)
  }
}

function openGenerationRecord(record: UnifiedGenerationRecord) {
  appStore.setCurrentView('chat')
  appStore.setSelectedCreation(record)
  props.onClose?.()
}

async function openConversationInChat(sessionId: string) {
  const session = historyStore.sessions.find((item) => item.id === sessionId)
  if (!session) return

  if (session.loadedFromServer && (!session.messages || session.messages.length === 0)) {
    await historyStore.loadSessionDetails(session.id)
  }

  generatorStore.messages = session.messages.map((message) => ({
    ...message,
    images: message.images ? [...message.images] : [],
    files: message.files ? [...message.files] : []
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
  props.onClose?.()
}

async function removeConversation(sessionId: string) {
  if (!confirm('确定要删除这条对话历史吗？')) return

  try {
    await api.deleteConversationHistory(sessionId)
    historyStore.deleteSession(sessionId)
    if (selectedConversationId.value === sessionId) {
      selectedConversationId.value = filteredConversationSessions.value[0]?.id || null
    }
  } catch (error) {
    console.error('删除对话历史失败:', error)
  }
}

function getSessionPreview(session: HistorySession) {
  const lastMessage = [...(session.messages || [])].reverse().find((message) => String(message.content || '').trim().length > 0)
  if (lastMessage) return lastMessage.content
  return '点击查看完整对话历史'
}

function normalizeDateValue(value?: string | number) {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'number') return value

  const parsed = new Date(value).getTime()
  return Number.isFinite(parsed) ? parsed : null
}

function formatRelativeTime(value?: string | number) {
  const timestamp = normalizeDateValue(value)
  if (!timestamp) return '未知时间'

  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`

  return new Date(timestamp).toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
  })
}

function formatFullTime(value?: string | number) {
  const timestamp = normalizeDateValue(value)
  if (!timestamp) return '未知时间'

  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatClockTime(value?: string | number) {
  const timestamp = normalizeDateValue(value)
  if (!timestamp) return ''

  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function handleClose() {
  props.onClose?.()
}

onMounted(async () => {
  await Promise.all([
    loadGenerationRecords(true),
    historyStore.loadFromServer(),
  ])
})
</script>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(15, 23, 42, 0.18) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.18);
  border-radius: 999px;
}

.history-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: white;
  padding: 0.55rem 0.9rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(15, 23, 42, 0.58);
  transition: all 180ms ease;
}

.history-tab--active {
  border-color: rgba(15, 23, 42, 0.14);
  background: rgba(15, 23, 42, 0.96);
  color: white;
}

.history-empty-state {
  display: flex;
  min-height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem 1rem;
  text-align: center;
}

.history-spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid rgba(15, 23, 42, 0.12);
  border-top-color: rgba(15, 23, 42, 0.72);
  border-radius: 999px;
  animation: history-spin 0.9s linear infinite;
}

.generation-item,
.conversation-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 0.9rem;
  border-radius: 1rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: white;
  padding: 0.85rem;
  transition: all 180ms ease;
}

.generation-item:hover,
.conversation-item:hover {
  border-color: rgba(15, 23, 42, 0.16);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.conversation-item--active {
  border-color: rgba(15, 23, 42, 0.18);
  background: rgba(15, 23, 42, 0.03);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
}

.generation-item__thumb {
  width: 4.75rem;
  height: 4.75rem;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 0.95rem;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: #f3f4f6;
}

.generation-item__thumb-empty {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
  color: rgba(15, 23, 42, 0.22);
}

.history-status-pill,
.history-type-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.22rem 0.55rem;
  font-size: 0.68rem;
  font-weight: 700;
}

.history-status-pill--pending {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
}

.history-status-pill--processing {
  background: rgba(37, 99, 235, 0.1);
  color: #1d4ed8;
}

.history-status-pill--completed {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}

.history-status-pill--failed {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.history-type-pill {
  background: rgba(15, 23, 42, 0.06);
  color: rgba(15, 23, 42, 0.56);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@keyframes history-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
