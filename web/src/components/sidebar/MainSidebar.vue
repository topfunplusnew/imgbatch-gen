<template>
  <aside :class="asideClass">
    <div v-if="!hideLogo" class="shrink-0 px-3 pt-4 pb-3">
      <div :class="['flex items-center gap-3 rounded-[20px] bg-white/90 px-3 py-3 shadow-sm', props.mobileDrawer ? 'justify-between' : 'justify-center']">
        <button
          type="button"
          class="flex flex-1 items-center justify-center rounded-[16px] transition-colors hover:bg-primary/5"
          @click="navigateHome"
        >
          <img
            src="/photo/logo.png"
            alt="Logo"
            class="h-auto w-[76%] object-contain"
            style="aspect-ratio: 240/160;"
          />
        </button>
        <el-button
          v-if="props.mobileDrawer"
          circle
          text
          @click="emit('requestClose')"
          aria-label="Close sidebar"
        >
          <span class="material-symbols-outlined !text-xl">close</span>
        </el-button>
      </div>
    </div>

    <div class="shrink-0 px-3 pb-3">
      <div class="mb-2 px-3 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">
        主菜单
      </div>
      <el-menu
        :default-active="activeMenuItem"
        class="main-sidebar-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.value"
          :index="item.value"
          class="main-sidebar-menu__item"
        >
          <component v-if="item.iconComponent" :is="item.iconComponent" />
          <span
            v-else-if="item.iconClass"
            :class="['k-icon', item.iconClass, 'icon']"
            style="font-family: 'Material Symbols Outlined';"
          >
            {{ item.icon }}
          </span>
          <span v-else class="material-symbols-outlined text-[20px]">{{ item.icon }}</span>
          <span class="text-sm font-medium">{{ item.text }}</span>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="flex min-h-0 flex-1 flex-col border-t border-border-dark/70">
      <div class="shrink-0 px-3 py-3">
        <el-button
          type="primary"
          class="w-full justify-center"
          :loading="generatorStore.isStartingNewConversation"
          @click="startNewConversation"
        >
          <span class="material-symbols-outlined !text-lg">add</span>
          <span>{{ generatorStore.isStartingNewConversation ? '创建中...' : '新对话' }}</span>
        </el-button>

        <div class="mt-3 flex items-center gap-2">
          <el-input
            v-model="historyStore.searchQuery"
            clearable
            placeholder="搜索历史对话..."
          >
            <template #prefix>
              <span class="material-symbols-outlined !text-sm text-ink-500">search</span>
            </template>
          </el-input>

          <el-button
            circle
            :loading="historyStore.isLoading"
            @click="refreshHistory"
            aria-label="Refresh history"
          >
            <span class="material-symbols-outlined !text-lg">refresh</span>
          </el-button>
        </div>
      </div>

      <el-scrollbar class="main-sidebar-scroll flex-1 px-2 pb-2">
        <div v-if="historyStore.isLoading && groupedSessions.length === 0" class="px-2 py-2">
          <el-card shadow="never" class="history-empty-card">
            <div class="flex flex-col items-center justify-center gap-2 py-8 text-center">
              <el-icon class="is-loading text-primary"><Loading /></el-icon>
              <p class="text-xs text-ink-500">正在加载历史记录...</p>
            </div>
          </el-card>
        </div>

        <div v-else-if="groupedSessions.length === 0" class="px-2 py-2">
          <el-card shadow="never" class="history-empty-card">
            <el-empty description="暂无历史记录" :image-size="58" />
          </el-card>
        </div>

        <div v-else class="pr-1">
          <div
            v-for="group in groupedSessions"
            :key="group.label"
            class="history-group"
          >
            <div class="history-group__label">
              {{ group.label }}
            </div>

            <el-menu
              :default-active="activeHistorySessionId"
              class="history-session-menu"
              @select="handleHistorySelect"
            >
              <el-menu-item
                v-for="session in group.sessions"
                :key="session.id"
                :index="session.id"
                class="history-session-menu__item"
              >
                <div class="history-session-item">
                  <div class="history-session-item__title">
                    {{ session.title || '未命名对话' }}
                  </div>
                  <div class="history-session-item__meta">
                    <span>{{ formatSessionTime(session.updatedAt || session.createdAt) }}</span>
                    <span>{{ session.messageCount || session.messages?.length || 0 }} 条消息</span>
                  </div>
                </div>
              </el-menu-item>
            </el-menu>
          </div>
        </div>
      </el-scrollbar>
    </div>

    <div :class="userSectionClass">
      <UserMenuDropdown v-if="authStore.isAuthenticated" :hide-user-center="props.mobileDrawer" />
      <div v-else class="p-3">
        <el-button type="default" class="w-full justify-center" @click="handleLoginClick">
          <span class="material-symbols-outlined !text-lg text-primary">login</span>
          <span>登录</span>
        </el-button>
      </div>
    </div>
  </aside>

  <el-drawer
    v-if="!props.mobileDrawer"
    v-model="showSettingsDrawer"
    append-to-body
    :modal="false"
    :with-header="false"
    direction="rtl"
    size="clamp(320px, 29vw, 420px)"
    class="sidebar-settings-drawer"
  >
    <div class="flex h-full flex-col">
      <div class="flex items-center justify-between gap-3 border-b border-border-dark px-5 py-4">
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold uppercase tracking-[0.22em] text-ink-950">生成参数</span>
          <el-button circle text @click="showHelp = true">
            <span class="material-symbols-outlined !text-lg">help</span>
          </el-button>
        </div>
        <el-button circle text @click="toggleSettingsDrawer">
          <span class="material-symbols-outlined !text-xl">close</span>
        </el-button>
      </div>

      <el-scrollbar class="flex-1 px-5 py-5">
        <div class="space-y-5">
          <section class="space-y-2">
            <div class="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">当前模型</div>
            <el-card shadow="never" class="settings-card">
              <div class="flex items-start gap-3">
                <div class="grid h-10 w-10 place-items-center rounded-2xl bg-primary-soft text-primary">
                  <span class="material-symbols-outlined !text-xl">auto_awesome</span>
                </div>
                <div class="min-w-0 flex-1">
                  <div class="truncate text-sm font-semibold">{{ currentModelDisplay }}</div>
                  <div
                    v-if="generatorStore.selectedModelInfo?.description"
                    class="line-clamp-2 mt-1 text-xs text-slate-500"
                  >
                    {{ generatorStore.selectedModelInfo.description }}
                  </div>
                </div>
              </div>
            </el-card>
          </section>

          <section class="space-y-2">
            <div class="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">图像质量</div>
            <el-radio-group
              :model-value="generatorStore.quality"
              class="settings-radio-group"
              @change="generatorStore.setQuality"
            >
              <el-radio-button
                v-for="quality in qualityOptions"
                :key="quality.value"
                :label="quality.value"
              >
                {{ quality.label }}
              </el-radio-button>
            </el-radio-group>
          </section>

          <section class="space-y-3">
            <div class="flex items-center justify-between gap-3">
              <div class="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">图像尺寸</div>
              <el-tag round effect="plain" class="!border-primary/20 !bg-primary-soft !text-primary">
                {{ generatorStore.width }}×{{ generatorStore.height }}
              </el-tag>
            </div>

            <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
              <el-button
                v-for="ratio in ratioOptions"
                :key="ratio.value"
                :type="selectedRatio === ratio.value ? 'primary' : 'default'"
                :plain="selectedRatio !== ratio.value"
                class="ratio-button !h-auto !whitespace-normal !px-3 !py-3"
                @click="selectRatio(ratio)"
              >
                <div class="flex flex-col items-center gap-1">
                  <div class="flex h-8 w-8 items-center justify-center">
                    <div
                      :style="getRatioBoxStyle(ratio)"
                      :class="[
                        'rounded-sm border-2 transition-colors',
                        selectedRatio === ratio.value ? 'border-white' : 'border-slate-400'
                      ]"
                    ></div>
                  </div>
                  <span class="text-xs font-semibold">{{ ratio.label }}</span>
                  <span class="text-[10px] opacity-80">{{ ratio.desc }}</span>
                </div>
              </el-button>
            </div>

            <div v-if="showCustomSize" class="grid grid-cols-2 gap-3">
              <el-input-number
                v-model="generatorStore.width"
                :min="64"
                :max="8192"
                controls-position="right"
                placeholder="宽度"
              />
              <el-input-number
                v-model="generatorStore.height"
                :min="64"
                :max="8192"
                controls-position="right"
                placeholder="高度"
              />
            </div>
          </section>

          <section class="space-y-2">
            <div class="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">负面提示词</div>
            <el-input
              v-model="generatorStore.negativePrompt"
              type="textarea"
              :rows="4"
              resize="none"
              placeholder="描述你不希望出现在图像中的内容..."
            />
          </section>

          <section class="space-y-2">
            <div class="flex items-center justify-between gap-3">
              <div class="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">随机种子</div>
              <el-button
                v-if="generatorStore.seed"
                text
                type="danger"
                @click="generatorStore.setSeed('')"
              >
                清除
              </el-button>
            </div>
            <div class="flex items-center gap-2">
              <el-input
                v-model="generatorStore.seed"
                class="flex-1"
                placeholder="留空为随机"
              />
              <el-button circle @click="generateRandomSeed">
                <span class="material-symbols-outlined !text-lg">shuffle</span>
              </el-button>
            </div>
          </section>
        </div>
      </el-scrollbar>
    </div>
  </el-drawer>

  <el-dialog
    v-model="showHelp"
    align-center
    append-to-body
    class="sidebar-help-dialog"
    width="min(420px, calc(100vw - 32px))"
  >
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-ink-950">参数说明</h3>
      </div>
    </template>
    <div class="space-y-3 text-sm text-ink-700">
      <div><strong class="text-ink-950">图像质量：</strong>标准、高清、超清，对应不同速度与细节等级。</div>
      <div><strong class="text-ink-950">生图数量：</strong>可在聊天输入区快捷调整，支持 1-50 张。</div>
      <div><strong class="text-ink-950">负面提示词：</strong>描述不希望出现在图像中的元素。</div>
      <div><strong class="text-ink-950">随机种子：</strong>固定种子可复现相近结果。</div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useHistoryStore } from '@/store/useHistoryStore'
