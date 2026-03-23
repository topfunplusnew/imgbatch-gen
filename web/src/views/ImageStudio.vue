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
      @openHistory="showHistoryDrawer = true"
      @openTemplates="appStore.toggleTemplateDrawer()"
      @toggleSettings="handleToggleSettings"
    />

    <!-- 历史记录居中弹窗 -->
    <Teleport to="body">
      <Transition name="panel">
        <div
          v-if="showHistoryDrawer"
          class="fixed inset-0 z-50 flex items-center justify-center">
          <!-- Backdrop -->
          <div
            class="absolute inset-0 bg-black/20 backdrop-blur-sm"
            @click="showHistoryDrawer = false"></div>
          <!-- Panel -->
          <div
            @click.stop
            class="relative w-[560px] max-w-[calc(100vw-32px)] bg-white border border-border-dark rounded-xl shadow-2xl overflow-hidden max-h-[85vh]">
            <CreationRecordList :onClose="() => showHistoryDrawer = false" />
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 创作记录居中弹窗 -->
    <Teleport to="body">
      <Transition name="panel">
        <div
          v-if="appStore.showCreationRecords"
          class="fixed inset-0 z-50 flex items-center justify-center">
          <!-- Backdrop -->
          <div
            class="absolute inset-0 bg-black/20 backdrop-blur-sm"
            @click="appStore.closeCreationRecords()"></div>
          <!-- Panel -->
          <div
            @click.stop
            class="relative w-[560px] max-w-[calc(100vw-32px)] bg-white border border-border-dark rounded-xl shadow-2xl overflow-hidden max-h-[85vh]">
            <CreationRecordList />
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 模板列表居中弹窗 -->
    <Teleport to="body">
      <Transition name="panel">
        <div
          v-if="appStore.showTemplateDrawer"
          class="fixed inset-0 z-50 flex items-center justify-center">
          <!-- Backdrop -->
          <div
            class="absolute inset-0 bg-black/20 backdrop-blur-sm"
            @click="appStore.closeTemplateDrawer()"></div>
          <!-- Panel -->
          <div
            @click.stop
            class="relative w-[700px] max-w-[calc(100vw-32px)] bg-white border border-border-dark rounded-xl shadow-2xl overflow-hidden max-h-[85vh]">
            <TemplateDrawer />
          </div>
        </div>
      </Transition>
    </Teleport>

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
import CreationRecordList from '../components/creation/CreationRecordList.vue'
import TemplateDrawer from '../components/cases/TemplateDrawer.vue'
import ProfileModal from '../components/layout/ProfileModal.vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAppStore } from '@/store/useAppStore'

const generatorStore = useGeneratorStore()
const appStore = useAppStore()

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

// Toggle settings drawer
const handleToggleSettings = () => {
  showSettingsOverlay.value = !showSettingsOverlay.value
  // Notify MainSidebar to toggle the drawer
  if (mainSidebarRef.value) {
    if (showSettingsOverlay.value) {
      mainSidebarRef.value.toggleSettingsDrawer()
    } else {
      mainSidebarRef.value.closeSettingsDrawer()
    }
  }
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
/* Panel transition */
.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.2s ease;
}
.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}
.panel-enter-to,
.panel-leave-from {
  opacity: 1;
}

/* Scale animation for the panel content */
.panel-enter-active > div > div:last-child,
.panel-leave-active > div > div:last-child {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.panel-enter-from > div > div:last-child,
.panel-leave-to > div > div:last-child {
  transform: scale(0.95);
  opacity: 0;
}
.panel-enter-to > div > div:last-child,
.panel-leave-from > div > div:last-child {
  transform: scale(1);
  opacity: 1;
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
