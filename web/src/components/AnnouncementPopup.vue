<template>
  <transition name="popup">
    <div
      v-if="notificationStore.popupAnnouncement"
      class="fixed top-4 right-4 z-50 w-96 max-w-[calc(100vw-2rem)] bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
    >
      <!-- 公告内容 -->
      <div class="p-4">
        <!-- 优先级标签和标题 -->
        <div class="flex items-start gap-3 mb-3">
          <span
            class="text-xs px-2 py-0.5 rounded-full flex-shrink-0"
            :class="priorityBadgeClasses[notificationStore.popupAnnouncement.priority]"
          >
            {{ getPriorityLabel(notificationStore.popupAnnouncement.priority) }}
          </span>
          <h3 class="font-semibold text-gray-900 dark:text-white flex-1 line-clamp-2">
            {{ notificationStore.popupAnnouncement.title }}
          </h3>
          <button
            @click="notificationStore.closePopup()"
            class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex-shrink-0"
            aria-label="关闭"
          >
            <span class="material-symbols-outlined !text-lg">close</span>
          </button>
        </div>

        <!-- 内容预览 -->
        <p
          class="text-sm text-gray-600 dark:text-gray-300 line-clamp-3 mb-3"
          v-html="stripHtml(notificationStore.popupAnnouncement.content)"
        ></p>

        <!-- 封面图片 -->
        <div
          v-if="notificationStore.popupAnnouncement.cover_image_url"
          class="mb-3 rounded overflow-hidden"
        >
          <img
            :src="notificationStore.popupAnnouncement.cover_image_url"
            :alt="notificationStore.popupAnnouncement.title"
            class="w-full h-40 object-cover"
          />
        </div>

        <!-- 时间 -->
        <p class="text-xs text-gray-400">
          {{ formatTime(notificationStore.popupAnnouncement.published_at) }}
        </p>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-2 p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
        <button
          @click="notificationStore.closePopup()"
          class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          关闭
        </button>
        <button
          @click="handleViewDetails"
          class="px-3 py-1.5 text-sm text-white bg-primary hover:bg-primary-strong rounded-lg transition-colors"
        >
          查看详情
        </button>
      </div>

      <!-- 倒计时进度条 -->
      <div class="h-1 bg-gray-200 dark:bg-gray-700">
        <div
          class="h-full bg-primary animate-countdown"
          :style="{ animationDuration: '10s' }"
        ></div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { useNotificationStore } from '@/store/useNotificationStore'
import { useAppStore } from '@/store/useAppStore'

const notificationStore = useNotificationStore()
const appStore = useAppStore()

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

// 去除HTML标签
function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
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

  // 显示具体日期
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
  })
}

// 查看详情
function handleViewDetails() {
  if (notificationStore.popupAnnouncement) {
    // 设置选中的通知ID
    notificationStore.setSelectedNotification(notificationStore.popupAnnouncement.id)

    // 关闭弹窗
    notificationStore.closePopup()

    // 切换到用户中心的通知标签页
    appStore.setCurrentPage('user-center', 'notifications')
  }
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 弹窗动画 */
.popup-enter-active {
  transition: all 0.3s ease;
}

.popup-leave-active {
  transition: all 0.2s ease;
}

.popup-enter-from {
  opacity: 0;
  transform: translateX(100%) scale(0.9);
}

.popup-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.9);
}

/* 倒计时动画 */
@keyframes countdown {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

.animate-countdown {
  animation: countdown linear forwards;
}
</style>