import { useAppStore } from '@/store/useAppStore'
import { useAuthStore } from '@/store/useAuthStore'
import UserMenuDropdown from '../layout/UserMenuDropdown.vue'
import AIGenerateIcon from '../icons/AIGenerateIcon.vue'

const appStore = useAppStore()
const authStore = useAuthStore()
const generatorStore = useGeneratorStore()
const historyStore = useHistoryStore()

const props = defineProps({
  hideLogo: { type: Boolean, default: false },
  mobileDrawer: { type: Boolean, default: false }
})

const emit = defineEmits(['settingsDrawerChange', 'requestClose'])

const showSettingsDrawer = ref(false)
const showHelp = ref(false)
const selectedRatio = ref('auto')
const showCustomSize = ref(false)

const asideClass = computed(() => {
  return props.mobileDrawer
    ? 'flex h-full w-full flex-col overflow-hidden bg-white/95 backdrop-blur-xl'
    : 'hidden h-full w-full flex-col overflow-hidden bg-white/82 backdrop-blur-xl md:flex'
})

const userSectionClass = computed(() => {
  return props.mobileDrawer
    ? 'block shrink-0 border-t border-border-dark bg-white/75'
    : 'hidden shrink-0 border-t border-border-dark bg-white/70 lg:block'
})

