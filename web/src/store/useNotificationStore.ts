/**
 * 通知系统状态管理 Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

export interface Announcement {
  id: string
  title: string
  content: string
  priority: 'low' | 'normal' | 'high' | 'urgent'
  announcement_type: string
  is_pinned: boolean
  is_published: boolean
  published_at: string | null
  expires_at: string | null
  cover_image_url: string | null
  target_audience: string
  view_count: number
  click_count: number
  created_at: string
  updated_at: string
  created_by: string | null
  is_read?: boolean
  read_at?: string | null
  is_clicked?: boolean
  clicked_at?: string | null
}

export const useNotificationStore = defineStore('notification', () => {
  // 状态
  const notifications = ref<Announcement[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // SSE连接状态
  const sseConnected = ref(false)
  const sseConnection = ref<EventSource | null>(null)
  const sseReconnectAttempts = ref(0)
  const sseMaxReconnectAttempts = 5
  const sseReconnectDelay = ref(1000) // 初始1秒
  const sseReconnectTimer = ref<number | null>(null)

  // 选中的通知ID（用于详情查看）
  const selectedNotificationId = ref<string | null>(null)

  // 新公告弹窗状态
  const popupAnnouncement = ref<Announcement | null>(null)
  const popupTimer = ref<number | null>(null)

  // 计算属性
  const hasUnread = computed(() => unreadCount.value > 0)
  const pinnedNotifications = computed(() =>
    notifications.value.filter(n => n.is_pinned)
  )
  const urgentNotifications = computed(() =>
    notifications.value.filter(n => n.priority === 'urgent' && !n.is_read)
  )
  const highPriorityNotifications = computed(() =>
    notifications.value.filter(n => n.priority === 'high' && !n.is_read)
  )

  // 获取我的通知列表
  async function fetchMyNotifications(page = 1, pageSize = 20) {
    loading.value = true
    error.value = null
    try {
      console.log(`[Notification] Fetching notifications: page=${page}, pageSize=${pageSize}`)
      const result = await api.getMyNotifications(page, pageSize)

      console.log(`[Notification] ✅ Received ${result.items.length} items, total: ${result.total}`)

      if (page === 1) {
        notifications.value = result.items
      } else {
        notifications.value.push(...result.items)
      }
      return result
    } catch (err: any) {
      console.error('[Notification] ❌ Fetch failed:', err)
      error.value = err.message || '获取通知失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取未读数量
  async function fetchUnreadCount() {
    try {
      const result = await api.getUnreadCount()
      unreadCount.value = result.count
      return result.count
    } catch (err: any) {
      console.error('获取未读数量失败:', err)
      throw err
    }
  }

  // 标记为已读
  async function markAsRead(announcementId: string) {
    try {
      await api.markNotificationAsRead(announcementId)

      // 更新本地状态
      const notification = notifications.value.find(n => n.id === announcementId)
      if (notification) {
        notification.is_read = true
        notification.read_at = new Date().toISOString()
      }

      // 更新未读数量
      if (unreadCount.value > 0) {
        unreadCount.value--
      }

      return true
    } catch (err: any) {
      console.error('标记已读失败:', err)
      throw err
    }
  }

  // 标记全部为已读
  async function markAllAsRead() {
    try {
      await api.markAllNotificationsAsRead()

      // 更新本地状态
      notifications.value.forEach(n => {
        if (!n.is_read) {
          n.is_read = true
          n.read_at = new Date().toISOString()
        }
      })

      unreadCount.value = 0
      return true
    } catch (err: any) {
      console.error('标记全部已读失败:', err)
      throw err
    }
  }

  // 标记为已点击
  async function markAsClicked(announcementId: string) {
    try {
      await api.markNotificationAsClicked(announcementId)

      // 更新本地状态
      const notification = notifications.value.find(n => n.id === announcementId)
      if (notification) {
        notification.is_clicked = true
        notification.clicked_at = new Date().toISOString()
      }

      return true
    } catch (err: any) {
      console.error('标记已点击失败:', err)
      throw err
    }
  }

  // 忽略/删除通知
  async function dismissNotification(announcementId: string) {
    try {
      await api.dismissNotification(announcementId)

      // 从本地列表中移除
      const index = notifications.value.findIndex(n => n.id === announcementId)
      if (index !== -1) {
        notifications.value.splice(index, 1)
      }

      return true
    } catch (err: any) {
      console.error('忽略通知失败:', err)
      throw err
    }
  }

  // 获取公开公告（首页轮播）
  async function fetchPublicAnnouncements(page = 1, pageSize = 10) {
    loading.value = true
    error.value = null
    try {
      const result = await api.getPublicAnnouncements(page, pageSize)
      return result.items
    } catch (err: any) {
      console.error('获取公开公告失败:', err)
      error.value = err.message || '获取公告失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // SSE连接管理
  function connectSSE() {
    if (sseConnection.value && sseConnection.value.readyState === EventSource.OPEN) {
      console.log('[SSE] 已存在连接，跳过重新连接')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        console.log('[SSE] 未登录，跳过SSE连接')
        return
      }

      // 构建SSE URL：开发环境使用完整后端URL，生产环境使用相对URL
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''
      const url = apiBaseUrl
        ? `${apiBaseUrl}/api/v1/notifications/stream?token=${token}`
        : `/api/v1/notifications/stream?token=${token}`

      console.log('[SSE] 正在连接...', url.substring(0, 70) + '...')
      console.log('[SSE] API Base URL:', apiBaseUrl || '(使用相对路径，走Vite代理)')
      const eventSource = new EventSource(url)

      eventSource.onopen = () => {
        console.log('[SSE] ✅ 连接成功')
        sseConnected.value = true
        sseReconnectAttempts.value = 0 // 重置重连次数
        sseReconnectDelay.value = 1000 // 重置延迟
      }

      eventSource.onerror = (err) => {
        console.error('[SSE] ❌ 连接错误:', err)
        console.error('[SSE] EventSource state:', eventSource.readyState)
        sseConnected.value = false

        // 关闭旧连接
        if (eventSource.readyState === EventSource.CLOSED) {
          eventSource.close()
          sseConnection.value = null

          // 尝试重连（指数退避）
          if (sseReconnectAttempts.value < sseMaxReconnectAttempts) {
            sseReconnectAttempts.value++
            const delay = sseReconnectDelay.value

            console.log(`[SSE] 🔄 ${delay}ms 后尝试第 ${sseReconnectAttempts.value} 次重连...`)

            sseReconnectTimer.value = window.setTimeout(() => {
              sseReconnectDelay.value = Math.min(delay * 2, 30000) // 指数退避，最大30秒
              connectSSE()
            }, delay)
          } else {
            console.error('[SSE] ❌ 达到最大重连次数，停止重连')
          }
        }
      }

      // 监听新公告事件
      eventSource.addEventListener('announcement', (event) => {
        console.log('[SSE] 📢 收到 announcement 事件')
        try {
          const data = JSON.parse(event.data)
          console.log('[SSE] 公告数据:', data)
          handleNewAnnouncement(data)
        } catch (err) {
          console.error('[SSE] ❌ 解析公告消息失败:', err)
        }
      })

      // 监听通用消息事件
      eventSource.onmessage = (event) => {
        console.log('[SSE] 📨 收到 message 事件')
        try {
          const data = JSON.parse(event.data)
          handleSSEResponse(data)
        } catch (err) {
          console.error('[SSE] ❌ 解析消息失败:', err)
        }
      }

      sseConnection.value = eventSource
    } catch (err) {
      console.error('[SSE] ❌ 创建连接失败:', err)
    }
  }

  // 断开SSE连接
  function disconnectSSE() {
    // 清除重连定时器
    if (sseReconnectTimer.value) {
      clearTimeout(sseReconnectTimer.value)
      sseReconnectTimer.value = null
    }

    // 关闭连接
    if (sseConnection.value) {
      sseConnection.value.close()
      sseConnection.value = null
      sseConnected.value = false
      sseReconnectAttempts.value = 0
      sseReconnectDelay.value = 1000
      console.log('[SSE] 连接已断开')
    }
  }

  // 处理新公告推送
  function handleNewAnnouncement(data: any) {
    console.log('[SSE] 🎯 处理新公告推送:', data)

    if (data.type === 'new_announcement' && data.data) {
      const announcement = data.data
      console.log('[SSE] 📝 公告详情:', {
        id: announcement.id,
        title: announcement.title,
        priority: announcement.priority
      })

      // 添加到列表开头
      notifications.value.unshift({
        ...announcement,
        is_read: false,
        read_at: null,
        is_clicked: false,
        clicked_at: null,
      })

      // 增加未读数量
      unreadCount.value++
      console.log('[SSE] 📊 未读数量更新:', unreadCount.value)

      // 显示浏览器通知（如果用户授权）
      showBrowserNotification(announcement.title, announcement.content)

      // 显示应用内弹窗
      console.log('[SSE] 🎉 显示弹窗')
      showPopup(announcement)
    } else {
      console.log('[SSE] ⚠️ 消息格式不匹配:', data)
    }
  }

  // 处理SSE响应
  function handleSSEResponse(data: any) {
    console.log('收到SSE消息:', data)
  }

  // 显示浏览器通知
  function showBrowserNotification(title: string, body: string) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, {
        body: body.substring(0, 200) + (body.length > 200 ? '...' : ''),
        icon: '/favicon.ico',
        tag: 'announcement',
      })
    } else if ('Notification' in window && Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          new Notification(title, {
            body: body.substring(0, 200) + (body.length > 200 ? '...' : ''),
            icon: '/favicon.ico',
            tag: 'announcement',
          })
        }
      })
    }
  }

  // 请求浏览器通知权限
  function requestNotificationPermission() {
    if ('Notification' in window) {
      Notification.requestPermission().then(permission => {
        console.log('通知权限:', permission)
      })
    }
  }

  // 清空通知列表
  function clearNotifications() {
    notifications.value = []
  }

  // 设置选中的通知ID
  function setSelectedNotification(notificationId: string | null) {
    selectedNotificationId.value = notificationId
  }

  // 获取选中的通知ID
  function getSelectedNotification() {
    if (!selectedNotificationId.value) return null
    return notifications.value.find(n => n.id === selectedNotificationId.value) || null
  }

  // 显示新公告弹窗
  function showPopup(announcement: Announcement) {
    console.log('[Popup] 🚀 显示弹窗:', announcement.title)
    popupAnnouncement.value = announcement

    // 10秒后自动关闭
    if (popupTimer.value) clearTimeout(popupTimer.value)
    popupTimer.value = window.setTimeout(() => {
      console.log('[Popup] ⏰ 自动关闭弹窗')
      popupAnnouncement.value = null
    }, 10000)
  }

  // 关闭弹窗
  function closePopup() {
    popupAnnouncement.value = null
    if (popupTimer.value) {
      clearTimeout(popupTimer.value)
      popupTimer.value = null
    }
  }

  // 重置状态
  function reset() {
    notifications.value = []
    unreadCount.value = 0
    loading.value = false
    error.value = null
    disconnectSSE()
  }

  return {
    // 状态
    notifications,
    unreadCount,
    loading,
    error,
    sseConnected,
    selectedNotificationId,
    popupAnnouncement,

    // 计算属性
    hasUnread,
    pinnedNotifications,
    urgentNotifications,
    highPriorityNotifications,

    // 方法
    fetchMyNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    markAsClicked,
    dismissNotification,
    fetchPublicAnnouncements,
    connectSSE,
    disconnectSSE,
    requestNotificationPermission,
    clearNotifications,
    reset,
    setSelectedNotification,
    getSelectedNotification,
    showPopup,
    closePopup,
  }
})
