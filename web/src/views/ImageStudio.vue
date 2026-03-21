<template>
  <div class="h-screen flex overflow-hidden bg-background-dark text-ink-950 font-display">
    <!-- 左侧导航 (hidden on mobile) -->
    <MainSidebar :class="['hidden md:flex']" />

    <!-- 主交互区 -->
    <main class="flex-1 flex flex-col relative bg-white/60 min-w-0 xs:min-w-[300px] md:min-w-[400px] lg:min-w-[500px] h-screen overflow-hidden">
      <TopHeader
        @openModelSelector="showModelSelector = true"
        @toggleSettings="showSettingsDrawer = !showSettingsDrawer"
        @openHistory="showHistoryDrawer = true"
        @openTemplates="appStore.toggleTemplateDrawer()"
      />

      <!-- 通知轮播 (显示重要公告) -->
      <div class="px-3 xs:px-4 sm:px-6 md:px-8 pt-4">
        <NotificationCarousel :autoplay="true" :autoplay-interval="5000" :max-items="3" />
      </div>

      <!-- 对话滚动区域 -->
      <div
        ref="chatAreaRef"
        class="flex-1 overflow-y-auto custom-scrollbar p-3 xs:p-4 sm:p-6 md:p-8 min-h-0 pb-8"
        :style="chatAreaStyle">

        <!-- 案例详情面板 -->
        <CaseDetailPanel />

        <!-- 创作记录详情面板 -->
        <CreationDetailPanel />

        <div class="max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-5xl mx-auto space-y-6 md:space-y-8">
          <MessageItem v-for="msg in generatorStore.messages" :key="msg.id" :msg="msg" />
        </div>
      </div>

      <!-- 底部输入框 -->
      <ChatInputBar />
    </main>

    <!-- 右侧参数面板 (hidden on mobile) -->
    <!-- 拖拽分隔条 -->
    <div
      v-if="!isMobile"
      class="w-1 cursor-col-resize bg-border-dark hover:bg-primary/30 transition-colors shrink-0 select-none"
      @mousedown="startResize">
    </div>
    <SettingsSidebar v-if="!isMobile && !showSettingsDrawer" :style="{ width: sidebarWidth + 'px', minWidth: sidebarWidth + 'px' }" />

    <!-- 移动端参数抽屉 -->
    <Transition name="drawer">
      <div v-if="showSettingsDrawer" class="fixed inset-0 z-40" @click.self="showSettingsDrawer = false">
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-ink-950/10 backdrop-blur-sm" @click="showSettingsDrawer = false"></div>
        <!-- 抽屉面板 -->
        <div class="absolute right-0 top-0 w-[85vw] max-w-[320px] md:max-w-[400px] h-full flex flex-col bg-white/95 backdrop-blur-xl border-l border-border-dark shadow-xl">
          <div class="flex items-center justify-between p-3 border-b border-border-dark shrink-0">
            <span class="font-bold text-sm uppercase tracking-wider">生成参数</span>
            <button @click="showSettingsDrawer = false" class="text-ink-500 hover:text-ink-950">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto">
            <SettingsSidebar :in-drawer="true" />
          </div>
        </div>
      </div>
    </Transition>

    <!-- 移动端历史抽屉 -->
    <Transition name="drawer-left">
      <div v-if="showHistoryDrawer" class="md:hidden fixed inset-0 z-40">
        <div class="absolute inset-0 bg-ink-950/10 backdrop-blur-sm" @click="showHistoryDrawer = false"></div>
        <div class="absolute left-0 top-0 w-[85vw] max-w-[320px] md:max-w-[400px] h-full bg-white/95 backdrop-blur-xl border-r border-border-dark flex flex-col shadow-xl">
          <div class="flex items-center justify-between p-3 border-b border-border-dark shrink-0">
            <span class="font-bold text-sm uppercase tracking-wider">历史记录</span>
            <button @click="showHistoryDrawer = false" class="text-ink-500 hover:text-ink-950">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <MainSidebar class="flex flex-col flex-1 !w-auto !border-0 overflow-hidden" :hide-logo="true" />
        </div>
        <div class="flex-1 bg-ink-950/10 backdrop-blur-sm" @click="showHistoryDrawer = false" />
      </div>
    </Transition>

    <!-- 创作记录右侧抽屉 -->
    <Transition name="drawer">
      <div v-if="appStore.showCreationRecords" class="fixed inset-0 z-50" @click.self="appStore.closeCreationRecords()">
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-ink-950/10 backdrop-blur-sm" @click="appStore.closeCreationRecords()"></div>
        <!-- 抽屉面板 -->
        <div class="absolute right-0 top-0 w-[85vw] md:w-[60vw] lg:w-[50vw] xl:w-[40vw] h-full flex flex-col bg-white/95 backdrop-blur-xl border-l border-border-dark shadow-xl">
          <CreationRecordList />
        </div>
      </div>
    </Transition>

    <!-- 模板列表抽屉 -->
    <Transition name="drawer">
      <div v-if="appStore.showTemplateDrawer" class="fixed inset-0 z-50" @click.self="appStore.closeTemplateDrawer()">
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-ink-950/10 backdrop-blur-sm" @click="appStore.closeTemplateDrawer()"></div>
        <!-- 抽屉面板 -->
        <div class="absolute right-0 top-0 w-[85vw] md:w-[60vw] lg:w-[50vw] xl:w-[40vw] h-full flex flex-col bg-white/95 backdrop-blur-xl border-l border-border-dark shadow-xl">
          <TemplateDrawer />
        </div>
      </div>
    </Transition>

    <!-- 模型选择器弹窗 -->
    <div
      v-if="showModelSelector"
      class="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/10 p-4 xs:p-6 md:p-8 backdrop-blur-sm"
      @click.self="showModelSelector = false">
      <div class="w-full max-w-full xs:max-w-2xl md:max-w-3xl max-h-[90vh] overflow-y-auto custom-scrollbar">
        <ModelSelector
          :current-model="generatorStore.model"
          :attachments="generatorStore.attachments"
          @select="handleModelSelect"
          @close="showModelSelector = false"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import MainSidebar from '../components/sidebar/MainSidebar.vue'