const menuItems = [
  { iconComponent: AIGenerateIcon, text: 'AI图片生成', value: 'generate' },
  { icon: 'dashboard', text: '模版列表', value: 'templates' }
]

const activeMenuItem = computed(() => appStore.selectedMenuItem || 'landing')
const activeHistorySessionId = computed(() => generatorStore.currentSessionId || '')

const ratioOptions = [
  { value: 'auto', label: 'Auto', desc: '自动', w: 1024, h: 1024 },
  { value: '1:1', label: '1:1', desc: '方形', w: 1024, h: 1024 },
  { value: '3:4', label: '3:4', desc: '竖版', w: 768, h: 1024 },
  { value: '4:3', label: '4:3', desc: '横版', w: 1024, h: 768 },
  { value: '9:16', label: '9:16', desc: '竖版', w: 576, h: 1024 },
  { value: '16:9', label: '16:9', desc: '横版', w: 1024, h: 576 },
  { value: '2:3', label: '2:3', desc: '竖版', w: 683, h: 1024 },
  { value: '3:2', label: '3:2', desc: '横版', w: 1024, h: 683 },
  { value: '4:5', label: '4:5', desc: '竖版', w: 819, h: 1024 },
  { value: '5:4', label: '5:4', desc: '横版', w: 1024, h: 819 },
  { value: '21:9', label: '21:9', desc: '影院', w: 1024, h: 439 },
  { value: 'custom', label: '自定义', desc: '更多', w: null, h: null }
]

