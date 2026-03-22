<template>
  <div class="h-screen flex overflow-hidden bg-background-dark text-ink-950 font-display">
    <!-- 左侧导航 (hidden on mobile) -->
    <MainSidebar
      :class="['hidden md:flex']"
      @openHistory="showHistoryDrawer = true"
      @settingsDrawerChange="showSettingsOverlay = $event"
      ref="mainSidebarRef"
    />

    <!-- 遮罩层 (当设置抽屉打开时显示) -->
    <Transition name="fade">
      <div
        v-if="showSettingsOverlay"
        @click="closeSettingsDrawer"
        class="fixed inset-0 bg-ink-950/10 backdrop-blur-sm z-40">
      </div>
    </Transition>

    <!-- 主交互区 - View Container -->
    <component
      :is="currentViewComponent"
      @openModelSelector="showModelSelector = true"
      @openHistory="showHistoryDrawer = true"
      @openTemplates="appStore.toggleTemplateDrawer()"
    />

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

    <!-- 桌面端历史记录抽屉 -->
    <Transition name="drawer-left">
      <div v-if="showHistoryDrawer" class="hidden md:flex fixed inset-0 z-40">
        <div class="absolute inset-0 bg-ink-950/10 backdrop-blur-sm" @click="showHistoryDrawer = false"></div>
        <div class="absolute left-0 top-0 w-[400px] h-full bg-white/95 backdrop-blur-xl border-r border-border-dark shadow-2xl flex flex-col">
          <div class="flex items-center justify-between p-4 border-b border-border-dark shrink-0">
            <span class="font-bold text-sm uppercase tracking-wider">历史记录</span>
            <button @click="showHistoryDrawer = false" class="text-ink-500 hover:text-ink-950">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <CreationRecordList />
        </div>
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

    <!-- 用户资料弹窗 -->
    <ProfileModal
      v-if="appStore.showProfileModal"
      @close="appStore.showProfileModal = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import MainSidebar from '../components/sidebar/MainSidebar.vue'
import LandingView from './LandingView.vue'
import ChatView from './ChatView.vue'
import ModelSelector from '../components/ModelSelector.vue'
import CreationRecordList from '../components/creation/CreationRecordList.vue'
import TemplateDrawer from '../components/cases/TemplateDrawer.vue'
import ProfileModal from '../components/layout/ProfileModal.vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAppStore } from '@/store/useAppStore'

const generatorStore = useGeneratorStore()
const appStore = useAppStore()

const showModelSelector = ref(false)
const showHistoryDrawer = ref(false)
const showSettingsOverlay = ref(false)
const mainSidebarRef = ref(null)

// Restore menu selection based on current view
const restoreMenuSelection = () => {
  if (appStore.currentView === 'landing') {
    appStore.selectedMenuItem = 'landing'
  } else if (appStore.currentView === 'chat') {
    appStore.selectedMenuItem = 'generate'
  }
}

// Watch history drawer state to restore menu selection when drawer closes
watch(() => showHistoryDrawer.value, (newVal, oldVal) => {
  // When drawer closes (true -> false)
  if (oldVal === true && newVal === false) {
    restoreMenuSelection()
  }
})

// View switching logic
const currentViewComponent = computed(() => {
  return appStore.currentView === 'landing' ? LandingView : ChatView
})

// Close settings drawer
const closeSettingsDrawer = () => {
  showSettingsOverlay.value = false
  // Notify MainSidebar to close the drawer
  if (mainSidebarRef.value) {
    mainSidebarRef.value.closeSettingsDrawer()
  }
}

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

/* 右侧抽屉 (模板、创作记录) */
.drawer-enter-active, .drawer-leave-active {
  transition: opacity 0.3s ease;
}
.drawer-enter-active > div:last-child,
.drawer-leave-active > div:last-child {
  transition: transform 0.3s ease;
}
.drawer-enter-from, .drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from > div:last-child,
.drawer-leave-to > div:last-child {
  transform: translateX(100%);
}

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #d1d8d3; border-radius: 10px; }

/* Fade animation for overlay */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
.fade-enter-to, .fade-leave-from {
  opacity: 1;
}
</style>
