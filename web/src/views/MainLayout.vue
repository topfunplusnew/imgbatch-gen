<template>
  <el-container class="main-layout">
    <!-- Desktop sidebar -->
    <el-aside width="220px" class="main-layout__aside hidden md:flex">
      <nav class="flex h-full w-full flex-col bg-white/82 backdrop-blur-xl">
        <!-- Logo -->
        <div class="shrink-0 px-4 pt-5 pb-4">
          <router-link to="/" class="flex items-center justify-center rounded-2xl bg-white/90 px-3 py-3 shadow-sm">
            <img src="/photo/logo.png" alt="Logo" class="h-auto w-[76%] object-contain" style="aspect-ratio: 240/160;" />
          </router-link>
        </div>

        <!-- Navigation menu -->
        <div class="shrink-0 px-3 pb-2">
          <div class="mb-2 px-3 text-[11px] font-bold uppercase tracking-[0.24em] text-ink-500">
            主菜单
          </div>
          <ul class="space-y-1">
            <li v-for="item in menuItems" :key="item.to">
              <router-link
                :to="item.to"
                :class="[
                  'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all',
                  isActive(item.to)
                    ? 'bg-primary/12 text-primary'
                    : 'text-ink-700 hover:bg-primary/5'
                ]"
              >
                <span class="material-symbols-outlined text-[20px]">{{ item.icon }}</span>
                <span>{{ item.text }}</span>
              </router-link>
            </li>
          </ul>
        </div>

        <!-- Spacer -->
        <div class="flex-1"></div>

        <!-- Points display -->
        <div v-if="authStore.isAuthenticated" class="shrink-0 mx-3 mb-2 rounded-2xl border border-border-dark bg-white/80 p-3">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-[11px] font-bold uppercase tracking-wider text-ink-500">我的积分</span>
            <router-link to="/pricing" class="text-[11px] text-primary hover:underline">充值</router-link>
          </div>
          <div class="flex items-baseline gap-1">
            <span class="text-xl font-bold text-ink-950">{{ accountPoints }}</span>
            <span class="text-xs text-ink-500">积分</span>
          </div>
          <div v-if="accountGiftPoints > 0" class="mt-0.5 text-[10px] text-ink-500">
            含临时积分 {{ accountGiftPoints }}（今日有效）
          </div>
        </div>

        <!-- Bottom actions -->
        <div class="shrink-0 border-t border-border-dark px-3 py-2 space-y-0.5">
          <router-link
            to="/pricing"
            :class="[
              'flex items-center gap-3 rounded-2xl px-4 py-2.5 text-sm font-medium transition-all',
              isActive('/pricing') ? 'bg-primary/12 text-primary' : 'text-ink-700 hover:bg-primary/5'
            ]"
          >
            <span class="material-symbols-outlined text-[20px]">payments</span>
            <span>套餐定价</span>
          </router-link>
          <button
            @click="openInvite"
            class="flex w-full items-center gap-3 rounded-2xl px-4 py-2.5 text-sm font-medium text-ink-700 transition-all hover:bg-primary/5"
          >
            <span class="material-symbols-outlined text-[20px]">person_add</span>
            <span>邀请好友</span>
          </button>
        </div>

        <!-- User section -->
        <div class="shrink-0 border-t border-border-dark bg-white/70 p-3">
          <UserMenuDropdown v-if="authStore.isAuthenticated" />
          <el-button v-else type="default" class="w-full justify-center" @click="$router.push('/login')">
            <span class="material-symbols-outlined !text-lg text-primary">login</span>
            <span>登录</span>
          </el-button>
        </div>
      </nav>
    </el-aside>

    <!-- Main content -->
    <el-container class="main-layout__content">
      <!-- Mobile top bar -->
      <div class="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-border-dark bg-white/80 px-4 py-3 backdrop-blur-xl md:hidden">
        <el-button circle @click="showMobileSidebar = true">
          <span class="material-symbols-outlined !text-xl">menu</span>
        </el-button>
        <router-link to="/" class="flex items-center">
          <img src="/photo/logo.png" alt="Logo" class="h-8 object-contain" />
        </router-link>
        <div class="w-10"></div>
      </div>

      <router-view />
    </el-container>

    <!-- Mobile sidebar drawer -->
    <el-drawer
      v-model="showMobileSidebar"
      direction="ltr"
      :with-header="false"
      size="280px"
      append-to-body
    >
      <nav class="flex h-full w-full flex-col bg-white">
        <!-- Logo + close -->
        <div class="flex items-center justify-between px-4 pt-5 pb-4">
          <router-link to="/" @click="showMobileSidebar = false">
            <img src="/photo/logo.png" alt="Logo" class="h-10 object-contain" />
          </router-link>
          <el-button circle text @click="showMobileSidebar = false">
            <span class="material-symbols-outlined !text-xl">close</span>
          </el-button>
        </div>

        <!-- Mobile nav -->
        <div class="flex-1 px-3">
          <ul class="space-y-1">
            <li v-for="item in menuItems" :key="item.to">
              <router-link
                :to="item.to"
                @click="showMobileSidebar = false"
                :class="[
                  'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all',
                  isActive(item.to)
                    ? 'bg-primary/12 text-primary'
                    : 'text-ink-700 hover:bg-primary/5'
                ]"
              >
                <span class="material-symbols-outlined text-[20px]">{{ item.icon }}</span>
                <span>{{ item.text }}</span>
              </router-link>
            </li>
          </ul>
        </div>

        <!-- Mobile points -->
        <div v-if="authStore.isAuthenticated" class="shrink-0 mx-3 mb-2 rounded-2xl border border-border-dark bg-white/80 p-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-ink-500">我的积分</span>
            <router-link to="/pricing" @click="showMobileSidebar = false" class="text-xs text-primary">充值</router-link>
          </div>
          <div class="text-lg font-bold text-ink-950">{{ accountPoints }}</div>
        </div>

        <!-- Mobile bottom -->
        <div class="shrink-0 border-t border-border-dark px-3 py-2 space-y-0.5">
          <router-link
            to="/pricing"
            @click="showMobileSidebar = false"
            class="flex items-center gap-3 rounded-2xl px-4 py-2.5 text-sm font-medium text-ink-700 hover:bg-primary/5"
          >
            <span class="material-symbols-outlined text-[20px]">payments</span>
            <span>套餐定价</span>
          </router-link>
          <button
            @click="openInvite(); showMobileSidebar = false"
            class="flex w-full items-center gap-3 rounded-2xl px-4 py-2.5 text-sm font-medium text-ink-700 hover:bg-primary/5"
          >
            <span class="material-symbols-outlined text-[20px]">person_add</span>
            <span>邀请好友</span>
          </button>
        </div>
        <div class="shrink-0 border-t border-border-dark p-3">
          <UserMenuDropdown v-if="authStore.isAuthenticated" />
          <el-button v-else type="default" class="w-full justify-center" @click="$router.push('/login'); showMobileSidebar = false">
            <span class="material-symbols-outlined !text-lg text-primary">login</span>
            <span>登录</span>
          </el-button>
        </div>
      </nav>
    </el-drawer>

    <!-- Invite dialog -->
    <el-dialog v-model="showInviteDialog" title="邀请好友" width="min(440px, 90vw)" align-center>
      <div class="space-y-4">
        <p class="text-sm text-ink-700">分享以下链接给好友，好友注册后双方都将获得奖励：</p>
        <div class="flex items-center gap-2">
          <el-input :model-value="inviteLink" readonly class="flex-1" />
          <el-button type="primary" @click="copyInviteLink">
            <span class="material-symbols-outlined !text-lg">content_copy</span>
            <span>复制</span>
          </el-button>
        </div>
        <p class="text-xs text-ink-500">好友通过此链接注册即视为邀请成功</p>
      </div>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/store/useAuthStore'
