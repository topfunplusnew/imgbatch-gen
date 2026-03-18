/**
 * 通知工具
 * 提供统一的用户反馈机制
 */

import { ref } from 'vue'

type NotificationType = 'success' | 'error' | 'warning' | 'info'

interface Notification {
  id: number
  type: NotificationType
  title: string
  message: string
  duration?: number
}

// 通知队列
const notifications = ref<Notification[]>([])
let idCounter = 0

/**
 * 显示通知
 */
export function showNotification(
  type: NotificationType,
  title: string,
  message: string,
  duration: number = 3000
): number {
  const id = ++idCounter

  const notification: Notification = {
    id,
    type,
    title,
    message,
    duration
  }

  notifications.value.push(notification)

  // 自动移除
  if (duration > 0) {
    setTimeout(() => {
      removeNotification(id)
    }, duration)
  }

  return id
}

/**
 * 移除通知
 */
export function removeNotification(id: number): void {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

/**
 * 快捷方法
 */
export const notification = {
  success(title: string, message: string = '', duration = 3000) {
    return showNotification('success', title, message, duration)
  },

  error(title: string, message: string = '', duration = 5000) {
    return showNotification('error', title, message, duration)
  },

  warning(title: string, message: string = '', duration = 4000) {
    return showNotification('warning', title, message, duration)
  },

  info(title: string, message: string = '', duration = 3000) {
    return showNotification('info', title, message, duration)
  }
}

/**
 * 导出通知列表（用于UI显示）
 */
export function useNotifications() {
  return {
    notifications,
    removeNotification
  }
}
