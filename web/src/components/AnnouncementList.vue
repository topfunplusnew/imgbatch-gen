<template>
  <div class="space-y-4">
    <!-- 筛选器 -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <button
        @click="filter = 'all'"
        class="px-3 py-1.5 text-sm rounded-lg transition-colors"
        :class="filter === 'all' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'"
      >
        全部
        <span v-if="totalCount > 0" class="ml-1 text-xs opacity-75">({{ totalCount }})</span>
      </button>
      <button
        @click="filter = 'unread'"
        class="px-3 py-1.5 text-sm rounded-lg transition-colors"
        :class="filter === 'unread' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'"
      >
        未读
        <span v-if="unreadCount > 0" class="ml-1 text-xs opacity-75">({{ unreadCount }})</span>
      </button>
      <button
        v-if="hasUnread"
        @click="handleMarkAllRead"
        class="ml-auto px-3 py-1.5 text-sm text-primary hover:text-primary/80 transition-colors"
      >
        全部已读
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
    </div>

    <!-- 空状态 -->
    <div
      v-else-if="filteredNotifications.length === 0"
      class="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400"
    >
      <span class="material-symbols-outlined !text-5xl mb-3">notifications_none</span>
      <p class="text-lg">暂无通知</p>
      <p class="text-sm mt-1">当有新公告时，会在这里显示</p>
    </div>

    <!-- 通知列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="notification in filteredNotifications"
        :key="notification.id"
        :data-notification-id="notification.id"
        @click="handleNotificationClick(notification)"
        class="p-4 rounded-xl border transition-all cursor-pointer hover:shadow-md"
        :class="{
          'bg-blue-50/50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800': !notification.is_read,
          'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700': notification.is_read,
          'ring-2 ring-primary ring-offset-2': highlightedId === notification.id
        }"
      >
        <div class="flex items-start gap-4">
          <!-- 优先级指示器 -->
          <div
            class="w-3 h-3 rounded-full mt-1 flex-shrink-0"
            :class="priorityDotClasses[notification.priority]"
          ></div>

          <div class="flex-1 min-w-0">
            <!-- 头部：标题和标签 -->
            <div class="flex items-center gap-2 mb-2 flex-wrap">
              <h3
                class="text-base font-semibold text-gray-900 dark:text-white"
                :class="{ 'font-bold': !notification.is_read }"
              >
                {{ notification.title }}
              </h3>
              <span
                class="text-xs px-2 py-0.5 rounded-full"
                :class="priorityBadgeClasses[notification.priority]"
              >
                {{ getPriorityLabel(notification.priority) }}
              </span>
              <span
                v-if="notification.is_pinned"
                class="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 flex items-center gap-1"
              >
                <span class="material-symbols-outlined !text-sm">push_pin</span>
                置顶
              </span>
              <span
                v-if="!notification.is_read"
                class="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
              >
                未读
              </span>
            </div>

            <!-- 封面图片 -->
            <div
              v-if="notification.cover_image_url"
              class="mb-3 rounded-lg overflow-hidden"
            >
              <img
                :src="notification.cover_image_url"
                :alt="notification.title"
                class="w-full max-h-64 object-cover"
              />
            </div>

            <!-- 内容 -->
            <div
              class="text-sm text-gray-700 dark:text-gray-300 mb-3 prose dark:prose-invert max-w-none"
              v-html="notification.content"
            ></div>

            <!-- 底部：时间和操作 -->
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>{{ formatTime(notification.published_at) }}</span>
              <div class="flex items-center gap-3">
                <span v-if="notification.view_count">
                  <span class="material-symbols-outlined !text-sm align-middle">visibility</span>
                  {{ notification.view_count }}
                </span>
                <button
                  v-if="!notification.is_read"
                  @click.stop="handleMarkAsRead(notification.id)"
                  class="text-primary hover:text-primary/80 transition-colors"
                >
                  标为已读
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div
      v-if="totalPages > 1"
      class="flex items-center justify-center gap-2 pt-4"
    >
      <button
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        上一页
      </button>
      <span class="text-sm text-gray-600 dark:text-gray-400">
        {{ currentPage }} / {{ totalPages }}
      </span>
      <button
        @click="goToPage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useNotificationStore, type Announcement } from '@/store/useNotificationStore'

