import { defineStore } from 'pinia'
import { api } from '@/services/api'

function parseHistoryTimestamp(value: string | number | null | undefined): number {
  if (value === null || value === undefined || value === '') {
    return 0
  }

  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : 0
  }

  const normalizedValue = value.trim()
  if (!normalizedValue) {
    return 0
  }

  const hasExplicitTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(normalizedValue)
  const normalizedIsoValue = hasExplicitTimezone
    ? normalizedValue
    : `${normalizedValue.replace(' ', 'T')}Z`

  const parsedTimestamp = Date.parse(normalizedIsoValue)
  if (Number.isFinite(parsedTimestamp)) {
    return parsedTimestamp
  }

  const fallbackTimestamp = new Date(normalizedValue).getTime()
  return Number.isFinite(fallbackTimestamp) ? fallbackTimestamp : 0
}

export interface HistorySession {
  id: string
  title: string
  createdAt: number
  updatedAt?: number
  model: string
  messages: Array<{
    id: number
    role: 'user' | 'assistant'
    content: string
    model?: string
    provider?: string
    createdAt?: number
    images?: Array<{ url: string; alt: string }>
    files?: Array<{
      id: number
      original_filename: string
      file_url: string
      file_size: number
      file_type: string
      category: string
    }>
  }>
  imageCount: number
  totalFiles: number
  messageCount?: number
  loadedFromServer?: boolean
}

export const useHistoryStore = defineStore('history', {
  state: () => {
    // 只从后端数据库获取数据，不使用本地存储
    return {
      sessions: [] as HistorySession[],
      searchQuery: '',
      filterDate: '',
      viewMode: 'list' as 'list' | 'grid',
      isLoading: false,
      lastSyncTime: 0,
    }
  },
  getters: {
    filteredSessions(): HistorySession[] {
      let result = [...this.sessions]
      
      // 搜索过滤
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        result = result.filter(session => 
          session.title.toLowerCase().includes(query) ||
          session.messages.some(msg => msg.content.toLowerCase().includes(query))
        )
      }
      
      // 日期过滤
      if (this.filterDate) {
        const filterDate = new Date(this.filterDate).getTime()
        const nextDay = filterDate + 24 * 60 * 60 * 1000
        result = result.filter(session => 
          session.createdAt >= filterDate && session.createdAt < nextDay
        )
      }
      
      // 按时间倒序排序
      return result.sort((a, b) => b.createdAt - a.createdAt)
    },
    allModels(): string[] {
      const models = new Set<string>()
      this.sessions.forEach(session => {
        if (session.model) {
          models.add(session.model)
        }
      })
      return Array.from(models).sort()
    },
  },
  actions: {
    // 从后端加载历史记录
    async loadFromServer() {
      if (this.isLoading) return

      this.isLoading = true
      try {
        const data = await api.getConversationHistoryList(100, 0)

        if (data && data.conversations) {
          const serverSessions = data.conversations.map((conv: any) => ({
            id: conv.session_id,
            title: conv.title || '无标题会话',
            createdAt: parseHistoryTimestamp(conv.created_at),
            updatedAt: conv.updated_at ? parseHistoryTimestamp(conv.updated_at) : undefined,
            model: conv.model || 'unknown',
            messages: [],  // 详细消息需要单独获取
            imageCount: Number(conv.image_count || 0),
            totalFiles: 0,
            messageCount: Number(conv.message_count || 0),
            loadedFromServer: true
          }))

          // 只使用服务器记录，不合并本地记录
          this.sessions = serverSessions
          this.lastSyncTime = Date.now()

          console.log(`从服务器加载了 ${serverSessions.length} 个历史记录`)
        }
      } catch (error) {
        console.error('从服务器加载历史记录失败:', error)
      } finally {
        this.isLoading = false
      }
    },

    // 获取特定会话的详细历史（包含文件）
    async loadSessionDetails(conversationId: string) {
      try {
        const data = await api.getConversationHistoryDetail(conversationId)

        if (data && data.messages) {
          // 转换消息格式
          const messages = data.messages.map((msg: any) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            model: msg.model,
            provider: msg.provider,
            createdAt: parseHistoryTimestamp(msg.created_at),
            images: msg.images ? msg.images.map((url: string) => ({ url, alt: '生成的图像' })) : [],
            files: msg.files || []
          }))

          // 更新本地会话
          const sessionIndex = this.sessions.findIndex(s => s.id === conversationId)
          if (sessionIndex !== -1) {
            this.sessions[sessionIndex].messages = messages
            this.sessions[sessionIndex].imageCount = data.image_count || 0
            this.sessions[sessionIndex].totalFiles = data.file_count || 0
            this.sessions[sessionIndex].messageCount = data.message_count || messages.length
            this.sessions[sessionIndex].updatedAt = data.updated_at ? parseHistoryTimestamp(data.updated_at) : this.sessions[sessionIndex].updatedAt
          }

          return { messages, files: data.files || [] }
        }
      } catch (error) {
        console.error('加载会话详情失败:', error)
        return null
      }
    },

    addSession(session: Omit<HistorySession, 'id' | 'createdAt' | 'imageCount' | 'totalFiles'>) {
      const newSession: HistorySession = {
        ...session,
        // 如果传入的session已经有id属性，则使用它，否则生成新的
        id: (session as any).id || `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        createdAt: Date.now(),
        imageCount: session.messages.reduce((count, msg) =>
          count + (msg.images?.length || 0), 0
        ),
        totalFiles: session.messages.reduce((count, msg) =>
          count + (msg.files?.length || 0), 0
        ),
      }
      this.sessions.unshift(newSession)
      return newSession
    },
    deleteSession(sessionId: string) {
      const index = this.sessions.findIndex(s => s.id === sessionId)
      if (index > -1) {
        this.sessions.splice(index, 1)
      }
    },
    deleteSessions(sessionIds: string[]) {
      this.sessions = this.sessions.filter(s => !sessionIds.includes(s.id))
    },
    updateSession(sessionId: string, updates: Partial<HistorySession>) {
      const index = this.sessions.findIndex(s => s.id === sessionId)
      if (index > -1) {
        Object.assign(this.sessions[index], updates)
      }
    },
    setSearchQuery(query: string) {
      this.searchQuery = query
    },
    setFilterDate(date: string) {
      this.filterDate = date
    },
    setViewMode(mode: 'list' | 'grid') {
      this.viewMode = mode
    },
    clearFilters() {
      this.searchQuery = ''
      this.filterDate = ''
    },

    // 刷新历史记录
    async refresh() {
      await this.loadFromServer()
    },
  },
})
