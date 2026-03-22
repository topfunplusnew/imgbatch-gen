<template>
  <div class="h-[300px] flex flex-col bg-transparent">
    <!-- 标题栏 -->
    <div
      @click="toggleRecords"
      class="item align-center transition relative history flex items-center gap-2 px-3 py-2.5 cursor-pointer hover:bg-primary/5 shrink-0 border-b border-border-dark bg-white/90 backdrop-blur-xl"
    >
      <span class="material-symbols-outlined !text-xl text-primary icon">photo_library</span>
<!--      <div class="text text-sm font-medium text-ink-950">我的创作</div>-->
      <span
        :class="[
          'material-symbols-outlined !text-sm arrow absolute transition right-3 text-ink-400',
          appStore.showCreationRecords ? 'rotate-180' : ''
        ]"
      >
        expand_more
      </span>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import { useAuthStore } from '@/store/useAuthStore'

const appStore = useAppStore()
const authStore = useAuthStore()

const toggleRecords = () => {
  appStore.toggleCreationRecords()
}

const goToLogin = () => {
  appStore.setCurrentPage('login')
}

const goToUserCenter = () => {
  appStore.setCurrentPage('user-center')
}

onMounted(async () => {
  // 如果已登录但没有账户信息，获取账户信息
  if (authStore.isAuthenticated && !authStore.accountInfo) {
    try {
      await authStore.fetchAccountInfo()
    } catch (error) {
      console.error('获取账户信息失败:', error)
    }
  }
})
</script>
