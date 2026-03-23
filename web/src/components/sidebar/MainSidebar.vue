<template>
  <aside :class="asideClass">
    <nav v-if="!hideLogo" class="px-3 xs:px-4 md:px-4 pt-4 pb-3 space-y-1 shrink-0">
      <div :class="['flex items-center mb-4', props.mobileDrawer ? 'justify-between' : 'justify-center']">
        <div class="w-8 h-8 bg-gradient-to-br from-primary to-primary-deep rounded-lg flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined !text-lg text-white">auto_awesome</span>
        </div>
        <span :class="menuTitleClass">AI 生图助手</span>
        <button
          v-if="props.mobileDrawer"
          @click="emit('requestClose')"
          class="flex items-center justify-center p-1 rounded-lg text-ink-500 hover:text-ink-950 hover:bg-gray-100 transition-colors"
          aria-label="Close sidebar"
        >
          <span class="material-symbols-outlined !text-xl">close</span>
        </button>
      </div>

      <div :class="menuSectionTitleClass">主菜单</div>

      <button
        v-for="item in menuItems"
        :key="item.value || item.action"
        :class="[getMenuItemClass(item), menuItemButtonClass]"
        @click="handleMenuClick(item)"
      >
        <span class="material-symbols-outlined text-[20px] xs:text-[22px] md:text-[24px]">{{ item.icon }}</span>
        <span :class="menuItemLabelClass">{{ item.text }}</span>
      </button>

    </nav>

    <div class="flex-1 flex flex-col min-h-0 border-t border-border-dark">
      <div class="px-2 xs:px-3 py-3 shrink-0">
        <div class="relative">
          <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-500 !text-sm">search</span>
          <input
            v-model="searchInput"
            @input="handleSearch"
            type="text"
            placeholder="搜索模板..."
            class="w-full bg-white border border-border-dark rounded-lg pl-8 pr-2 py-1.5 text-xs focus:ring-1 focus:ring-primary focus:border-primary"
          >
        </div>
      </div>

      <div
        ref="caseListRef"
        class="flex-1 overflow-y-auto custom-scrollbar px-2 py-2 space-y-2"
      >
        <CaseCard
          v-for="caseItem in displayCases"
          :key="caseItem.id"
          :case-data="caseItem"
          @requestClose="handleCaseSelected"
        />

        <div v-if="loading && cases.length > 0" class="flex items-center justify-center py-4">
          <div class="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>

        <div v-else-if="!hasMore && cases.length > 0" class="text-center py-4">
          <p class="text-xs text-gray-500">没有更多模板了</p>
        </div>

        <div v-else-if="cases.length === 0 && !loading" class="text-center py-8">
          <p class="text-sm text-gray-500">暂无模板</p>
        </div>
      </div>
    </div>

    <div :class="userSectionClass">
      <UserMenuDropdown v-if="authStore.isAuthenticated" :hide-user-center="props.mobileDrawer" />
      <div v-else class="p-3">
        <button
          @click="handleLoginClick"
          class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white hover:bg-primary/5 rounded-xl border border-border-dark transition-colors shadow-sm"
        >
          <span class="material-symbols-outlined !text-xl text-primary">login</span>
          <span class="text-sm font-medium text-ink-950">登录</span>
        </button>
      </div>
    </div>
  </aside>

  <!-- Settings Drawer (从侧边栏右边缘滑出) - 使用Teleport传送到body -->
  <Teleport v-if="!props.mobileDrawer" to="body">
    <Transition name="settings-drawer">
      <div
        v-if="showSettingsDrawer"
        class="fixed z-[60] flex flex-col overflow-hidden bg-white/95 backdrop-blur-xl border border-border-dark shadow-2xl settings-drawer-panel">
        <!-- Drawer Header -->
        <div class="flex items-center justify-between gap-3 px-3 xs:px-4 py-3 border-b border-border-dark shrink-0">
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-ink-950 uppercase tracking-wider">生成参数</span>
            <button
              @click="showHelp = true"
              class="text-ink-500 hover:text-ink-950 flex items-center justify-center">
              <span class="material-symbols-outlined !text-lg">help</span>
            </button>
          </div>
          <button
            @click="toggleSettingsDrawer"
            class="text-ink-500 hover:text-ink-950 flex items-center justify-center p-1 rounded-lg hover:bg-gray-100 transition-colors">
            <span class="material-symbols-outlined !text-xl">close</span>
          </button>
        </div>

        <!-- Drawer Content -->
        <div class="flex-1 overflow-y-auto p-3 xs:p-4 sm:p-5 space-y-4 sm:space-y-5 custom-scrollbar">
          <!-- 当前模型 -->
          <div class="space-y-2">
            <label class="text-xs font-bold text-slate-500 uppercase">当前模型</label>
            <div class="bg-white border border-border-dark rounded-xl p-3 shadow-sm">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined !text-xl text-primary">auto_awesome</span>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-semibold truncate">{{ currentModelDisplay }}</div>
                  <div v-if="generatorStore.selectedModelInfo" class="text-[10px] text-slate-500 mt-0.5 line-clamp-2">
                    {{ generatorStore.selectedModelInfo.description }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 图像质量 -->
          <div class="space-y-2">
            <label class="text-xs font-bold text-slate-500 uppercase">图像质量</label>
            <div class="grid grid-cols-3 gap-2">
              <button
                v-for="quality in qualityOptions"
                :key="quality.value"
                @click="generatorStore.setQuality(quality.value)"
                :class="[
                  'py-2 text-xs font-bold rounded-lg transition-colors',
                  generatorStore.quality === quality.value
                    ? 'bg-primary-strong text-white shadow-sm'
                    : 'bg-white text-ink-700 border border-border-dark hover:bg-primary/5'
                ]">
                {{ quality.label }}
              </button>
            </div>
          </div>

          <!-- 图像尺寸 -->
          <div class="space-y-2">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <label class="text-xs font-bold text-slate-500 uppercase">图像尺寸</label>
              <span class="text-xs text-primary bg-primary/10 px-2 py-0.5 rounded-full font-bold">
                {{ generatorStore.width }}×{{ generatorStore.height }}
              </span>
            </div>

            <!-- 比例选择网格 -->
            <div class="grid grid-cols-2 xs:grid-cols-3 gap-2">
              <button
                v-for="ratio in ratioOptions"
                :key="ratio.value"
                @click="selectRatio(ratio)"
                :class="[
                  'flex flex-col items-center justify-center gap-1 py-2 px-2 rounded-xl transition-colors min-h-[72px]',
                  selectedRatio === ratio.value
                    ? 'bg-primary-strong text-white shadow-sm'
                    : 'bg-white text-ink-700 border border-border-dark hover:bg-primary/5'
                ]">
                <!-- 比例预览框 -->
                <div class="flex items-center justify-center w-6 h-6">
                  <div
                    :style="getRatioBoxStyle(ratio)"
                    :class="[
                      'rounded-sm border-2',
                      selectedRatio === ratio.value ? 'border-ink-950' : 'border-slate-500'
                    ]">
                  </div>
                </div>
                <span class="text-[10px] font-bold leading-tight">{{ ratio.label }}</span>
              </button>
            </div>

            <!-- 自定义尺寸（展开） -->
            <div v-if="showCustomSize" class="grid grid-cols-2 gap-2 mt-2">
              <div class="relative flex items-center">
                <input type="number" v-model.number="generatorStore.width"
                  class="w-full bg-white border border-border-dark rounded-xl text-sm py-2 px-3 focus:ring-1 focus:ring-primary focus:ring-offset-0">
                <span class="absolute right-2 text-[10px] text-slate-500 pointer-events-none">W</span>
              </div>
              <div class="relative flex items-center">
                <input type="number" v-model.number="generatorStore.height"
                  class="w-full bg-white border border-border-dark rounded-xl text-sm py-2 px-3 focus:ring-1 focus:ring-primary focus:ring-offset-0">
                <span class="absolute right-2 text-[10px] text-slate-500 pointer-events-none">H</span>
              </div>
            </div>
          </div>

          <!-- 批量数量 -->
          <div class="space-y-2">
            <label class="text-xs font-bold text-slate-500 uppercase">批量生成数量</label>
            <input
              type="number"
              v-model.number="generatorStore.batchSize"
              min="1"
              max="50"
              placeholder="输入数量"
              class="w-full bg-white border border-border-dark rounded-xl text-sm py-2.5 px-4 focus:ring-1 focus:ring-primary">
          </div>

          <!-- 负面提示词 -->
          <div class="space-y-2">
            <label class="text-xs font-bold text-slate-500 uppercase">负面提示词</label>
            <textarea
              v-model="generatorStore.negativePrompt"
              placeholder="描述你不希望出现在图像中的内容..."
              class="w-full bg-white border border-border-dark rounded-xl text-sm py-3 px-4 focus:ring-1 focus:ring-primary resize-none h-24 custom-scrollbar">
            </textarea>
          </div>

          <!-- 随机种子 -->
          <div class="space-y-2">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <label class="text-xs font-bold text-slate-500 uppercase">随机种子</label>
              <button
                v-if="generatorStore.seed"
                @click="generatorStore.setSeed('')"
                class="text-xs text-ink-500 hover:text-red-400">
                清除
              </button>
            </div>
            <div class="flex gap-2">
              <input
                type="text"
                v-model="generatorStore.seed"
                placeholder="留空为随机"
                class="flex-1 bg-white border border-border-dark rounded-xl text-sm py-2.5 px-4 focus:ring-1 focus:ring-primary">
              <button
                @click="generateRandomSeed"
                class="px-4 bg-white border border-border-dark rounded-xl hover:bg-primary/5 transition-colors">
                <span class="material-symbols-outlined !text-xl">shuffle</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 帮助弹窗 -->
  <div
    v-if="showHelp"
    @click="showHelp = false"
    class="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/10 p-4 xs:p-6 backdrop-blur-sm">
    <div
      @click.stop
      class="bg-white border border-border-dark rounded-2xl p-4 xs:p-6 max-w-md w-full mx-4 space-y-4 shadow-xl">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">参数说明</h3>
        <button @click="showHelp = false" class="text-ink-500 hover:text-ink-950">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="space-y-3 text-sm text-ink-700">
        <div>
          <strong class="text-ink-950">图像质量：</strong>标准（快速）、高清（更好质量）、超清（最佳质量）
        </div>
        <div>
          <strong class="text-ink-950">批量数量：</strong>一次性生成多张图像，数量1-50张
        </div>
        <div>
          <strong class="text-ink-950">负面提示词：</strong>描述你不希望出现在图像中的内容
        </div>
        <div>
          <strong class="text-ink-950">随机种子：</strong>设置固定值可以重复生成相同图像
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useCaseStore } from '@/store/useCaseStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import CaseCard from '../cases/CaseCard.vue'
import { useAppStore } from '@/store/useAppStore'
import { useAuthStore } from '@/store/useAuthStore'
import UserMenuDropdown from '../layout/UserMenuDropdown.vue'