import { useAppStore } from '@/store/useAppStore'
import UserMenuDropdown from '@/components/layout/UserMenuDropdown.vue'
import api from '@/services/api'
import { notification } from '@/utils/notification'

const route = useRoute()
const authStore = useAuthStore()
const appStore = useAppStore()

const showMobileSidebar = ref(false)
const showInviteDialog = ref(false)
const accountPoints = ref(0)
const accountGiftPoints = ref(0)

const menuItems = [
  { icon: 'home', text: '首页', to: '/' },
  { icon: 'collections', text: '多图创作', to: '/multi' },
  { icon: 'photo_library', text: '我的作品', to: '/gallery' },
  { icon: 'grid_view', text: '场景库', to: '/scenes' },
]

const isActive = (to: string) => {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}

const inviteLink = computed(() => {
  const code = authStore.user?.invite_code || authStore.user?.id || ''
  return `${window.location.origin}/login?code=${code}`
})

const openInvite = () => {
  showInviteDialog.value = true
}

const copyInviteLink = async () => {
  try {
    await navigator.clipboard.writeText(inviteLink.value)
    notification.success('已复制', '邀请链接已复制到剪贴板')
  } catch {
    notification.error('复制失败', '请手动复制链接')
  }
}

const loadAccountInfo = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const info = await api.getAccountInfo()
    accountPoints.value = (info.points || 0) + (info.gift_points || 0)
    accountGiftPoints.value = info.gift_points || 0
  } catch {
    // silently fail
  }
}

watch(() => authStore.isAuthenticated, (val) => {
  if (val) loadAccountInfo()
})

onMounted(() => {
  loadAccountInfo()
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(140, 42, 46, 0.1), transparent 28%),
    linear-gradient(180deg, rgba(255, 252, 251, 0.86) 0%, rgba(246, 239, 238, 0.96) 100%);
}

.main-layout__aside {
  height: 100vh;
  position: relative;
  z-index: 20;
  background: rgba(255, 253, 252, 0.78);
  backdrop-filter: blur(18px);
  border-right: 1px solid var(--color-border-dark);
}

.main-layout__content {
  min-width: 0;
  height: 100vh;
  overflow: hidden;
  flex-direction: column;
}
</style>
