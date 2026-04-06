<template>
  <div
    class="w-80 max-h-[500px] bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col"
    @click.stop
  >
    <!-- 头部 -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <h3 class="font-semibold text-gray-900 dark:text-white">
        通知
        <span v-if="unreadCount > 0" class="ml-2 text-sm text-primary">
          ({{ unreadCount }})
        </span>
      </h3>
      <div class="flex items-center gap-2">
        <button
          v-if="hasUnread"
          @click="handleMarkAllRead"
          class="text-xs text-primary hover:text-primary/80 transition-colors"
        >
          全部已读
        </button>
        <button
          @click="$emit('close')"
          class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          aria-label="关闭"
        >
          <span class="material-symbols-outlined !text-lg">close</span>
        </button>
      </div>
    </div>

    <!-- 通知列表 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="notifications.length === 0" class="flex flex-col items-center justify-center py-8 text-gray-500 dark:text-gray-400">
        <span class="material-symbols-outlined !text-4xl mb-2">notifications_none</span>
        <p class="text-sm">暂无通知</p>
      </div>

      <div v-else class="divide-y divide-gray-100 dark:divide-gray-700">
        <div
          v-for="notification in displayedNotifications"
          :key="notification.id"
          @click="handleNotificationClick(notification)"
          class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
          :class="{ 'bg-blue-50/50 dark:bg-blue-900/10': !notification.is_read }"
        >
          <!-- 优先级指示器 -->
          <div class="flex items-start gap-3">
            <div
              class="w-2 h-2 rounded-full mt-2 flex-shrink-0"
              :class="priorityClasses[notification.priority]"
            ></div>

            <div class="flex-1 min-w-0">
              <!-- 标题 -->
              <div class="flex items-center gap-2 mb-1">
                <h4
                  class="font-medium text-gray-900 dark:text-white truncate"
                  :class="{ 'font-semibold': !notification.is_read }"
                >
                  {{ notification.title }}
                </h4>
                <span v-if="notification.is_pinned" class="material-symbols-outlined !text-sm text-gray-400">
                  push_pin
                </span>
              </div>

              <!-- 内容预览 -->
              <p
                class="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-2"
                v-html="stripHtml(notification.content)"
              ></p>

              <!-- 封面图片 -->
              <div
                v-if="notification.cover_image_url"
                class="mb-2 rounded overflow-hidden"
              >
                <img
                  :src="notification.cover_image_url"
                  :alt="notification.title"
                  class="w-full h-32 object-cover cursor-pointer"
                  @click.stop="handleNotificationClick(notification)"
                />
              </div>

              <!-- 时间 -->
              <p class="text-xs text-gray-400">
                {{ formatTime(notification.published_at) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部 -->
    <div class="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
      <button
        @click="handleViewAllNotifications"
        class="block w-full text-center text-sm text-primary hover:text-primary/80 transition-colors"
      >
        查看全部通知
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore, type Announcement } from '@/store/useNotificationStore'
import { useAppStore } from '@/store/useAppStore'

const props = defineProps<{
  maxItems?: number
}>()

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const appStore = useAppStore()
const notificationStore = useNotificationStore()

const loading = ref(false)
const notifications = ref<Announcement[]>([])

// 优先级样式映射
const priorityClasses = {
  urgent: 'bg-red-500',
  high: 'bg-orange-500',
  normal: 'bg-blue-500',
  low: 'bg-gray-400',
}

const unreadCount = computed(() => notificationStore.unreadCount)
const hasUnread = computed(() => notificationStore.hasUnread)

// 显示的通知列表（限制数量）
const displayedNotifications = computed(() => {
  const max = props.maxItems || 10
  return notifications.value.slice(0, max)
})

// 加载通知列表
async function loadNotifications() {
  loading.value = true
  try {
    const result = await notificationStore.fetchMyNotifications(1, 20)
    notifications.value = result.items

    // 同时刷新未读数量
    await notificationStore.fetchUnreadCount()
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

  // 设置选中的通知ID
  notificationStore.setSelectedNotification(notification.id)

  // 关闭面板
  emit('close')

  // 使用 appStore 切换到用户中心的通知标签页
  router.push('/user-center')
}

// 查看全部通知
function handleViewAllNotifications() {
  emit('close')
  router.push('/user-center')
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

// 去除HTML标签
function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

// 格式化时间
function formatTime(dateString: string | null): string {
  if (!dateString) return ''

  // 后端返回UTC时间不带Z，补上避免8小时时差
  let normalized = dateString
  if (!dateString.endsWith('Z') && !dateString.includes('+') && !/[+-]\d{2}:\d{2}$/.test(dateString)) {
    normalized = dateString.replace(' ', 'T') + 'Z'
  }
  const date = new Date(normalized)
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
    month: '2-digit',
    day: '2-digit',
  })
}

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
