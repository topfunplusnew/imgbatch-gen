<template>
  <el-container class="image-studio-shell">
    <el-aside width="clamp(224px, 18vw, 256px)" class="image-studio-shell__aside hidden md:block">
      <MainSidebar
        ref="mainSidebarRef"
        @settingsDrawerChange="showSettingsOverlay = $event"
      />
    </el-aside>

    <Transition name="fade">
      <div
        v-if="showSettingsOverlay"
        class="fixed inset-0 z-40 bg-ink-950/10 backdrop-blur-sm"
        @click="closeSettingsDrawer"
      ></div>
    </Transition>

    <el-container class="image-studio-shell__main">
      <component
        :is="currentViewComponent"
        @toggleSettings="handleToggleSettings"
        @toggleSidebar="toggleMobileSidebar"
      />
    </el-container>

    <el-drawer
      v-model="showMobileSidebar"
      direction="ltr"
      :with-header="false"
      size="88vw"
      append-to-body
      modal-class="studio-mobile-sidebar-mask"
      class="studio-mobile-sidebar"
    >
      <MainSidebar
        mobile-drawer
        @requestClose="closeMobileSidebar"
      />
    </el-drawer>

    <ProfileModal
      v-if="appStore.showProfileModal"
      @close="appStore.showProfileModal = false"
    />
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import MainSidebar from '../components/sidebar/MainSidebar.vue'
import LandingView from './LandingView.vue'
import ChatView from './ChatView.vue'
import TemplateListView from './TemplateListView.vue'
import ProfileModal from '../components/layout/ProfileModal.vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAppStore } from '@/store/useAppStore'
import { isSelectableFrontendModel } from '@/utils/modelSelection'

const generatorStore = useGeneratorStore()
const appStore = useAppStore()

const showSettingsOverlay = ref(false)
const mainSidebarRef = ref(null)
const showMobileSidebar = ref(false)
let mobileViewportQuery = null
let previousBodyOverflow = ''

watch(
  () => appStore.currentView,
  (view) => {
    closeMobileSidebar()
    if (view !== 'chat' && showSettingsOverlay.value) {
      closeSettingsDrawer()
    }
  }
)

watch(
  () => appStore.selectedCase,
  (selectedCase) => {
    if (selectedCase) closeMobileSidebar()
  }
)

watch(
  () => appStore.selectedCreation,
  (selectedCreation) => {
    if (selectedCreation) closeMobileSidebar()
  }
)

watch(showMobileSidebar, (isOpen) => {
  if (isOpen) {
    previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return
  }

  document.body.style.overflow = previousBodyOverflow
  previousBodyOverflow = ''
})

const currentViewComponent = computed(() => {
  if (appStore.currentView === 'landing') {
    return LandingView
  }

  if (appStore.currentView === 'templates') {
    return TemplateListView
  }

  return ChatView
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

const closeSettingsDrawer = () => {
  showSettingsOverlay.value = false
  if (mainSidebarRef.value) {
    mainSidebarRef.value.closeSettingsDrawer()
  }
}

const handleToggleSettings = () => {
  closeMobileSidebar()
  showSettingsOverlay.value = !showSettingsOverlay.value
  if (mainSidebarRef.value) {
    if (showSettingsOverlay.value) {
      mainSidebarRef.value.toggleSettingsDrawer()
    } else {
      mainSidebarRef.value.closeSettingsDrawer()
    }
  }
}

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
      const restoredModel = {
        ...(data.modelInfo || {}),
        model_name: data.modelName || data.modelInfo?.model_name,
      }

      if (isSelectableFrontendModel(restoredModel)) {
        generatorStore.setSelectedModel(restoredModel.model_name)
        generatorStore.setSelectedModelInfo(data.modelInfo || null)
        console.log('恢复模型选择:', restoredModel.model_name)
      } else {
        localStorage.removeItem('selectedModel')
      }
    }
  } catch (error) {
    console.error('恢复模型选择失败:', error)
  }

  generatorStore.fetchAvailableModels()
})

onUnmounted(() => {
  mobileViewportQuery?.removeEventListener('change', handleMobileViewportChange)
  document.body.style.overflow = previousBodyOverflow
  previousBodyOverflow = ''
})
</script>

<style scoped>
.image-studio-shell {
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(140, 42, 46, 0.1), transparent 28%),
    linear-gradient(180deg, rgba(255, 252, 251, 0.86) 0%, rgba(246, 239, 238, 0.96) 100%);
}

.image-studio-shell__aside {
  height: 100vh;
  position: relative;
  z-index: 20;
  background: rgba(255, 253, 252, 0.78);
  backdrop-filter: blur(18px);
  border-right: 1px solid var(--color-border-dark);
}

.image-studio-shell__main {
  min-width: 0;
  height: 100vh;
  overflow: hidden;
}

.studio-mobile-sidebar :deep(.el-drawer) {
  width: min(360px, 88vw) !important;
  border-radius: 0 24px 24px 0;
}

.studio-mobile-sidebar :deep(.el-drawer__body) {
  padding: 0;
  height: 100%;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
}
</style>
