<template>
  <div
    v-if="announcements.length > 0"
    class="relative w-full h-[120px] overflow-hidden bg-gradient-to-br from-primary/10 to-primary/5 border-b border-border-dark"
    @mouseenter="pauseAutoplay"
    @mouseleave="resumeAutoplay"
  >
    <!-- 轮播内容 - 内部可滚动 -->
    <transition
      :name="transitionDirection"
      mode="out-in"
    >
      <div
        v-if="currentAnnouncement"
        :key="currentAnnouncement.id"
        class="h-full overflow-y-auto scrollbar-thin"
        @click="handleClick(currentAnnouncement)"
      >
        <div
          class="p-4 md:px-8 cursor-pointer min-h-full flex items-center"
        >
          <div class="flex items-center gap-4 w-full">
            <!-- 封面图片 -->
            <div
              v-if="currentAnnouncement.cover_image_url"
              class="w-20 h-20 md:w-24 md:h-24 rounded-lg overflow-hidden flex-shrink-0 shadow-md"
            >
              <img
                :src="getImageUrl(currentAnnouncement.cover_image_url)"
                :alt="currentAnnouncement.title"
                class="w-full h-full object-cover"
              />
            </div>

            <!-- 内容 -->
            <div class="flex-1 min-w-0">
              <!-- 标签 -->
              <div class="flex items-center gap-2 mb-1">
                <span
                  class="text-xs px-2 py-0.5 rounded-full"
                  :class="priorityBadgeClasses[currentAnnouncement.priority]"
                >
                  {{ getPriorityLabel(currentAnnouncement.priority) }}
                </span>
                <span
                  v-if="currentAnnouncement.is_pinned"
                  class="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
                >
                  置顶
                </span>
              </div>

              <!-- 标题 -->
              <h3 class="text-sm md:text-base font-semibold text-ink-950 dark:text-white mb-1 line-clamp-1">
                {{ currentAnnouncement.title }}
              </h3>

              <!-- 内容预览 -->
              <p
                class="text-xs md:text-sm text-ink-600 dark:text-white/80 line-clamp-2"
                v-html="stripHtml(currentAnnouncement.content)"
              ></p>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 导航按钮 -->
    <template v-if="announcements.length > 1">
      <!-- 上一张 -->
      <button
        @click.stop="previous"
        class="absolute left-3 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-white/80 dark:bg-gray-800/80 hover:bg-white dark:hover:bg-gray-800 shadow-md flex items-center justify-center transition-all z-10"
        aria-label="上一张"
      >
        <span class="material-symbols-outlined !text-base text-gray-600 dark:text-gray-300">chevron_left</span>
      </button>

      <!-- 下一张 -->
      <button
        @click.stop="next"
        class="absolute right-3 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-white/80 dark:bg-gray-800/80 hover:bg-white dark:hover:bg-gray-800 shadow-md flex items-center justify-center transition-all z-10"
        aria-label="下一张"
      >
        <span class="material-symbols-outlined !text-base text-gray-600 dark:text-gray-300">chevron_right</span>
      </button>
    </template>

    <!-- 指示点 -->
    <div
      v-if="announcements.length > 1"
      class="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center gap-1.5"
    >
      <button
        v-for="(announcement, index) in announcements"
        :key="announcement.id"
        @click.stop="goTo(index)"
        class="w-1.5 h-1.5 rounded-full transition-all"
        :class="currentIndex === index ? 'bg-primary w-5' : 'bg-white/50 hover:bg-white/70'"
        :aria-label="`幻灯片 ${index + 1}`"
      ></button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import { useNotificationStore } from '@/store/useNotificationStore'

const props = defineProps<{
  autoplay?: boolean
  autoplayInterval?: number
  maxItems?: number
}>()

const appStore = useAppStore()
const notificationStore = useNotificationStore()

const announcements = ref<any[]>([])
const currentIndex = ref(0)
const transitionDirection = ref<'slide-left' | 'slide-right'>('slide-left')

let autoplayTimer: number | null = null
let isPaused = false

// 优先级标签样式 - 使用系统配色
const priorityBadgeClasses = {
  urgent: 'bg-red-500/20 text-red-600 dark:text-red-300',
  high: 'bg-orange-500/20 text-orange-600 dark:text-orange-300',
  normal: 'bg-primary/20 text-primary dark:text-white/90',
  low: 'bg-gray-500/20 text-gray-600 dark:text-gray-300',
}

// 获取优先级标签
function getPriorityLabel(priority: string): string {
  const labels: Record<string, string> = {
    urgent: '紧急',
    high: '重要',
    normal: '普通',
    low: '低',
  }
  return labels[priority] || '普通'
}

