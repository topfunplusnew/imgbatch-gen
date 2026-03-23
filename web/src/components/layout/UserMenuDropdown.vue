<template>
  <div class="relative">
    <!-- 用户信息按钮 -->
    <button
      @click="showMenu = !showMenu"
      class="w-full flex items-center gap-3 px-3 py-3 hover:bg-white/80 transition-colors"
      :class="showMenu ? 'bg-white shadow-sm' : ''"
    >
      <div class="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center text-white font-medium text-base shrink-0">
        {{ userInitial }}
      </div>
      <div class="flex-1 min-w-0 text-left">
        <p class="text-sm font-medium text-ink-950 truncate">{{ displayName }}</p>
        <p class="text-xs text-ink-500 truncate">{{ displayEmail }}</p>
      </div>
      <span class="material-symbols-outlined !text-xl text-ink-500 shrink-0" :class="showMenu ? 'rotate-180' : ''">
        expand_more
      </span>
    </button>

    <!-- 下拉菜单（向上展开） -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 scale-95 translate-y-2"
      enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 translate-y-2">
      <div
        v-if="showMenu"
        class="absolute bottom-full left-0 right-0 mb-2 bg-white rounded-xl shadow-xl border border-border-dark overflow-hidden">
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
            v-if="!props.hideUserCenter"
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/store/useAuthStore'
import { useAppStore } from '@/store/useAppStore'
import { useNotificationStore } from '@/store/useNotificationStore'

const props = defineProps({
  hideUserCenter: { type: Boolean, default: false }
})

const authStore = useAuthStore()
const appStore = useAppStore()
const notificationStore = useNotificationStore()

const showMenu = ref(false)

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

function goToProfile() {
  showMenu.value = false
  // 打开个人资料弹窗
  appStore.showProfileModal = true
}

function goToUserCenter() {
  showMenu.value = false
  appStore.setCurrentPage('user-center')
}

function goToAdmin() {
  showMenu.value = false
  appStore.setCurrentPage('admin')
}

async function handleLogout() {
  showMenu.value = false
  if (confirm('确定要退出登录吗？')) {
    await authStore.logout()
    // 断开SSE连接
    notificationStore.disconnectSSE()
  }
}
</script>
