<template>
  <header class="h-12 xs:h-14 md:h-16 lg:h-16 border-b border-border-dark flex items-center justify-between px-3 xs:px-4 md:px-6 lg:px-8 bg-white/80 backdrop-blur-xl sticky top-0 z-10">
    <div class="flex items-center gap-2 md:gap-4 min-w-0">
      <button
        @click="$emit('toggleSidebar')"
        class="md:hidden flex items-center justify-center p-1.5 rounded-lg border border-border-dark bg-white/90 hover:bg-primary/5 text-ink-700 min-h-[44px] min-w-[44px]"
        aria-label="Open sidebar">
        <span class="material-symbols-outlined !text-xl">menu</span>
      </button>

      <!-- Back to Home button (shown in chat view) -->
      <button
        v-if="appStore.currentView === 'chat'"
        @click="appStore.setCurrentView('landing')"
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border-dark bg-white/90 hover:bg-primary/5 text-ink-700 transition-colors min-h-[44px] min-w-[44px]"
        title="返回首页">
        <span class="material-symbols-outlined !text-lg">home</span>
        <span class="hidden sm:inline">返回首页</span>
      </button>

      <div class="hidden xs:flex items-center gap-2 min-w-0">
        <span class="text-sm font-medium text-slate-500 shrink-0">当前会话:</span>
        <span class="text-sm font-semibold truncate">{{ generatorStore.currentSessionTitle }}</span>
      </div>
    </div>

    <div class="flex items-center gap-1.5 xs:gap-2 md:gap-4">
      <!-- 通知按钮（已登录时显示） -->
      <NotificationButton
        v-if="authStore.isAuthenticated"
        class="hidden md:flex"
        :unread-count="notificationStore.unreadCount"
        :active="showNotifications"
        @toggle="toggleNotifications"
      />

      <!-- 移动端操作按钮组 -->
      <button
        @click="$emit('toggleSettings')"
        class="flex items-center justify-center p-1.5 rounded-lg border border-border-dark bg-white/90 hover:bg-primary/5 text-ink-700 min-h-[44px] min-w-[44px]"
        aria-label="Open settings">
        <span class="material-symbols-outlined !text-xl">tune</span>
      </button>


      <!-- 用户菜单（仅在移动端显示） -->
      <!-- 未登录：显示登录按钮 -->
      <button
        v-if="!authStore.isAuthenticated"
        @click="goToLogin"
        class="hidden md:flex lg:hidden items-center gap-1.5 xs:gap-2 px-2.5 xs:px-3 py-1.5 bg-white rounded-full shadow-sm border border-border-dark hover:shadow-md transition-all min-h-[44px]">
        <div class="w-7 h-7 xs:w-8 xs:h-8 rounded-full bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined !text-base xs:!text-lg text-white">login</span>
        </div>
        <span class="text-xs xs:text-sm font-medium text-ink-950 hidden sm:inline">登录</span>
      </button>

      <!-- 已登录：显示用户头像按钮（仅移动端） -->
      <button
        v-else
        @click="showUserMenu = !showUserMenu"
        class="hidden md:flex lg:hidden items-center gap-1.5 xs:gap-2 px-2 xs:px-2.5 py-1.5 bg-white rounded-full shadow-sm border border-border-dark hover:shadow-md transition-all min-h-[44px]">
        <div class="w-7 h-7 xs:w-8 xs:h-8 rounded-full bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center text-white font-medium text-xs xs:text-sm shrink-0">
          {{ userInitial }}
        </div>
        <span class="text-xs xs:text-sm font-medium text-ink-950 max-w-[60px] xs:max-w-[100px] truncate hidden sm:inline">{{ displayName }}</span>
        <span class="material-symbols-outlined !text-base xs:!text-lg text-ink-500 hidden sm:inline">expand_more</span>
      </button>
    </div>
  </header>

  <!-- 用户菜单下拉（仅移动端） -->
  <div
    v-if="showUserMenu"
    @click="showUserMenu = false"
    class="fixed inset-0 z-50">
  </div>

  <!-- 用户下拉菜单内容（仅移动端） -->
  <transition
    enter-active-class="transition ease-out duration-200"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition ease-in duration-150"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95">
    <div
      v-if="showUserMenu && authStore.isAuthenticated"
      class="lg:hidden fixed top-14 xs:top-16 right-3 xs:right-4 z-50 w-48 bg-white rounded-xl shadow-xl border border-border-dark overflow-hidden">
      <!-- 用户信息头部 -->
      <div class="px-4 py-3 bg-primary-soft border-b border-border-dark">
        <p class="text-sm font-medium text-ink-950 truncate">{{ displayName }}</p>
        <p class="text-xs text-ink-500 truncate">{{ displayEmail }}</p>
      </div>

      <!-- 菜单项 -->
      <div class="py-1">
        <button
          @click="goToProfile"
          class="w-full px-4 py-2.5 text-left text-sm text-ink-700 hover:bg-primary/5 flex items-center gap-2"
        >
          <span class="material-symbols-outlined !text-lg">person</span>
          个人资料
        </button>
        <button
          @click="goToUserCenter"
          class="w-full px-4 py-2.5 text-left text-sm text-ink-700 hover:bg-primary/5 flex items-center gap-2"
        >
          <span class="material-symbols-outlined !text-lg">settings</span>
          账户设置
        </button>
        <!-- 管理后台入口（仅管理员可见） -->
        <button
          v-if="authStore.userRole === 'admin'"
          @click="goToAdmin"
          class="w-full px-4 py-2.5 text-left text-sm text-purple-600 hover:bg-purple-50 flex items-center gap-2"
        >
          <span class="material-symbols-outlined !text-lg">admin_panel_settings</span>
          管理后台
        </button>
        <div class="border-t border-border-dark my-1"></div>
        <button
          @click="handleLogout"
          class="w-full px-4 py-2.5 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
        >
          <span class="material-symbols-outlined !text-lg">logout</span>
          退出登录
        </button>
      </div>
    </div>
  </transition>

  <!-- 通知面板下拉 -->
  <div
    v-if="showNotifications"
    @click="showNotifications = false"
    class="fixed inset-0 z-50">
  </div>

  <transition
    enter-active-class="transition ease-out duration-200"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition ease-in duration-150"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95">
    <div
      v-if="showNotifications"
      class="fixed top-14 xs:top-16 right-16 xs:right-20 md:right-24 lg:right-28 z-50">
      <NotificationPanel @close="showNotifications = false" />
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAuthStore } from '@/store/useAuthStore'
import { useAppStore } from '@/store/useAppStore'
import { useNotificationStore } from '@/store/useNotificationStore'
import NotificationButton from '@/components/NotificationButton.vue'
import NotificationPanel from '@/components/NotificationPanel.vue'

