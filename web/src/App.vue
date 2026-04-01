<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from './store/useAuthStore'
import { useNotificationStore } from './store/useNotificationStore'
import NotificationContainer from './components/NotificationContainer.vue'
import ProfileModal from './components/layout/ProfileModal.vue'
import AnnouncementPopup from './components/AnnouncementPopup.vue'
import { useAppStore } from './store/useAppStore'

// 开发模式导入调试工具
if (import.meta.env.DEV) {
  import('./utils/notification-debug')
}

const appStore = useAppStore()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

// 初始化认证状态
onMounted(() => {
  authStore.init()
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

// 监听用户登录状态，管理 SSE 连接
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    notificationStore.connectSSE()
    notificationStore.requestNotificationPermission()
    notificationStore.fetchUnreadCount().catch(err => {
      console.error('Failed to fetch unread count:', err)
    })
  } else {
    notificationStore.disconnectSSE()
  }
}, { immediate: true })

function handleVisibilityChange() {
  if (!document.hidden && authStore.isAuthenticated && !notificationStore.sseConnected) {
    notificationStore.connectSSE()
  }
}

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<template>
  <router-view />
  <NotificationContainer />
  <ProfileModal v-if="appStore.showProfileModal" @close="appStore.showProfileModal = false" />
  <AnnouncementPopup />
</template>
