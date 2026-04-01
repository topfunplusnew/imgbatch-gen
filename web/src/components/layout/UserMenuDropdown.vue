<template>
  <el-dropdown trigger="click" placement="top-start" @command="handleCommand">
    <div class="user-menu-trigger">
      <div class="user-menu-trigger__avatar">{{ userInitial }}</div>
      <div class="min-w-0 flex-1 text-left">
        <p class="truncate text-sm font-semibold text-ink-950">{{ displayName }}</p>
        <p class="truncate text-xs text-ink-500">{{ displayEmail }}</p>
      </div>
      <span class="material-symbols-outlined !text-xl text-ink-500 shrink-0">expand_more</span>
    </div>

    <template #dropdown>
      <el-dropdown-menu class="user-menu-dropdown">
        <el-dropdown-item command="profile">
          <span class="material-symbols-outlined !text-lg">person</span>
          <span>个人资料</span>
        </el-dropdown-item>
        <el-dropdown-item v-if="!props.hideUserCenter" command="user-center">
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
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/useAuthStore'
import { useAppStore } from '@/store/useAppStore'
import { useNotificationStore } from '@/store/useNotificationStore'

const props = defineProps({
  hideUserCenter: { type: Boolean, default: false }
})

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()
const notificationStore = useNotificationStore()

const displayName = computed(() => {
  return authStore.userName || authStore.userEmail || authStore.userPhone || '用户'
})

const displayEmail = computed(() => {
  return authStore.userEmail || authStore.userPhone || ''
})

const userInitial = computed(() => {
  return displayName.value.charAt(0).toUpperCase()
})

function goToProfile() {
  appStore.showProfileModal = true
}

function goToUserCenter() {
  router.push('/user-center')
}

function goToAdmin() {
  router.push('/admin')
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

const handleCommand = (command) => {
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
</script>

<style scoped>
.user-menu-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(255, 253, 252, 0.86);
  transition: background-color 0.2s ease;
  cursor: pointer;
  outline: none;
}

.user-menu-trigger:hover {
  background: rgba(140, 42, 46, 0.06);
}

.user-menu-trigger__avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-deep));
  color: white;
  font-size: 15px;
  font-weight: 700;
  flex-shrink: 0;
}
</style>