const generatorStore = useGeneratorStore()
const authStore = useAuthStore()
const appStore = useAppStore()
const notificationStore = useNotificationStore()

const emit = defineEmits(['toggleSettings', 'openHistory', 'openTemplates', 'toggleSidebar'])

// 通知面板状态
const showNotifications = ref(false)

// 用户菜单状态
const showUserMenu = ref(false)

// 显示的用户名
const displayName = computed(() => {
  return authStore.userName || authStore.userEmail || authStore.userPhone || '用户'
})

// 显示的邮箱/手机号
const displayEmail = computed(() => {
  return authStore.userEmail || authStore.userPhone || ''
})

// 用户名首字母（头像）
const userInitial = computed(() => {
  const name = displayName.value
  return name.charAt(0).toUpperCase()
})

function goToLogin() {
  appStore.goToLogin()
}

function goToUserCenter() {
  showUserMenu.value = false
  appStore.setCurrentPage('user-center')
}

function goToAdmin() {
  showUserMenu.value = false
  appStore.setCurrentPage('admin')
}

function goToProfile() {
  showUserMenu.value = false
  appStore.showProfileModal = true
}

async function handleLogout() {
  showUserMenu.value = false
  if (confirm('确定要退出登录吗？')) {
    await authStore.logout()
    // 断开SSE连接
    notificationStore.disconnectSSE()
  }
}

// 切换通知面板
function toggleNotifications() {
  showNotifications.value = !showNotifications.value
  // 关闭用户菜单
  if (showNotifications.value) {
    showUserMenu.value = false
  }
}

// 初始化通知系统
onMounted(async () => {
  if (authStore.isAuthenticated) {
    // 获取未读数量
    try {
      await notificationStore.fetchUnreadCount()
    } catch (error) {
      console.error('获取未读数量失败:', error)
    }
  }
})
</script>