import SettingsSidebar from '../components/sidebar/SettingsSidebar.vue'
import TopHeader from '../components/layout/TopHeader.vue'
import MessageItem from '../components/chat/MessageItem.vue'
import ChatInputBar from '../components/chat/ChatInputBar.vue'
import ModelSelector from '../components/ModelSelector.vue'
import CaseDetailPanel from '../components/cases/CaseDetailPanel.vue'
import CreationDetailPanel from '../components/creation/CreationDetailPanel.vue'
import CreationRecordList from '../components/creation/CreationRecordList.vue'
import NotificationCarousel from '../components/NotificationCarousel.vue'
import TemplateDrawer from '../components/cases/TemplateDrawer.vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAppStore } from '@/store/useAppStore'

const generatorStore = useGeneratorStore()
const appStore = useAppStore()

const showModelSelector = ref(false)
const showSettingsDrawer = ref(false)
const showHistoryDrawer = ref(false)

const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value < 1024)

// 拖拽调整侧边栏宽度
const sidebarWidth = ref(parseInt(localStorage.getItem('sidebarWidth') || '280'))
const sidebarMinWidth = 200
const sidebarMaxWidth = 500
let isResizing = false

// 监听 sidebarWidth 变化并保存到 localStorage
watch(sidebarWidth, (newWidth) => {
  localStorage.setItem('sidebarWidth', newWidth.toString())
})

const startResize = (e) => {
  isResizing = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'

  // 创建遮罩层以防止拖拽时的干扰
  const overlay = document.createElement('div')
  overlay.className = 'fixed inset-0 z-50 resize-overlay'
  document.body.appendChild(overlay)

  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  e.preventDefault()
}

const onResize = (e) => {
  if (!isResizing) return
  const newWidth = window.innerWidth - e.clientX
  sidebarWidth.value = Math.min(sidebarMaxWidth, Math.max(sidebarMinWidth, newWidth))
}

const stopResize = () => {
  isResizing = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''

  // 移除遮罩层
  document.querySelector('.resize-overlay')?.remove()

  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

// 对话区域高度拖拽（通过 chatAreaStyle 控制，这里保持 flex-1 自动）
const chatAreaStyle = computed(() => ({}))
const chatAreaRef = ref(null)

function onWindowResize() { windowWidth.value = window.innerWidth }
onMounted(() => window.addEventListener('resize', onWindowResize))
onUnmounted(() => {
  window.removeEventListener('resize', onWindowResize)
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
})

// 处理模型选择
const handleModelSelect = (model) => {
  console.log('选择模型:', model)
  generatorStore.setSelectedModel(model.model_name)
  generatorStore.setSelectedModelInfo(model)
  showModelSelector.value = false

  // 保存到localStorage
  localStorage.setItem('selectedModel', JSON.stringify({
    modelName: model.model_name,
    modelInfo: model
  }))
}

// 组件挂载时恢复模型选择
onMounted(() => {
  try {
    const savedModel = localStorage.getItem('selectedModel')
    if (savedModel) {
      const data = JSON.parse(savedModel)
      generatorStore.setSelectedModel(data.modelName)
      generatorStore.setSelectedModelInfo(data.modelInfo)
      console.log('恢复模型选择:', data.modelName)
    }
  } catch (error) {
    console.error('恢复模型选择失败:', error)
  }

  // Fetch available models
  generatorStore.fetchAvailableModels()
})
</script>

<style scoped>
/* 右侧抽屉 */
.drawer-enter-active, .drawer-leave-active {
  transition: opacity 0.25s ease;
}
.drawer-enter-active > div:last-child,
.drawer-leave-active > div:last-child {
  transition: transform 0.25s ease;
}
.drawer-enter-from, .drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from > div:last-child,
.drawer-leave-to > div:last-child {
  transform: translateX(100%);
}

/* 左侧抽屉 */
.drawer-left-enter-active, .drawer-left-leave-active {
  transition: opacity 0.25s ease;
}
.drawer-left-enter-active > div:first-child,
.drawer-left-leave-active > div:first-child {
  transition: transform 0.25s ease;
}
.drawer-left-enter-from, .drawer-left-leave-to {
  opacity: 0;
}
.drawer-left-enter-from > div:first-child,
.drawer-left-leave-to > div:first-child {
  transform: translateX(-100%);
}

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #d1d8d3; border-radius: 10px; }

/* 侧边栏调整大小遮罩 */
.resize-overlay {
  background: transparent;
  cursor: col-resize;
}
</style>