const qualityOptions = [
  { value: '720p', label: '720P' },
  { value: '2k', label: '2K' },
  { value: '4k', label: '4K' }
]

const currentModelDisplay = computed(() => {
  return (
    generatorStore.selectedModelInfo?.display_name ||
    generatorStore.selectedModelInfo?.model_name ||
    generatorStore.model ||
    '未选择模型'
  )
})

const groupedSessions = computed(() => {
  const now = Date.now()
  const todayStart = new Date().setHours(0, 0, 0, 0)
  const weekStart = todayStart - 7 * 24 * 60 * 60 * 1000
  const monthStart = todayStart - 30 * 24 * 60 * 60 * 1000
  const query = historyStore.searchQuery.trim().toLowerCase()

  let sessions = [...historyStore.sessions].sort(
    (a, b) => (b.updatedAt || b.createdAt) - (a.updatedAt || a.createdAt)
  )

  if (query) {
    sessions = sessions.filter((session) => {
      const matchedTitle = session.title?.toLowerCase().includes(query)
      const matchedMessage = session.messages?.some((message) =>
        String(message.content || '').toLowerCase().includes(query)
      )
      return matchedTitle || matchedMessage
    })
  }

  const groups = {
    today: [],
    week: [],
    month: [],
    older: []
  }

  sessions.forEach((session) => {
    const timestamp = session.updatedAt || session.createdAt || now

    if (timestamp >= todayStart) {
      groups.today.push(session)
    } else if (timestamp >= weekStart) {
      groups.week.push(session)
    } else if (timestamp >= monthStart) {
      groups.month.push(session)
    } else {
      groups.older.push(session)
    }
  })

  const labelMap = {
    today: '今天',
    week: '7 天内',
    month: '30 天内',
    older: '更早'
  }

  return Object.entries(groups)
    .filter(([, sessionsInGroup]) => sessionsInGroup.length > 0)
    .map(([key, sessionsInGroup]) => ({
      label: labelMap[key],
      sessions: sessionsInGroup
    }))
})

const toggleSettingsDrawer = () => {
  showSettingsDrawer.value = !showSettingsDrawer.value
}

const closeSettingsDrawer = () => {
  showSettingsDrawer.value = false
}

defineExpose({
  closeSettingsDrawer,
  toggleSettingsDrawer,
  showSettingsDrawer
})

watch(showSettingsDrawer, (newValue) => {
  emit('settingsDrawerChange', newValue)
})

const requestCloseIfMobile = () => {
  if (props.mobileDrawer) {
    emit('requestClose')
  }
}

const handleMenuSelect = (index) => {
  appStore.setSelectedMenuItem(index)
  requestCloseIfMobile()
}

const navigateHome = () => {
  appStore.setCurrentView('landing')
  requestCloseIfMobile()
}

const handleLoginClick = () => {
  appStore.goToLogin()
  requestCloseIfMobile()
}

const refreshHistory = async () => {
  await historyStore.refresh()
}

const syncSelectedModelInfo = (modelName) => {
  generatorStore.setSelectedModel(modelName)

  const matchedModel = generatorStore.availableModels.find((model) => model.model_name === modelName)
  generatorStore.setSelectedModelInfo(matchedModel || null)
}

const openHistorySession = async (session) => {
  if (session.loadedFromServer && (!session.messages || session.messages.length === 0)) {
    const result = await historyStore.loadSessionDetails(session.id)
    if (result) {
      session.messages = result.messages
      session.files = result.files || []
    }
  }

  generatorStore.messages = (session.messages || []).map((message) => ({
    ...message,
    images: message.images ? [...message.images] : [],
    files: message.files ? [...message.files] : []
  }))
  generatorStore.currentSessionTitle = session.title || '无标题会话'
  generatorStore.currentSessionId = session.id
  generatorStore.sessionSavedToHistory = true
  generatorStore.prompt = ''
  generatorStore.clearAttachments()
  syncSelectedModelInfo(session.model || generatorStore.model)

  appStore.clearSelectedCase()
  appStore.setCurrentView('chat')
  requestCloseIfMobile()
}

