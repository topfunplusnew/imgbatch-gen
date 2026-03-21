<template>
  <div
    v-if="announcements.length > 0"
    class="relative rounded-xl overflow-hidden bg-gradient-to-br from-primary/10 to-primary/5 dark:from-primary/20 dark:to-primary/10"
    @mouseenter="pauseAutoplay"
    @mouseleave="resumeAutoplay"
  >
    <!-- 轮播内容 -->
    <div class="relative">
      <transition
        :name="transitionDirection"
        @before-enter="beforeEnter"
        @after-enter="afterEnter"
      >
        <div
          v-if="currentAnnouncement"
          :key="currentAnnouncement.id"
          class="p-4 md:p-6 cursor-pointer"
          @click="handleClick(currentAnnouncement)"
        >
          <div class="flex items-start gap-4">
            <!-- 封面图片 -->
            <div
              v-if="currentAnnouncement.cover_image_url"
              class="w-24 h-24 md:w-32 md:h-32 rounded-lg overflow-hidden flex-shrink-0"
            >
              <img
                :src="currentAnnouncement.cover_image_url"
                :alt="currentAnnouncement.title"
                class="w-full h-full object-cover"
              />
            </div>

            <!-- 内容 -->
            <div class="flex-1 min-w-0">
              <!-- 标签 -->
              <div class="flex items-center gap-2 mb-2">
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
              <h3 class="text-base md:text-lg font-semibold text-gray-900 dark:text-white mb-1 line-clamp-2">
                {{ currentAnnouncement.title }}
              </h3>

              <!-- 内容预览 -->
              <p
                class="text-sm text-gray-600 dark:text-gray-300 line-clamp-2"
                v-html="stripHtml(currentAnnouncement.content)"
              ></p>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- 导航按钮 -->
    <template v-if="announcements.length > 1">
      <!-- 上一张 -->
      <button
        @click.stop="previous"
        class="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white/80 dark:bg-gray-800/80 hover:bg-white dark:hover:bg-gray-800 shadow-lg flex items-center justify-center transition-all opacity-0 hover:opacity-100 group-hover:opacity-100"
        aria-label="上一张"
      >
        <span class="material-symbols-outlined !text-lg">chevron_left</span>
      </button>

      <!-- 下一张 -->
      <button
        @click.stop="next"
        class="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white/80 dark:bg-gray-800/80 hover:bg-white dark:hover:bg-gray-800 shadow-lg flex items-center justify-center transition-all opacity-0 hover:opacity-100 group-hover:opacity-100"
        aria-label="下一张"
      >
        <span class="material-symbols-outlined !text-lg">chevron_right</span>
      </button>
    </template>

    <!-- 指示点 -->
    <div
      v-if="announcements.length > 1"
      class="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5"
    >
      <button
        v-for="(announcement, index) in announcements"
        :key="announcement.id"
        @click.stop="goTo(index)"
        class="w-2 h-2 rounded-full transition-all"
        :class="currentIndex === index ? 'bg-primary w-6' : 'bg-white/50 hover:bg-white/70'"
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

// 优先级标签样式
const priorityBadgeClasses = {
  urgent: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  low: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300',
}

// 优先级标签中文映射
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
  return announcements.value[currentIndex.value] || null
})

// 加载公告列表
async function loadAnnouncements() {
  try {
    const items = await notificationStore.fetchPublicAnnouncements(1, props.maxItems || 5)
    // 只显示置顶和高优先级的公告
    announcements.value = items.filter((a: any) =>
      a.is_pinned || a.priority === 'high' || a.priority === 'urgent'
    )
  } catch (error) {
    console.error('加载公告失败:', error)
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

// 去除HTML标签
function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}
</script>

<style scoped>
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
</style>