const appStore = useAppStore()
const authStore = useAuthStore()
const generatorStore = useGeneratorStore()

const props = defineProps({
  hideLogo: { type: Boolean, default: false },
  mobileDrawer: { type: Boolean, default: false }
})

const caseStore = useCaseStore()
const caseListRef = ref(null)
const searchInput = ref('')

const asideClass = computed(() => {
  if (props.mobileDrawer) {
    return 'w-full h-full flex flex-col border-r border-border-dark bg-white/95 backdrop-blur-xl relative'
  }
  return 'hidden md:flex w-28 xs:w-32 sm:w-44 md:w-56 lg:w-56 xl:w-64 flex-col border-r border-border-dark bg-white/90 backdrop-blur-xl shrink-0 h-screen transition-all duration-300 relative'
})

const menuTitleClass = computed(() => {
  return props.mobileDrawer ? 'text-sm font-bold text-ink-950 ml-2 flex-1' : 'text-sm font-bold text-ink-950 hidden md:block ml-2'
})

const menuItemButtonClass = computed(() => {
  return props.mobileDrawer
    ? 'w-full flex items-center justify-start gap-3 px-3 py-2.5 rounded-xl transition-colors text-left'
    : 'w-full flex items-center justify-center md:justify-start gap-2 md:gap-3 px-2 md:px-3 py-2.5 rounded-xl transition-colors text-left'
})