const handleHistorySelect = async (sessionId) => {
  const session = historyStore.sessions.find((item) => item.id === sessionId)
  if (!session) return
  await openHistorySession(session)
}

const startNewConversation = async () => {
  appStore.setCurrentPage('agent')
  appStore.clearSelectedCase()
  appStore.setCurrentView('chat')
  await generatorStore.startNewConversation()
  requestCloseIfMobile()
}

const selectRatio = (ratio) => {
  if (ratio.value === 'custom') {
    showCustomSize.value = !showCustomSize.value
    selectedRatio.value = 'custom'
    return
  }

  selectedRatio.value = ratio.value
  showCustomSize.value = false

  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  const maxDim = maxDimMap[generatorStore.quality] || 1024
  const ratioValue = ratio.w / ratio.h

  if (ratioValue >= 1) {
    generatorStore.width = maxDim
    generatorStore.height = Math.round(maxDim / ratioValue)
  } else {
    generatorStore.height = maxDim
    generatorStore.width = Math.round(maxDim * ratioValue)
  }
}

const getRatioBoxStyle = (ratio) => {
  if (!ratio.w || !ratio.h) return { width: '20px', height: '20px' }

  const maxDim = 24
  const ratioValue = ratio.w / ratio.h
  if (ratioValue >= 1) {
    return { width: `${maxDim}px`, height: `${Math.round(maxDim / ratioValue)}px` }
  }

  return { width: `${Math.round(maxDim * ratioValue)}px`, height: `${maxDim}px` }
}

const generateRandomSeed = () => {
  generatorStore.setSeed(Math.floor(Math.random() * 999999999).toString())
}

const formatSessionTime = (timestamp) => {
  const date = new Date(timestamp)
  const todayStart = new Date().setHours(0, 0, 0, 0)

  if (timestamp >= todayStart) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

onMounted(() => {
  if (historyStore.sessions.length === 0) {
    historyStore.loadFromServer()
  }
})
</script>

<style scoped>
.main-sidebar-menu {
  background: transparent;
}

.main-sidebar-menu :deep(.el-menu-item) {
  margin-bottom: 8px;
  border-radius: 16px;
  height: auto;
  min-height: 52px;
  line-height: 1.2;
}

.main-sidebar-menu :deep(.el-menu-item .el-menu-tooltip__trigger) {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-sidebar-scroll :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

.history-empty-card :deep(.el-card__body) {
  padding: 10px;
}

.history-group + .history-group {
  margin-top: 16px;
}

.history-group__label {
  padding: 0 12px 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-ink-500);
}

.history-session-menu {
  background: transparent;
}

.history-session-menu :deep(.el-menu-item-group__title) {
  padding: 0;
}

.history-session-menu :deep(.el-menu-item) {
  height: auto;
  min-height: 0;
  margin: 0 6px 8px;
  padding: 0 !important;
  border-radius: 18px;
  align-items: stretch;
  line-height: 1.2;
}

.history-session-menu :deep(.el-menu-item .el-menu-tooltip__trigger) {
  display: block;
  width: 100%;
  line-height: 1.2;
}

.history-session-menu :deep(.el-menu-item.is-active) {
  background: rgba(140, 42, 46, 0.1);
}

.history-session-menu :deep(.el-menu-item:hover) {
  background: rgba(140, 42, 46, 0.06);
}

.history-session-item {
  width: 100%;
  min-width: 0;
  padding: 10px 12px;
}

.history-session-item__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ink-950);
  line-height: 1.35;
}

.history-session-item__meta {
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 10px;
  line-height: 1.2;
  color: var(--color-ink-500);
}

.sidebar-settings-drawer :deep(.el-drawer) {
  margin: 12px;
  height: calc(100% - 24px);
  border-radius: 28px;
}

.sidebar-settings-drawer :deep(.el-drawer__body) {
  padding: 0;
}

.settings-card :deep(.el-card__body) {
  padding: 16px;
}

.settings-radio-group {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.settings-radio-group :deep(.el-radio-button__inner) {
  width: 100%;
  border-radius: 14px;
  border-left: 1px solid var(--color-border-dark);
}

.ratio-button :deep(span) {
  white-space: normal;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