const notificationStore = useNotificationStore()

const filter = ref<'all' | 'unread'>('all')
const loading = ref(false)
const notifications = ref<Announcement[]>([])
const currentPage = ref(1)
const pageSize = 10
const totalPages = ref(1)
const totalCount = ref(0)
const highlightedId = ref<string | null>(null)

// 优先级样式
const priorityDotClasses = {
  urgent: 'bg-red-500',
  high: 'bg-orange-500',
  normal: 'bg-blue-500',
  low: 'bg-gray-400',
}

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

// 未读数量
const unreadCount = computed(() => notificationStore.unreadCount)
const hasUnread = computed(() => notificationStore.hasUnread)

// 过滤后的通知列表
const filteredNotifications = computed(() => {
  if (filter.value === 'unread') {
    return notifications.value.filter(n => !n.is_read)
  }
  return notifications.value
})

// 加载通知列表
async function loadNotifications(page = 1) {
  loading.value = true
  try {
    const result = await notificationStore.fetchMyNotifications(page, pageSize)
    notifications.value = result.items
    totalPages.value = result.total_pages
    totalCount.value = result.total
    currentPage.value = page
  } catch (error) {
    console.error('加载通知失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理通知点击
async function handleNotificationClick(notification: Announcement) {
  // 标记为已读
  if (!notification.is_read) {
    await notificationStore.markAsRead(notification.id)
    // 更新本地状态
    const index = notifications.value.findIndex(n => n.id === notification.id)
    if (index !== -1) {
      notifications.value[index].is_read = true
      notifications.value[index].read_at = new Date().toISOString()
    }
  }

  // 标记为已点击
  await notificationStore.markAsClicked(notification.id)
}

// 标记为已读
async function handleMarkAsRead(announcementId: string) {
  try {
    await notificationStore.markAsRead(announcementId)
    // 更新本地状态
    const index = notifications.value.findIndex(n => n.id === announcementId)
    if (index !== -1) {
      notifications.value[index].is_read = true
      notifications.value[index].read_at = new Date().toISOString()
    }
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

// 标记全部为已读
async function handleMarkAllRead() {
  try {
    await notificationStore.markAllAsRead()
    // 更新本地状态
    notifications.value.forEach(n => {
      n.is_read = true
      n.read_at = new Date().toISOString()
    })
  } catch (error) {
    console.error('标记全部已读失败:', error)
  }
}

// 分页导航
function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    loadNotifications(page)
  }
}

// 格式化时间
function formatTime(dateString: string | null): string {
  if (!dateString) return ''

  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于1分钟
  if (diff < 60 * 1000) {
    return '刚刚'
  }

  // 小于1小时
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000))
    return `${minutes}分钟前`
  }

  // 小于1天
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    return `${hours}小时前`
  }

  // 小于7天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days}天前`
  }

  // 显示具体日期
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 监听筛选器变化
watch(filter, () => {
  // 如果切换到未读且没有未读通知，加载第一页
  if (filter.value === 'unread' && filteredNotifications.value.length === 0) {
    loadNotifications(1)
  }
})

// 监听选中的通知ID（用于从其他页面跳转过来时显示特定通知）
watch(() => notificationStore.selectedNotificationId, (id) => {
  if (id && notifications.value.length > 0) {
    // 检查通知是否在当前页
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      highlightedId.value = id
      // 滚动到指定通知
      nextTick(() => {
        const element = document.querySelector(`[data-notification-id="${id}"]`)
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' })
          // 3秒后移除高亮
          setTimeout(() => {
            highlightedId.value = null
          }, 3000)
        }
      })
    } else {
      // 通知不在当前页，重新加载
      loadNotifications(1)
    }
  }
})

onMounted(() => {
  loadNotifications(1)
})
</script>