const menuItemLabelClass = computed(() => {
  return props.mobileDrawer ? 'inline text-sm' : 'hidden md:inline text-xs xs:text-sm'
})

const menuSectionTitleClass = computed(() => {
  return props.mobileDrawer
    ? 'text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 text-left px-3'
    : 'text-[10px] xs:text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 text-center md:text-left md:px-3'
})

const userSectionClass = computed(() => {
  return props.mobileDrawer
    ? 'block shrink-0 border-t border-border-dark bg-gray-50/50'
    : 'hidden lg:block shrink-0 border-t border-border-dark bg-gray-50/50'
})

// Settings drawer state
const showSettingsDrawer = ref(false)
const showHelp = ref(false)

// Toggle settings drawer
const toggleSettingsDrawer = () => {
  showSettingsDrawer.value = !showSettingsDrawer.value
}

// Close settings drawer (called by parent)
const closeSettingsDrawer = () => {
  showSettingsDrawer.value = false
}

// Expose closeSettingsDrawer to parent
defineExpose({
  closeSettingsDrawer,
  toggleSettingsDrawer,
  showSettingsDrawer
})

// Navigation menu items
const menuItems = [
  { icon: 'smart_toy', text: '首页', value: 'landing' },
  { icon: 'auto_awesome', text: 'AI图片生成', value: 'generate', active: true },
  { icon: 'view_module', text: '模板库', action: 'templates' },
  { icon: 'history', text: '历史记录', action: 'history' },
]