// 当前公告
const currentAnnouncement = computed(() => {
  console.log('[NotificationCarousel] Computing currentAnnouncement')
  console.log('[NotificationCarousel] announcements:', announcements.value)
  console.log('[NotificationCarousel] announcements.value.length:', announcements.value.length)
  console.log('[NotificationCarousel] currentIndex:', currentIndex.value)

  if (!announcements.value || announcements.value.length === 0) {
    console.log('[NotificationCarousel] announcements is empty, returning null')
    return null
  }

  if (currentIndex.value >= announcements.value.length) {
    console.log('[NotificationCarousel] currentIndex out of bounds, resetting to 0')
    currentIndex.value = 0
    return null
  }

  const announcement = announcements.value[currentIndex.value]
  console.log('[NotificationCarousel] announcements.value[currentIndex.value]:', announcement)
  console.log('[NotificationCarousel] currentAnnouncement:', announcement)
  return announcement
})

// 加载公告列表
async function loadAnnouncements() {
  try {
    console.log('[NotificationCarousel] Loading announcements...')
    const items = await notificationStore.fetchPublicAnnouncements(1, props.maxItems || 5)
    console.log('[NotificationCarousel] Fetched items type:', typeof items, Array.isArray(items))
    console.log('[NotificationCarousel] Fetched items:', items)

    // 显示所有已发布的公告（API已过滤is_published）
    if (Array.isArray(items)) {
      announcements.value = items
    } else if (items && Array.isArray(items.items)) {
      // 兼容不同的返回格式
      announcements.value = items.items
    } else {
      announcements.value = []
    }

    console.log('[NotificationCarousel] Announcements to display:', announcements.value.length, announcements.value)
  } catch (error) {
    console.error('[NotificationCarousel] 加载公告失败:', error)
    announcements.value = []
  }
}

// 下一张
function next() {
  transitionDirection.value = 'slide-left'
  currentIndex.value = (currentIndex.value + 1) % announcements.value.length
}

 // 上一张
function previous() {
  transitionDirection.value = 'slide-right'
  currentIndex.value =
    currentIndex.value === 0
      ? announcements.value.length - 1
      : currentIndex.value - 1
  }

// 跳转到指定幻灯片
function goTo(index: number) {
  if (index < currentIndex.value) {
    transitionDirection.value = 'slide-right'
  } else {
    transitionDirection.value = 'slide-left'
  }
  currentIndex.value = index
}

// 处理点击
function handleClick(announcement: any) {
  // 设置选中的通知ID
  notificationStore.setSelectedNotification(announcement.id)

  // 跳转到用户中心通知详情
  appStore.setCurrentPage('user-center')
}

// 暂停自动播放
function pauseAutoplay() {
  isPaused = true
  stopAutoplay()
}

 // 恢复自动播放
function resumeAutoplay() {
  isPaused = false
  startAutoplay()
}

 // 开始自动播放
function startAutoplay() {
  if (!props.autoplay || announcements.value.length <= 1) return

  stopAutoplay()
  autoplayTimer = window.setInterval(() => {
    if (!isPaused) {
      next()
    }
  }, props.autoplayInterval || 5000)
}

// 停止自动播放
function stopAutoplay() {
  if (autoplayTimer !== null) {
    clearInterval(autoplayTimer)
    autoplayTimer = null
  }
}

// 过渡动画回调
function beforeEnter(el: HTMLElement) {
  el.style.opacity = '0'
}

 function afterEnter(el: HTMLElement) {
  el.style.opacity = '1'
}

 onMounted(() => {
  loadAnnouncements()
  startAutoplay()
})

 onUnmounted(() => {
  stopAutoplay()
})

// 暴露方法给父组件
defineExpose({
  pauseAutoplay,
  resumeAutoplay
})

// 去除HTML标签
function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

// 获取图片完整 URL
function getImageUrl(path: string | null): string {
  if (!path) return ''
  // 如果 path 以 /api/ 开头，需要拼接完整 URL
  if (path.startsWith('/api/')) {
    // 如果已经是完整URL，直接返回
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path
    }
    // 否则，拼接 API 基础 URL
    return `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8888'}${path}`
  }
  return path
}
</script>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 幻灯片过渡动画 */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease;
}

 .slide-left-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

 .slide-left-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

 .slide-right-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

 .slide-right-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* 自定义滚动条样式 */
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

 .scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.scrollbar-thin:hover::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.3);
}
</style>
