/**
 * SSE (Server-Sent Events) Composable
 *
 * 用于管理SSE连接的复用逻辑
 */

import { ref, onUnmounted } from 'vue'

export interface SSEMessage {
  type: string
  data: any
  id?: string
}

export interface SSEOptions {
  onMessage?: (data: any) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useSSE(endpoint: string, options: SSEOptions = {}) {
  const {
    onMessage,
    onError,
    onOpen,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options

  const eventSource = ref<EventSource | null>(null)
  const connected = ref(false)
  const error = ref<Event | null>(null)
  const reconnectAttempts = ref(0)
  const manuallyClosed = ref(false)

  /**
   * 连接SSE
   */
  function connect(token?: string) {
    // 如果已经连接，不再重复连接
    if (eventSource.value && eventSource.value.readyState === EventSource.OPEN) {
      console.log('SSE already connected')
      return
    }

    // 构建URL
    let url = endpoint
    if (token) {
      const separator = endpoint.includes('?') ? '&' : '?'
      url = `${endpoint}${separator}token=${token}`
    }

    console.log('Connecting to SSE:', url)

    try {
      eventSource.value = new EventSource(url)

      eventSource.value.onopen = () => {
        console.log('SSE connected')
        connected.value = true
        error.value = null
        reconnectAttempts.value = 0
        onOpen?.()
      }

      eventSource.value.onerror = (err) => {
        console.error('SSE error:', err)
        error.value = err
        connected.value = false
        onError?.(err)

        // 如果不是手动关闭的，尝试重连
        if (!manuallyClosed.value && reconnectAttempts.value < maxReconnectAttempts) {
          reconnectAttempts.value++
          console.log(`Reconnecting... Attempt ${reconnectAttempts.value}/${maxReconnectAttempts}`)
          setTimeout(() => {
            if (!manuallyClosed.value) {
              connect(token)
            }
          }, reconnectInterval)
        }
      }

      eventSource.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage?.(data)
        } catch (err) {
          console.error('Failed to parse SSE message:', err)
        }
      }

      // 监听特定事件类型
      eventSource.value.addEventListener('announcement', (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          onMessage?.({ type: 'announcement', data, ...event })
        } catch (err) {
          console.error('Failed to parse announcement event:', err)
        }
      })

    } catch (err) {
      console.error('Failed to create EventSource:', err)
      error.value = err as Event
    }
  }

  /**
   * 断开连接
   */
  function disconnect() {
    manuallyClosed.value = true
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
      connected.value = false
      console.log('SSE disconnected')
    }
  }

  /**
   * 重新连接
   */
  function reconnect() {
    disconnect()
    manuallyClosed.value = false
    reconnectAttempts.value = 0
    // 延迟一点再重连
    setTimeout(() => {
      connect()
    }, 100)
  }

  /**
   * 添加事件监听器
   */
  function addEventListener(eventType: string, callback: (data: any) => void) {
    if (eventSource.value) {
      eventSource.value.addEventListener(eventType, (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          callback(data)
        } catch (err) {
          console.error(`Failed to parse ${eventType} event:`, err)
        }
      })
    }
  }

  /**
   * 移除事件监听器
   */
  function removeEventListener(eventType: string, callback: (data: any) => void) {
    if (eventSource.value) {
      eventSource.value.removeEventListener(eventType, callback as EventListener)
    }
  }

  // 组件卸载时自动断开连接
  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    error,
    eventSource,
    reconnectAttempts,
    connect,
    disconnect,
    reconnect,
    addEventListener,
    removeEventListener,
  }
}

/**
 * 通知SSE Hook
 *
 * 专门用于通知系统的SSE连接
 */
export function useNotificationSSE(token?: string) {
  const { connected, connect, disconnect } = useSSE(
    '/api/v1/notifications/stream',
    {
      token,
      onMessage: (data) => {
        console.log('Notification SSE message:', data)
        // 可以在这里触发全局事件或更新状态
      },
      onError: (err) => {
        console.error('Notification SSE error:', err)
      },
      onOpen: () => {
        console.log('Notification SSE connected')
      },
    }
  )

  // 如果提供了token，自动连接
  if (token) {
    connect(token)
  }

  return {
    connected,
    connect,
    disconnect,
  }
}