// Get menu item class
const getMenuItemClass = (item) => {
  let isActive = false

  if (item.value) {
    // For value-based items (landing, generate)
    isActive = appStore.selectedMenuItem === item.value
  } else if (item.action) {
    // For action-based items (templates, history)
    isActive = appStore.selectedMenuItem === item.action
  }

  return isActive
    ? 'bg-primary/10 text-primary font-medium'
    : 'text-ink-700 hover:bg-primary/5'
}

// Restore menu selection based on current view
const restoreMenuSelection = () => {
  if (appStore.currentView === 'landing') {
    appStore.selectedMenuItem = 'landing'
  } else if (appStore.currentView === 'chat') {
    appStore.selectedMenuItem = 'generate'
  }
}

// Watch drawer states to restore menu selection when drawers close
watch(() => appStore.showTemplateDrawer, (newVal, oldVal) => {
  // When drawer closes (true -> false)
  if (oldVal === true && newVal === false) {
    restoreMenuSelection()
  }
})

watch(() => appStore.showCreationRecords, (newVal, oldVal) => {
  // When drawer closes (true -> false)
  if (oldVal === true && newVal === false) {
    restoreMenuSelection()
  }
})

// Handle menu item clicks
const requestCloseIfMobile = () => {
  if (props.mobileDrawer) {
    emit('requestClose')
  }
}

const handleMenuClick = (item) => {
  if (item.action) {
    // Handle action-based items (open drawers/modals)
    // Note: setSelectedMenuItem will handle the drawer toggling internally
    appStore.setSelectedMenuItem(item.action)

    // Special handling for history drawer (emit event to parent)
    if (item.action === 'history') {
      emit('openHistory')
    }
    // templates, creations, settings are handled by setSelectedMenuItem
  } else {
    // Handle view-based items
    appStore.setSelectedMenuItem(item.value)
  }

  requestCloseIfMobile()
}

const handleCaseSelected = () => {
  requestCloseIfMobile()
}

const handleLoginClick = () => {
  appStore.setCurrentPage('login')
  requestCloseIfMobile()
}

// Emit event for history drawer (parent component will handle)
const emit = defineEmits(['openHistory', 'settingsDrawerChange', 'requestClose'])

// Watch settings drawer state and emit to parent
watch(showSettingsDrawer, (newValue) => {
  emit('settingsDrawerChange', newValue)
})

// Settings-related data and methods
const ratioOptions = [
  { value: 'auto',  label: 'Auto',  desc: '自动',   w: 1024, h: 1024 },
  { value: '1:1',   label: '1:1',   desc: '方形',   w: 1024, h: 1024 },
  { value: '3:4',   label: '3:4',   desc: '竖版',   w: 768,  h: 1024 },
  { value: '4:3',   label: '4:3',   desc: '横版',   w: 1024, h: 768  },
  { value: '9:16',  label: '9:16',  desc: '竖版',   w: 576,  h: 1024 },
  { value: '16:9',  label: '16:9',  desc: '横版',   w: 1024, h: 576  },
  { value: '2:3',   label: '2:3',   desc: '竖版',   w: 683,  h: 1024 },
  { value: '3:2',   label: '3:2',   desc: '横版',   w: 1024, h: 683  },
  { value: '4:5',   label: '4:5',   desc: '竖版',   w: 819,  h: 1024 },
  { value: '5:4',   label: '5:4',   desc: '横版',   w: 1024, h: 819  },
  { value: '21:9',  label: '21:9',  desc: '影院',   w: 1024, h: 439  },
  { value: 'custom',label: '自定义', desc: '更多',   w: null, h: null },
]

const selectedRatio = ref('1:1')
const showCustomSize = ref(false)

