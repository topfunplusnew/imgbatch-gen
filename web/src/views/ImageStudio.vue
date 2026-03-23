<template>
  <div class="h-screen flex overflow-hidden bg-background-dark text-ink-950 font-display">
    <!-- 左侧导航 (hidden on mobile) -->
    <MainSidebar
      @openHistory="showHistoryDrawer = true"
      @settingsDrawerChange="showSettingsOverlay = $event"
      ref="mainSidebarRef"
    />

    <Teleport to="body">
      <Transition name="mobile-sidebar">
        <div
          v-if="showMobileSidebar"
          class="fixed inset-0 z-[70] md:hidden"
        >
          <div
            class="absolute inset-0 bg-black/30 backdrop-blur-sm"
            @click="closeMobileSidebar"
          ></div>
          <div class="absolute left-0 top-0 h-full w-[88vw] max-w-[360px]">
            <MainSidebar
              mobile-drawer
              @openHistory="openHistoryFromSidebar"
              @requestClose="closeMobileSidebar"
            />
          </div>
        </div>
      </Transition>
    </Teleport>

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
      @openHistory="openHistoryFromView"
      @openTemplates="openTemplatesFromView"
      @toggleSettings="handleToggleSettings"
      @toggleSidebar="toggleMobileSidebar"
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
            class="relative w-[calc(100vw-8px)] xs:w-[calc(100vw-16px)] sm:w-[560px] md:w-[640px] lg:w-[700px] max-w-[calc(100vw-16px)] bg-white border border-border-dark rounded-xl shadow-2xl overflow-hidden max-h-[85vh]">
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
            class="relative w-[calc(100vw-8px)] xs:w-[calc(100vw-16px)] sm:w-[560px] md:w-[640px] lg:w-[700px] max-w-[calc(100vw-16px)] bg-white border border-border-dark rounded-xl shadow-2xl overflow-hidden max-h-[85vh]">
            <CreationRecordList />
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 模板列表居中弹窗 -->
    <Teleport to="body">
      <Transition name="template-drawer">
        <div
          v-if="appStore.showTemplateDrawer"
          class="fixed inset-0 z-50">
          <!-- Backdrop -->
          <div
            class="absolute inset-0 bg-black/20 backdrop-blur-sm"
            @click="appStore.closeTemplateDrawer()"></div>
          <!-- Drawer -->
          <div
            @click.stop
            class="absolute left-0 top-0 h-full w-[calc(100vw-16px)] max-w-[420px] xs:w-[360px] sm:w-[400px] md:w-[420px] bg-white border-r border-border-dark shadow-2xl overflow-hidden">
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
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
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
const showMobileSidebar = ref(false)
let mobileViewportQuery = null
let previousBodyOverflow = ''

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

watch(() => appStore.currentView, (view) => {
  closeMobileSidebar()
  if (view !== 'chat' && showSettingsOverlay.value) {
    closeSettingsDrawer()
  }
})

watch(() => appStore.showTemplateDrawer, (isOpen) => {
  if (isOpen) closeMobileSidebar()
})

watch(() => appStore.showCreationRecords, (isOpen) => {
  if (isOpen) closeMobileSidebar()
})

watch(() => appStore.selectedCase, (selectedCase) => {
  if (selectedCase) closeMobileSidebar()
})

watch(() => appStore.selectedCreation, (selectedCreation) => {
  if (selectedCreation) closeMobileSidebar()
})

watch(() => showHistoryDrawer.value, (isOpen) => {
  if (isOpen) closeMobileSidebar()
})

watch(showMobileSidebar, (isOpen) => {
  if (isOpen) {
    previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return
  }

  document.body.style.overflow = previousBodyOverflow
  previousBodyOverflow = ''
})

// View switching logic
const currentViewComponent = computed(() => {
  return appStore.currentView === 'landing' ? LandingView : ChatView
})

const toggleMobileSidebar = () => {
  showMobileSidebar.value = !showMobileSidebar.value
}

const closeMobileSidebar = () => {
  showMobileSidebar.value = false
}

const handleMobileViewportChange = (event) => {
  if (event.matches) {
    closeMobileSidebar()
  }
}

const openHistoryFromSidebar = () => {
  showHistoryDrawer.value = true
  closeMobileSidebar()
}

const openHistoryFromView = () => {
  showHistoryDrawer.value = true
  closeMobileSidebar()
}

const openTemplatesFromView = () => {
  appStore.toggleTemplateDrawer()
  closeMobileSidebar()
}

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
  closeMobileSidebar()
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
  mobileViewportQuery = window.matchMedia('(min-width: 768px)')
  if (mobileViewportQuery.matches) {
    closeMobileSidebar()
  }
  mobileViewportQuery.addEventListener('change', handleMobileViewportChange)

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

onUnmounted(() => {
  mobileViewportQuery?.removeEventListener('change', handleMobileViewportChange)
  document.body.style.overflow = previousBodyOverflow
  previousBodyOverflow = ''
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

.template-drawer-enter-active,
.template-drawer-leave-active {
  transition: opacity 0.25s ease;
}

.template-drawer-enter-from,
.template-drawer-leave-to {
  opacity: 0;
}

.template-drawer-enter-to,
.template-drawer-leave-from {
  opacity: 1;
}

.template-drawer-enter-active > div:last-child,
.template-drawer-leave-active > div:last-child {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.template-drawer-enter-from > div:last-child,
.template-drawer-leave-to > div:last-child {
  transform: translateX(-100%);
  opacity: 0;
}

.template-drawer-enter-to > div:last-child,
.template-drawer-leave-from > div:last-child {
  transform: translateX(0);
  opacity: 1;
}

.mobile-sidebar-enter-active,
.mobile-sidebar-leave-active {
  transition: opacity 0.25s ease;
}

.mobile-sidebar-enter-from,
.mobile-sidebar-leave-to {
  opacity: 0;
}

.mobile-sidebar-enter-to,
.mobile-sidebar-leave-from {
  opacity: 1;
}

.mobile-sidebar-enter-active > div:last-child,
.mobile-sidebar-leave-active > div:last-child {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.mobile-sidebar-enter-from > div:last-child,
.mobile-sidebar-leave-to > div:last-child {
  transform: translateX(-100%);
  opacity: 0;
}

.mobile-sidebar-enter-to > div:last-child,
.mobile-sidebar-leave-from > div:last-child {
  transform: translateX(0);
  opacity: 1;
}
</style>
