<template>
  <header class="top-header">
    <div class="flex min-w-0 items-center gap-2 md:gap-4">
      <el-button
        circle
        class="md:hidden"
        @click="$emit('toggleSidebar')"
        aria-label="Open sidebar"
      >
        <span class="material-symbols-outlined !text-xl">menu</span>
      </el-button>

      <el-button
        v-if="appStore.currentView !== 'landing'"
        class="top-header__home-btn"
        @click="appStore.setCurrentView('landing')"
      >
        <span class="material-symbols-outlined !text-lg">home</span>
        <span class="hidden sm:inline">返回首页</span>
      </el-button>

      <div v-if="appStore.currentView === 'chat'" class="hidden min-w-0 xs:flex xs:items-center xs:gap-2">
        <span class="shrink-0 text-sm font-medium text-slate-500">当前会话</span>
        <el-tag effect="plain" round class="max-w-[260px] truncate">
          {{ generatorStore.currentSessionTitle }}
        </el-tag>
      </div>

      <div v-else-if="appStore.currentView === 'templates'" class="hidden min-w-0 xs:flex xs:items-center xs:gap-2">
        <span class="shrink-0 text-sm font-medium text-slate-500">当前页面</span>
        <el-tag effect="plain" round class="max-w-[260px] truncate">
          模版列表
        </el-tag>
      </div>
    </div>

    <div class="flex items-center gap-2 md:gap-3">
      <el-popover
        v-if="authStore.isAuthenticated"
        v-model:visible="showNotifications"
        trigger="click"
        placement="bottom-end"
        :width="340"
        popper-class="top-header-notification-popover"
      >
        <template #reference>
          <el-badge
            :value="notificationBadgeValue"
            :hidden="notificationStore.unreadCount === 0"
            class="hidden md:inline-flex"
          >
            <el-button circle :type="showNotifications ? 'primary' : 'default'" :plain="!showNotifications">
              <span class="material-symbols-outlined !text-xl">notifications</span>
            </el-button>
          </el-badge>
        </template>
        <NotificationPanel @close="showNotifications = false" />
      </el-popover>

      <el-button
        v-if="appStore.currentView === 'chat'"
        circle
        @click="$emit('toggleSettings')"
        aria-label="Open settings"
      >
        <span class="material-symbols-outlined !text-xl">tune</span>
      </el-button>

      <el-button
        v-if="!authStore.isAuthenticated"
        class="hidden md:inline-flex lg:hidden"
        @click="goToLogin"
      >
        <span class="material-symbols-outlined !text-lg text-primary">login</span>
        <span class="hidden sm:inline">登录</span>
      </el-button>

      <el-dropdown
        v-else
        trigger="click"
        class="hidden md:inline-flex lg:hidden"
        @command="handleUserCommand"
      >
        <div class="top-header__user-trigger">
          <div class="top-header__avatar">{{ userInitial }}</div>
          <div class="hidden min-w-0 sm:block">
            <div class="max-w-[108px] truncate text-sm font-semibold text-ink-950">{{ displayName }}</div>
            <div class="max-w-[108px] truncate text-xs text-ink-500">{{ displayEmail }}</div>
          </div>
          <span class="material-symbols-outlined !text-lg text-ink-500 hidden sm:inline">expand_more</span>
        </div>

        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <span class="material-symbols-outlined !text-lg">person</span>
              <span>个人资料</span>
            </el-dropdown-item>
            <el-dropdown-item command="user-center">
              <span class="material-symbols-outlined !text-lg">settings</span>
              <span>账户设置</span>
            </el-dropdown-item>
            <el-dropdown-item v-if="authStore.userRole === 'admin'" command="admin">
              <span class="material-symbols-outlined !text-lg">admin_panel_settings</span>
              <span>管理后台</span>
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <span class="material-symbols-outlined !text-lg">logout</span>
              <span>退出登录</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAuthStore } from '@/store/useAuthStore'
import { useAppStore } from '@/store/useAppStore'
import { useNotificationStore } from '@/store/useNotificationStore'
import NotificationPanel from '@/components/NotificationPanel.vue'

const generatorStore = useGeneratorStore()
const authStore = useAuthStore()
const appStore = useAppStore()
const notificationStore = useNotificationStore()

defineEmits(['toggleSettings', 'openHistory', 'openTemplates', 'toggleSidebar'])

const showNotifications = ref(false)

const displayName = computed(() => {
  return authStore.userName || authStore.userEmail || authStore.userPhone || '用户'
})

const displayEmail = computed(() => {
  return authStore.userEmail || authStore.userPhone || ''
})

const userInitial = computed(() => {
  return displayName.value.charAt(0).toUpperCase()
})

const notificationBadgeValue = computed(() => {
  return notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount
})

function goToLogin() {
  appStore.goToLogin()
}

function goToUserCenter() {
  appStore.setCurrentPage('user-center')
}

function goToAdmin() {
  appStore.setCurrentPage('admin')
}

function goToProfile() {
  appStore.showProfileModal = true
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
      type: 'warning',
      confirmButtonText: '退出',
      cancelButtonText: '取消'
    })
    await authStore.logout()
    notificationStore.disconnectSSE()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('退出登录失败:', error)
    }
  }
}

const handleUserCommand = (command) => {
  if (command === 'profile') {
    goToProfile()
    return
  }
  if (command === 'user-center') {
    goToUserCenter()
    return
  }
  if (command === 'admin') {
    goToAdmin()
    return
  }
  if (command === 'logout') {
    handleLogout()
  }
}

onMounted(async () => {
  if (authStore.isAuthenticated) {
    try {
      await notificationStore.fetchUnreadCount()
    } catch (error) {
      console.error('获取未读数量失败:', error)
    }
  }
})
</script>

<style scoped>
.top-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 16px;
  border-bottom: 1px solid var(--color-border-dark);
  background: rgba(255, 252, 251, 0.78);
  backdrop-filter: blur(18px);
  position: sticky;
  top: 0;
  z-index: 15;
}

@media (min-width: 768px) {
  .top-header {
    padding: 0 24px;
  }
}

.top-header__home-btn {
  border-radius: 999px;
}

.top-header__user-trigger {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px 6px 8px;
  border: 1px solid var(--color-border-dark);
  border-radius: 999px;
  background: rgba(255, 253, 252, 0.9);
  cursor: pointer;
  outline: none;
}

.top-header__avatar {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-deep));
  color: white;
  font-size: 13px;
  font-weight: 700;
}
</style>