const selectRatio = (ratio) => {
  if (ratio.value === 'custom') {
    showCustomSize.value = !showCustomSize.value
    return
  }
  selectedRatio.value = ratio.value
  showCustomSize.value = false

  // 根据当前质量设置调整尺寸
  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  const maxDim = maxDimMap[generatorStore.quality] || 1024

  // 计算当前比例
  const ratioValue = ratio.w / ratio.h

  // 根据比例和最大边长计算最终尺寸
  if (ratioValue >= 1) {
    // 横向或方形图片
    generatorStore.width = maxDim
    generatorStore.height = Math.round(maxDim / ratioValue)
  } else {
    // 竖向图片
    generatorStore.height = maxDim
    generatorStore.width = Math.round(maxDim * ratioValue)
  }
}

const getRatioBoxStyle = (ratio) => {
  if (!ratio.w || !ratio.h) return { width: '20px', height: '20px' }
  const maxDim = 24
  const r = ratio.w / ratio.h
  if (r >= 1) {
    return { width: `${maxDim}px`, height: `${Math.round(maxDim / r)}px` }
  } else {
    return { width: `${Math.round(maxDim * r)}px`, height: `${maxDim}px` }
  }
}

// 质量选项
const qualityOptions = [
  { value: '720p', label: '720P' },
  { value: '2k', label: '2K' },
  { value: '4k', label: '4K' },
]

// 当前模型显示
const currentModelDisplay = computed(() => {
  return generatorStore.selectedModelInfo?.model_name || generatorStore.model || '未选择模型'
})

// 生成随机种子
const generateRandomSeed = () => {
  generatorStore.setSeed(Math.floor(Math.random() * 999999999).toString())
}

// 获取案例列表
const cases = computed(() => caseStore.cases)
const loading = computed(() => caseStore.loading)
const hasMore = computed(() => caseStore.hasMore)

// 显示的案例（考虑搜索）
const displayCases = computed(() => {
  let result = cases.value

  // 按关键词搜索
  if (searchInput.value) {
    const query = searchInput.value.toLowerCase()
    result = result.filter(c =>
      c.title.toLowerCase().includes(query) ||
      c.description?.toLowerCase().includes(query) ||
      c.tags?.some(tag => tag.toLowerCase().includes(query))
    )
  }

  return result
})

const handleSearch = () => {
  // 使用防抖来减少筛选
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    // 搜索逻辑已经在computed中处理
  }, 300)
}

let searchTimeout = null

// 案例列表滚动加载更多
const handleCaseListScroll = () => {
  if (!caseListRef.value) return

  const { scrollTop, scrollHeight, clientHeight } = caseListRef.value

  // 距离底部50px时加载更多
  if (scrollHeight - scrollTop - clientHeight < 50) {
    caseStore.loadMore()
  }
}

onMounted(() => {
  // 初始化案例
  if (caseStore.cases.length === 0) {
    caseStore.initialize()
  }

  // 添加案例列表滚动监听
  if (caseListRef.value) {
    caseListRef.value.addEventListener('scroll', handleCaseListScroll)
  }
})

onUnmounted(() => {
  if (caseListRef.value) {
    caseListRef.value.removeEventListener('scroll', handleCaseListScroll)
  }
})
</script>

<style scoped>
/* 自定义滚动条 */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

/* Settings Drawer Animation - 从侧边栏右边缘向右滑出 */
.settings-drawer-enter-active,
.settings-drawer-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
}

.settings-drawer-enter-from,
.settings-drawer-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}

.settings-drawer-enter-to,
.settings-drawer-leave-from {
  transform: translateX(0);
  opacity: 1;
}

/* Settings drawer positioning */
.settings-drawer-panel {
  top: 0.75rem;
  right: 0.75rem;
  bottom: 0.75rem;
  left: 0.75rem;
  width: auto;
  max-height: calc(100vh - 1.5rem);
  border-radius: 1rem;
}

@media (min-width: 768px) {
  .settings-drawer-panel {
    left: 14rem;
    right: 1rem;
    width: min(24rem, calc(100vw - 14rem - 1rem));
  }
}

@media (min-width: 1280px) {
  .settings-drawer-panel {
    left: 16rem;
    right: 1.5rem;
    width: min(24rem, calc(100vw - 16rem - 1.5rem));
  }
}

@media (max-width: 474px) {
  .settings-drawer-panel {
    top: 0.5rem;
    right: 0.5rem;
    bottom: 0.5rem;
    left: 0.5rem;
    max-height: calc(100vh - 1rem);
  }
}

@supports (height: 100dvh) {
  .settings-drawer-panel {
    max-height: calc(100dvh - 1.5rem);
  }
}

@supports (height: 100dvh) {
  @media (max-width: 474px) {
    .settings-drawer-panel {
      max-height: calc(100dvh - 1rem);
    }
  }
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
