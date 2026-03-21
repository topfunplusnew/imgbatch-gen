/**
 * 通知系统调试工具
 */

export function testNotificationAPI() {
  console.log('=== 通知系统 API 测试 ===')

  // 检查认证状态
  const token = localStorage.getItem('access_token')
  console.log('✅ Token:', token ? '存在' : '不存在')

  if (token) {
    // 尝试获取通知列表
    console.log('📡 获取通知列表...')
    fetch('/api/v1/notifications/my?page=1&page_size=10', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(res => {
      console.log('✅ API响应状态:', res.status, res.statusText)
      return res.json()
    })
    .then(data => {
      console.log('✅ 通知列表数据:', data)
      console.log(`  - 总数: ${data.total}`)
      console.log(`  - 当前页: ${data.page}`)
      console.log(`  - 每页数量: ${data.page_size}`)
      console.log(`  - 项目数: ${data.items.length}`)

      if (data.items.length > 0) {
        console.log('  - 第一条通知:', data.items[0])
      } else {
        console.warn('⚠️ 通知列表为空！')
      }
    })
    .catch(err => {
      console.error('❌ API请求失败:', err)
    })

    // 尝试获取未读数量
    console.log('📡 获取未读数量...')
    fetch('/api/v1/notifications/my/unread-count', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(res => res.json())
    .then(data => {
      console.log('✅ 未读数量:', data)
    })
    .catch(err => {
      console.error('❌ 未读数量获取失败:', err)
    })
  } else {
    console.error('❌ 未登录，无法测试')
  }
}

export function testSSEConnection() {
  console.log('=== SSE 连接测试 ===')

  const token = localStorage.getItem('access_token')
  if (!token) {
    console.error('❌ 未登录')
    return
  }

  console.log('✅ Token 存在')

  const url = `/api/v1/notifications/stream?token=${token}`
  console.log('🔗 连接URL:', url.substring(0, 70) + '...')

  const eventSource = new EventSource(url)

  let connected = false
  let messageCount = 0
  const startTime = Date.now()

  // 5秒超时检查
  const timeoutId = setTimeout(() => {
    if (!connected) {
      console.error('❌ SSE连接超时（5秒未连接）')
      console.error('📊 EventSource state:', eventSource.readyState)
      console.error('   (0=CONNECTING, 1=OPEN, 2=CLOSED)')
      eventSource.close()
    }
  }, 5000)

  eventSource.onopen = () => {
    connected = true
    clearTimeout(timeoutId)
    const connectTime = Date.now() - startTime
    console.log(`✅ SSE连接成功 (耗时: ${connectTime}ms)`)
    console.log('📊 连接状态:', eventSource.readyState, '(OPEN)')
  }

  eventSource.onerror = (err) => {
    console.error('❌ SSE连接错误:', err)
    console.error('📊 连接状态:', eventSource.readyState)
    console.error('   (0=CONNECTING, 1=OPEN, 2=CLOSED)')
  }

  eventSource.addEventListener('announcement', (event) => {
    messageCount++
    console.log(`📢 收到公告 #${messageCount}:`, event.data)
    try {
      const data = JSON.parse(event.data)
      console.log('   解析后:', data)
    } catch (e) {
      console.error('   解析失败:', e)
    }
  })

  eventSource.onmessage = (event) => {
    messageCount++
    console.log(`📨 收到消息 #${messageCount}:`, event.data)
  }

  // 15秒后结束测试
  setTimeout(() => {
    console.log(`🔚 测试结束，共收到 ${messageCount} 条消息`)
    eventSource.close()
  }, 15000)
}

// 暴露到全局作用域（仅开发模式）
if (import.meta.env.DEV) {
  (window as any).notificationDebug = {
    testAPI: testNotificationAPI,
    testSSE: testSSEConnection,
  }
  console.log('💡 通知调试工具已加载')
  console.log('   使用方法:')
  console.log('   - notificationDebug.testAPI()     测试通知 API')
  console.log('   - notificationDebug.testSSE()     测试 SSE 连接')
}
