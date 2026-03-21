<template>
  <aside class="w-12 xs:w-16 sm:w-20 md:w-56 lg:w-56 xl:w-64 flex flex-col border-r border-border-dark bg-white/90 backdrop-blur-xl shrink-0 h-screen transition-all duration-300">
    <nav v-if="!hideLogo" class="px-3 xs:px-4 md:px-4 pt-4 pb-3 space-y-1 shrink-0">
      <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 px-3">主菜单</div>

      <button
        :class="{
          'bg-white text-primary-strong border border-primary/25 shadow-sm font-medium': activeItem === 'agent',
          'text-ink-700 hover:bg-primary/5': activeItem !== 'agent'
        }"
        @click="setActive('agent')"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors text-left"
      >
        <span class="material-symbols-outlined">smart_toy</span>
        <span>首页</span>
      </button>
    </nav>

    <!-- 案例模板区域 -->
    <div class="flex-1 flex flex-col min-h-0 border-t border-border-dark">
      <!-- 搜索框 -->
      <div class="px-2 xs:px-3 py-2.5 shrink-0">
        <div class="relative">
          <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-500 !text-sm">search</span>
          <input
            v-model="searchInput"
            @input="handleSearch"
            type="text"
            placeholder="搜索模板..."
            class="w-full bg-white border border-border-dark rounded-lg pl-8 pr-2.5 py-1.5 text-xs focus:ring-1 focus:ring-primary focus:border-primary"
          >
        </div>
      </div>

      <!-- 案例列表区域 -->
      <div
        ref="caseListRef"
        class="flex-1 overflow-y-auto custom-scrollbar px-2 py-2 space-y-2"
      >
        <CaseCard
          v-for="caseItem in displayCases"
          :key="caseItem.id"
          :case-data="caseItem"
        />

        <!-- 加载更多 -->
        <div v-if="loading && cases.length > 0" class="flex items-center justify-center py-4">
          <div class="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>

        <!-- 没有更多 -->
        <div v-else-if="!hasMore && cases.length > 0" class="text-center py-4">
          <p class="text-xs text-gray-500">没有更多模板了</p>
        </div>

        <!-- 空状态 -->
        <div v-else-if="cases.length === 0 && !loading" class="text-center py-8">
          <p class="text-sm text-gray-500">暂无模板</p>
        </div>
      </div>

      <!-- 固定在底部的全部模板按钮 -->
      <div class="shrink-0 px-2 py-2 border-t border-border-dark">
        <button
          @click="appStore.toggleTemplateDrawer()"
          class="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-strong rounded-lg transition-colors shadow-sm min-h-[44px]"
        >
          <span class="material-symbols-outlined !text-lg">view_module</span>
          全部模板
        </button>
      </div>
    </div>

    <!-- 我的创作区域 -->
    <MyCreation />

    <!-- 桌面端用户信息区域 -->
    <div class="hidden lg:block shrink-0 border-t border-border-dark bg-gray-50/50">
      <UserMenuDropdown v-if="authStore.isAuthenticated" />
      <div v-else class="p-3">
        <button
          @click="appStore.setCurrentPage('login')"
          class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white hover:bg-primary/5 rounded-xl border border-border-dark transition-colors shadow-sm"
        >
          <span class="material-symbols-outlined !text-xl text-primary">login</span>
          <span class="text-sm font-medium text-ink-950">登录</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useCaseStore } from '@/store/useCaseStore'
import CaseCard from '../cases/CaseCard.vue'
import { useAppStore } from '@/store/useAppStore'
import { useAuthStore } from '@/store/useAuthStore'
import MyCreation from '../creation/MyCreation.vue'
import UserMenuDropdown from '../layout/UserMenuDropdown.vue'

const appStore = useAppStore()
const authStore = useAuthStore()

defineProps({
  hideLogo: { type: Boolean, default: false }
})

const caseStore = useCaseStore()
const caseListRef = ref(null)
const searchInput = ref('')

const activeItem = computed(() => appStore.currentPage)

// 获取案例列表
const cases = computed(() => caseStore.cases)
const loading = computed(() => caseStore.loading)
const hasMore = computed(() => caseStore.hasMore)

// 显示的案例（考虑搜索）
const displayCases = computed(() => {
  let result = cases.value

  // 按关键词搜索
  if (searchInput.value) {
    const query = searchInput.value.toLowerCase()
    result = result.filter(c =>
      c.title.toLowerCase().includes(query) ||
      c.description?.toLowerCase().includes(query) ||
      c.tags?.some(tag => tag.toLowerCase().includes(query))
    )
  }

  return result
})

const setActive = (item) => {
  appStore.setCurrentPage(item)
}

const handleSearch = () => {
  // 使用防抖来减少筛选
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    // 搜索逻辑已经在computed中处理
  }, 300)
}

let searchTimeout = null

// 案例列表滚动加载更多
const handleCaseListScroll = () => {
  if (!caseListRef.value) return

  const { scrollTop, scrollHeight, clientHeight } = caseListRef.value

  // 距离底部50px时加载更多
  if (scrollHeight - scrollTop - clientHeight < 50) {
    caseStore.loadMore()
  }
}

onMounted(() => {
  // 初始化案例
  if (caseStore.cases.length === 0) {
    caseStore.initialize()
  }

  // 添加案例列表滚动监听
  if (caseListRef.value) {
    caseListRef.value.addEventListener('scroll', handleCaseListScroll)
  }
})

onUnmounted(() => {
  if (caseListRef.value) {
    caseListRef.value.removeEventListener('scroll', handleCaseListScroll)
  }
})
</script>

<style scoped>
/* 自定义滚动条 */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}
</style>
