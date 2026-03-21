<script setup>
import { computed, onMounted, onUnmounted, watch, ref } from 'vue'
import { useAppStore } from './store/useAppStore'
import { useAuthStore } from './store/useAuthStore'
import { useNotificationStore } from './store/useNotificationStore'
import ImageStudio from './views/ImageStudio.vue'
import Login from './views/Login.vue'
import UserCenter from './views/UserCenter.vue'
import AdminPanel from './views/AdminPanel.vue'
import NotificationContainer from './components/NotificationContainer.vue'
import ProfileModal from './components/layout/ProfileModal.vue'
import AnnouncementPopup from './components/AnnouncementPopup.vue'

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

  // 监听页面可见性变化
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

// 监听用户登录状态，管理 SSE 连接
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    // 用户已登录，建立 SSE 连接
    console.log('[App] User authenticated, connecting SSE...')
    notificationStore.connectSSE()

    // 请求浏览器通知权限
    notificationStore.requestNotificationPermission()

    // 加载未读数量
    notificationStore.fetchUnreadCount().catch(err => {
      console.error('Failed to fetch unread count:', err)
    })
  } else {
    // 用户未登录，断开 SSE 连接
    console.log('[App] User not authenticated, disconnecting SSE...')
    notificationStore.disconnectSSE()
  }
}, { immediate: true })

// 处理页面可见性变化
function handleVisibilityChange() {
  if (document.hidden) {
    // 页面隐藏时不断开连接，保持SSE活跃
    console.log('[App] Page hidden, keeping SSE connection')
  } else {
    // 页面显示时，如果未连接则重新连接
    if (authStore.isAuthenticated && !notificationStore.sseConnected) {
      console.log('[App] Page visible, reconnecting SSE...')
      notificationStore.connectSSE()
    }
  }
}

// 组件卸载时清理
onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  // 注意：不在这里断开SSE，因为用户可能只是切换标签页
  // SSE连接应该只在用户登出时断开
})

const currentComponent = computed(() => {
  switch (appStore.currentPage) {
    case 'agent':
      return ImageStudio
    case 'login':
      return Login
    case 'user-center':
      return UserCenter
    case 'admin':
      return AdminPanel
    default:
      return ImageStudio
  }
})
</script>

<template>
  <component :is="currentComponent" />
  <NotificationContainer />
  <ProfileModal />
  <AnnouncementPopup />
</template>

<style scoped>
</style>
