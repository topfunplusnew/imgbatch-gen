/**
 * API服务模块
 * 封装所有与后端API的交互
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { useApiConfigStore } from '@/store/useApiConfigStore'

// API响应类型定义
export interface TaskStageEvent {
  stage: string
  label: string
  message: string
  status: string
  progress: number
  attempt: number
  timestamp: string
}

export interface ImageTask {
  task_id: string
  status: 'pending' | 'processing' | 'running' | 'completed' | 'failed' | 'cancelled'
  params?: any
  result?: any
  images?: any[]
  error?: string
  progress?: number
  stage?: string
  stage_label?: string
  stage_message?: string
  attempt?: number
  updated_at?: string
  stage_history?: TaskStageEvent[]
  metadata?: Record<string, any>
}

export interface BatchStageOverviewItem {
  stage: string
  label: string
  count: number
}

export interface BatchStatusDetail {
  current_stage: string
  current_stage_label: string
  current_stage_message: string
  progress_percent: number
  pending_tasks: number
  running_tasks: number
  completed_tasks: number
  failed_tasks: number
  stage_overview: BatchStageOverviewItem[]
}

export interface BatchTaskStatus {
  batch_id: string
  status: 'pending' | 'processing' | 'running' | 'completed' | 'failed' | 'cancelled'
  tasks?: ImageTask[]
  total: number
  completed: number
  failed: number
  pending?: number
  running?: number
  progress?: number
  stage?: string
  stage_label?: string
  stage_message?: string
  status_detail?: BatchStatusDetail
  created_at?: string
  completed_at?: string
  updated_at?: string
}

export interface ChatMessage {
  role: string
  content: string
  images?: string[]
  metadata?: Record<string, any>
}

export interface ChatRequest {
  messages: ChatMessage[]
  session_id?: string
  enable_context?: boolean
  files?: string[]
  stream?: boolean
  model?: string
  model_type?: string
  // 图像生成参数
  image_params?: {
    width?: number
    height?: number
    style?: string
    quality?: string
    n?: number
    negative_prompt?: string
    seed?: number
  }
}

export interface Intent {
  type: string
  confidence: number
  parameters: Record<string, any>
  reasoning: string
}

export interface ChatResponse {
  message: ChatMessage
  intent?: Intent
  task_id?: string
  batch_id?: string
  requires_action: boolean
  metadata?: Record<string, any>
}

export interface GenerateRequest {
  prompt: string
  width?: number
  height?: number
  style?: string
  quality?: string
  n?: number
  provider?: string
  model_name?: string
  extra_params?: Record<string, any>
}

export interface ModelInfo {
  id: string
  name: string
  provider: string
  type: 'image' | 'llm' | 'embedding'
}

export interface BatchGenerateRequest {
  prompts?: string[]
  file?: File
  provider?: string
  default_params?: {
    width?: number
    height?: number
    style?: string
    quality?: string
  }
}

// 生成或获取持久化的 client_id cookie
function ensureClientId(): string {
  const key = 'client_id'
  let clientId = document.cookie
    .split('; ')
    .find(row => row.startsWith(key + '='))
    ?.split('=')[1]

  if (!clientId) {
    clientId = 'c_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
    // 有效期1年
    const expires = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toUTCString()
    document.cookie = `${key}=${clientId}; expires=${expires}; path=/; SameSite=Lax`
  }
  return clientId
}

function buildModelAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {}
  const token = localStorage.getItem('access_token')
  const apiConfig = useApiConfigStore()

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  if (apiConfig.apiKey) {
    headers['X-Model-Api-Key'] = apiConfig.apiKey
  }

  return headers
}

// 创建axios实例
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    timeout: 600000, // 10分钟超时（支持超大文件）
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: false, // 开发环境下禁用，避免CORS问题
  })

  // 请求拦截器
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const apiConfig = useApiConfigStore()

      // 确保 client_id cookie 存在（用于区分不同客户端的历史记录）
      ensureClientId()

      // 设置baseURL（从store中获取）
      if (apiConfig.apiEndpoint) {
        config.baseURL = apiConfig.apiEndpoint
      }

      Object.entries(buildModelAuthHeaders()).forEach(([key, value]) => {
        config.headers[key] = value
      })

      // 添加请求日志（开发环境）
      if (import.meta.env.DEV) {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
          params: config.params,
          data: config.data,
        })
      }

      return config
    },
    (error: AxiosError) => {
      console.error('[API Request Error]', error)
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // 添加响应日志（开发环境）
      if (import.meta.env.DEV) {
        console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
          status: response.status,
          data: response.data,
        })
      }

      return response
    },
    (error: AxiosError) => {
      // 统一错误处理
      const errorMessage = handleApiError(error)
      console.error('[API Response Error]', errorMessage)

      // 401 未授权 - 自动跳转到登录页面
      if (error.response?.status === 401) {
        // 动态导入 store 避免循环依赖
        import('@/store/useAppStore').then(({ useAppStore }) => {
          const appStore = useAppStore()
          if (appStore.currentPage !== 'login') {
            appStore.setCurrentPage('login')
          }
        })
      }

      // 可以在这里添加全局错误提示
      // 例如：showToast(errorMessage)

      return Promise.reject(error)
    }
  )

  return client
}

// 错误处理函数
const handleApiError = (error: AxiosError): string => {
  if (error.response) {
    // 服务器返回错误响应
    const status = error.response.status
    const data = error.response.data as any

    switch (status) {
      case 400:
        return data?.detail || '请求参数错误'
      case 401:
        return '未授权，请检查API密钥'
      case 403:
        return data?.detail || '禁止访问，需要管理员权限'
      case 404:
        return '请求的资源不存在'
      case 500:
        return data?.detail || '服务器内部错误'
      default:
        return data?.detail || `请求失败 (${status})`
    }
  } else if (error.request) {
    // 请求已发出但没有收到响应
    return '网络连接失败，请检查服务器地址'
  } else {
    // 请求配置错误
    return error.message || '请求配置错误'
  }
}

// 创建API客户端实例
const apiClient = createApiClient()

// API方法集合
export const api = {
  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await apiClient.get('/health')
    return response.data
  },

  /**
   * 生成图像
   */
  async generateImage(request: GenerateRequest): Promise<ImageTask> {
    const response = await apiClient.post('/api/v1/generate', request)
    return response.data
  },

  /**
   * 查询任务状态
   */
  async getTaskStatus(taskId: string): Promise<ImageTask> {
    const response = await apiClient.get(`/api/v1/tasks/${taskId}`)
    return response.data
  },

  /**
   * 获取模型列表（通过后端API）
   */
  async getModels(modelType?: string, keyword?: string): Promise<{ total: number; models: any[] }> {
    const params: any = {}
    if (modelType) params.model_type = modelType
    if (keyword) params.keyword = keyword

    const response = await apiClient.get('/api/v1/models', { params })
    const data = response.data

    if (data && data.models) {
      let models = data.models.map((item: any) => ({
          id: item.model_name,
          name: item.model_name,
          model_name: item.model_name,
          description: item.description,
          provider: item.vendor_name,
          vendor_name: item.vendor_name,
          model_type: item.model_type,
          tags: Array.isArray(item.tags) ? item.tags : (item.tags ? item.tags.split(',') : []),
          is_async: item.is_async
        }))

        // 根据model_type过滤
        if (modelType === 'image') {
          models = models.filter((m: any) => m.model_type === '图像')
        } else if (modelType === 'chat') {
          models = models.filter((m: any) => m.model_type === '文本')
        }

        // 根据关键词搜索
        if (keyword) {
          const lowerKeyword = keyword.toLowerCase()
          models = models.filter((m: any) =>
            m.model_name.toLowerCase().includes(lowerKeyword) ||
            (m.description && m.description.toLowerCase().includes(lowerKeyword)) ||
            (m.tags && m.tags.some((tag: string) => tag.toLowerCase().includes(lowerKeyword)))
          )
        }

        return { total: models.length, models }
    }

    return { total: 0, models: [] }
  },

  /**
   * 获取指定模型详细信息
   */
  async getModelInfo(modelName: string): Promise<ModelInfo & { vendor_id?: string; supported_endpoint_types?: string[] }> {
    const response = await apiClient.get(`/api/v1/models/${modelName}`)
    return response.data
  },

  /**
   * 刷新模型配置
   */
  async refreshModels(): Promise<{ message: string; total_models: number; last_update: string | null }> {
    const response = await apiClient.post('/api/v1/models/refresh')
    return response.data
  },

  /**
   * 批量生成图像（支持文件上传或prompts列表）
   */
  async batchGenerate(request: BatchGenerateRequest, onProgress?: (progress: number) => void): Promise<any> {
    const formData = new FormData()

    // 添加prompts（如果有）
    if (request.prompts && request.prompts.length > 0) {
      request.prompts.forEach((prompt) => {
        formData.append('prompts', prompt)
      })
    }

    // 添加文件（如果有）
    if (request.file) {
      formData.append('file', request.file)
    }

    // 添加provider（如果有）
    if (request.provider) {
      formData.append('provider', request.provider)
    }

    // 添加default_params（如果有）
    if (request.default_params) {
      formData.append('default_params', JSON.stringify(request.default_params))
    }

    const response = await apiClient.post('/api/v1/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })

    return response.data
  },

  /**
   * 查询批量任务状态
   */
  async getBatchTaskStatus(batchId: string): Promise<BatchTaskStatus> {
    const response = await apiClient.get(`/api/v1/batch/${batchId}`)
    return response.data
  },

  /**
   * 列出所有任务
   */
  async listTasks(status?: string): Promise<ImageTask[]> {
    const params: any = {}
    if (status) params.status = status

    const response = await apiClient.get('/api/v1/tasks', { params })
    return response.data
  },

  /**
   * 统一AI助手聊天接口
   */
  async assistantChat(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post('/api/v1/assistant/chat', request)
    return response.data
  },

  /**
   * 流式AI助手聊天接口（SSE）
   */
  assistantChatStream(
    request: ChatRequest,
    callbacks: {
      onChunk: (content: string) => void
      onDone: () => void
      onError: (error: string) => void
    }
  ): { abort: () => void } {
    const controller = new AbortController()

    const apiConfig = useApiConfigStore()
    const baseURL = apiConfig.apiEndpoint || ''

    fetch(`${baseURL}/api/v1/assistant/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...buildModelAuthHeaders(),
      },
      body: JSON.stringify({ ...request, stream: true }),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          callbacks.onError(`请求失败 (${response.status})`)
          return
        }

        const reader = response.body?.getReader()
        if (!reader) {
          callbacks.onError('无法读取响应流')
          return
        }

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed || !trimmed.startsWith('data: ')) continue

            const data = trimmed.slice(6)
            if (data === '[DONE]') {
              callbacks.onDone()
              return
            }

            try {
              const parsed = JSON.parse(data)
              if (parsed.error) {
                callbacks.onError(parsed.error)
                return
              }
              if (parsed.content) {
                callbacks.onChunk(parsed.content)
              }
            } catch {
              // ignore malformed JSON
            }
          }
        }

        callbacks.onDone()
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          callbacks.onError(err.message || '流式请求失败')
        }
      })

    return { abort: () => controller.abort() }
  },

  /**
   * 查询助手任务状态
   */
  async getAssistantTask(taskId: string): Promise<ImageTask> {
    const response = await apiClient.get(`/api/v1/assistant/tasks/${taskId}`)
    return response.data
  },

  /**
   * 查询助手批量任务状态
   */
  async getAssistantBatchTask(batchId: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/assistant/batch/${batchId}`)
    return response.data
  },

  /**
   * 上传文件到MinIO（直传，无大小限制）
   */
  async uploadFileToMinio(file: File, onProgress?: (progress: number) => void): Promise<{ file_id: string; filename: string; url: string; size: number }> {
    try {
      console.log(`[MinIO上传] 开始上传文件: ${file.name}, 大小: ${(file.size / 1024 / 1024).toFixed(2)}MB`)

      // 1. 获取MinIO预签名上传URL
      const presignedResponse = await apiClient.post('/api/v1/files/minio/presigned-url', null, {
        params: { filename: file.name }
      })
      const { upload_url, file_url, filename } = presignedResponse.data

      console.log(`[MinIO上传] 获取预签名URL成功: ${upload_url}`)

      // 2. 直接上传到MinIO
      const uploadResponse = await fetch(upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type || 'application/octet-stream',
        },
      })

      if (!uploadResponse.ok) {
        throw new Error(`MinIO上传失败: ${uploadResponse.status} ${uploadResponse.statusText}`)
      }

      console.log(`[MinIO上传] 上传成功: ${file_url}`)
      if (onProgress) onProgress(100)

      // 3. 返回文件信息
      return {
        file_id: filename,
        filename: file.name,
        url: file_url,
        size: file.size
      }
    } catch (error: any) {
      console.error('[MinIO上传] 失败:', error)
      throw error
    }
  },

  /**
   * 上传文件（优先使用MinIO直传，无大小限制）
   */
  async uploadFile(file: File, onProgress?: (progress: number) => void): Promise<{ file_id: string; filename: string; url: string; size: number }> {
    // 使用MinIO直传（无大小限制），不再回退到传统上传
    return await this.uploadFileToMinio(file, onProgress)
  },

  /**
   * 批量上传多个文件（使用MinIO直传）
   */
  async uploadFiles(files: File[], onProgress?: (progress: number, current: number, total: number) => void): Promise<Array<{ file_id: string; filename: string; url: string; size: number }>> {
    const results = []

    for (let i = 0; i < files.length; i++) {
      const file = files[i]

      try {
        const result = await this.uploadFile(file, (progress) => {
          if (onProgress) {
            const totalProgress = Math.round(((i * 100 + progress) / files.length))
            onProgress(totalProgress, i + 1, files.length)
          }
        })

        results[i] = result
        console.log(`[批量上传] 文件 ${file.name} 上传成功`)
      } catch (error: any) {
        console.error(`[批量上传] 文件 ${file.name} 上传失败:`, error)
        throw error
      }
    }

    console.log(`[批量上传] 全部完成，成功上传 ${results.length} 个文件`)
    return results
  },

  // ==================== 认证相关API ====================

  /**
   * 用户名注册
   */
  async registerByUsername(data: { username: string; password: string; password_confirmation: string; invite_code?: string }): Promise<{
    access_token: string
    refresh_token: string
    token_type: string
    user: User
  }> {
    const response = await apiClient.post('/api/v1/auth/register', data)
    return response.data
  },

  /**
   * 用户名登录
   */
  async loginByUsername(username: string, password: string): Promise<{
    access_token: string
    refresh_token: string
    token_type: string
    user: User
  }> {
    const response = await apiClient.post('/api/v1/auth/login', { username, password })
    return response.data
  },

  /**
   * 刷新Token
   */
  async refreshToken(refreshToken: string): Promise<{ access_token: string; token_type: string }> {
    const response = await apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/api/v1/auth/me')
    return response.data
  },

  /**
   * 更新用户资料
   */
  async updateProfile(data: { username?: string }): Promise<User> {
    const response = await apiClient.patch('/api/v1/auth/profile', data)
    return response.data
  },

  /**
   * 修改密码
   */
  async changePassword(data: {
    old_password: string
    new_password: string
  }): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/api/v1/auth/change-password', data)
    return response.data
  },

  /**
   * 登出
   */
  async logout(): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/api/v1/auth/logout')
    return response.data
  },

  /**
   * 发送验证码
   */
  async sendVerifyCode(identifier: string, authType: 'email' | 'phone'): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/api/v1/auth/send-code', {
      identifier,
      auth_type: authType
    })
    return response.data
  },

  /**
   * 重置密码
   */
  async resetPassword(identifier: string, code: string, newPassword: string, authType: 'email' | 'phone'): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/api/v1/auth/reset-password', {
      identifier,
      code,
      new_password: newPassword,
      auth_type: authType
    })
    return response.data
  },

  // ==================== 签到相关API ====================

  /**
   * 每日签到
   */
  async dailyCheckin(): Promise<{ success: boolean; reward_points: number; consecutive_days: number; gift_points: number }> {
    const response = await apiClient.post('/api/v1/checkin/daily')
    return response.data
  },

  /**
   * 获取签到状态
   */
  async getCheckinStatus(): Promise<{ can_checkin: boolean; consecutive_days: number; gift_points: number }> {
    const response = await apiClient.get('/api/v1/checkin/status')
    return response.data
  },

  // ==================== 邀请码相关API ====================

  /**
   * 获取我的邀请码
   */
  async getMyInviteCode(): Promise<{ invite_code: string; total_invite_count: number; total_reward_points: number }> {
    const response = await apiClient.get('/api/v1/referral/my-code')
    return response.data
  },

  /**
   * 使用邀请码
   */
  async applyInviteCode(inviteCode: string): Promise<{ success: boolean; inviter_id: string; reward_points: number }> {
    const response = await apiClient.post('/api/v1/referral/apply', { invite_code: inviteCode })
    return response.data
  },

  /**
   * 获取邀请记录
   */
  async getInviteRecords(): Promise<Array<{ user_id: string; username: string; phone: string; created_at: string }>> {
    const response = await apiClient.get('/api/v1/referral/records')
    return response.data
  },

  /**
   * 获取邀请统计
   */
  async getInviteStats(): Promise<{ invite_code: string; total_invite_count: number; total_reward_points: number }> {
    const response = await apiClient.get('/api/v1/referral/stats')
    return response.data
  },

  // ==================== 下载记录相关API ====================

  /**
   * 记录下载
   */
  async recordDownload(data: { image_url: string; file_name: string; file_size?: number; request_id?: string; consumption_record_id?: string }): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/api/v1/download/record', data)
    return response.data
  },

  /**
   * 获取下载记录
   */
  async getDownloadRecords(limit: number = 50, offset: number = 0): Promise<Array<{
    id: string
    image_url: string
    file_name: string
    file_size: number
    request_id: string
    consumption_record_id: string
    download_ip: string
    created_at: string
  }>> {
    const response = await apiClient.get('/api/v1/download/records', { params: { limit, offset } })
    return response.data
  },

  /**
   * 获取下载记录总数
   */
  async getDownloadRecordsCount(): Promise<{ count: number }> {
    const response = await apiClient.get('/api/v1/download/records/count')
    return response.data
  },

  // ==================== 账户相关API ====================

  /**
   * 获取账户信息
   */
  async getAccountInfo(): Promise<AccountInfo> {
    const response = await apiClient.get('/api/v1/account')
    return response.data
  },

  /**
   * 获取交易记录
   */
  async getTransactions(limit: number = 50, offset: number = 0): Promise<Transaction[]> {
    const response = await apiClient.get('/api/v1/account/transactions', { params: { limit, offset } })
    return response.data
  },

  /**
   * 获取消费记录
   */
  async getConsumptionRecords(limit: number = 50, offset: number = 0): Promise<ConsumptionRecord[]> {
    const response = await apiClient.get('/api/v1/account/consumption', { params: { limit, offset } })
    return response.data
  },

  /**
   * 获取模型价格列表
   */
  async getModelPricing(): Promise<ModelPrice[]> {
    const response = await apiClient.get('/api/v1/account/models/pricing')
    return response.data
  },

  /**
   * 获取充值选项
   */
  async getRechargeOptions(): Promise<RechargeOption[]> {
    const response = await apiClient.get('/api/v1/account/recharge/options')
    return response.data
  },

  /**
   * 获取计费配置
   */
  async getBillingConfig(): Promise<BillingConfig> {
    const response = await apiClient.get('/api/v1/account/billing/config')
    return response.data
  },

  // ==================== 支付相关API ====================

  /**
   * 创建充值订单
   */
  async createRechargeOrder(rechargeOptionId: string, paymentMethod: 'wechat' | 'alipay'): Promise<{
    order_id: string
    amount: number
    amount_yuan: number
    qr_code_url: string
    status: string
    expire_time: string
  }> {
    const response = await apiClient.post('/api/v1/payment/create', {
      recharge_option_id: rechargeOptionId,
      payment_method: paymentMethod
    })
    return response.data
  },

  /**
   * 创建H5支付订单（手机网页支付）
   */
  async createH5RechargeOrder(rechargeOptionId: string, clientIp: string): Promise<{
    order_id: string
    user_id: string
    order_type: string
    amount: number
    amount_yuan: number
    payment_method: string
    status: string
    subject: string
    created_at: string
    expire_time: string | null
    qr_code_url: string | null
    pay_url: string | null
  }> {
    const response = await apiClient.post('/api/v1/payment/create-h5', {
      recharge_option_id: rechargeOptionId,
      client_ip: clientIp
    })
    return response.data
  },

  /**
   * 获取支付二维码
   */
  async getPaymentQrcode(orderId: string): Promise<{
    order_id: string
    qr_code_url: string
    pay_url: string | null
    amount: number
    amount_yuan: number
    status: string
    expire_time: string
  }> {
    const response = await apiClient.get(`/api/v1/payment/qrcode/${orderId}`)
    return response.data
  },

  /**
   * 查询订单状态
   */
  async getOrderStatus(orderId: string): Promise<{
    order_id: string
    status: string
    amount: number
    amount_yuan: number
    paid_at: string | null
  }> {
    const response = await apiClient.get(`/api/v1/payment/status/${orderId}`)
    return response.data
  },

  /**
   * 获取订单列表
   */
  async getOrders(limit: number = 50, offset: number = 0): Promise<Order[]> {
    const response = await apiClient.get('/api/v1/payment/orders', { params: { limit, offset } })
    return response.data
  },

  /**
   * 取消订单
   */
  async cancelOrder(orderId: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(`/api/v1/payment/cancel/${orderId}`)
    return response.data
  },

  // ==================== 生成历史相关API ====================

  /**
   * 获取生成历史记录
   */
  async getGenerationHistory(limit: number = 20, offset: number = 0, status?: string): Promise<GenerationRecord[]> {
    const params: any = { limit, offset }
    if (status) params.status = status

    const response = await apiClient.get('/api/v1/generate/history', { params })
    return response.data
  },

  /**
   * 获取生成历史记录总数
   */
  async getGenerationHistoryCount(status?: string): Promise<{ count: number }> {
    const params: any = {}
    if (status) params.status = status

    const response = await apiClient.get('/api/v1/generate/history/count', { params })
    return response.data
  },

  /**
   * 获取统一生成历史（对话 + 异步）
   */
  async getUnifiedGenerationHistory(
    limit: number = 20,
    offset: number = 0,
    status?: string
  ): Promise<UnifiedGenerationRecord[]> {
    const params: any = { limit, offset }
    if (status) params.status = status

    const response = await apiClient.get('/api/v1/generate/history/unified', { params })
    return response.data
  },

  /**
   * 获取统一生成历史总数
   */
  async getUnifiedGenerationHistoryCount(status?: string): Promise<{ count: number }> {
    const params: any = {}
    if (status) params.status = status

    const response = await apiClient.get('/api/v1/generate/history/unified/count', { params })
    return response.data
  },

  // ==================== 管理员相关API ====================

  /**
   * 获取用户列表
   */
  async getAdminUsers(params?: {
    keyword?: string
    status?: string
    role?: string
    limit?: number
    offset?: number
  }): Promise<AdminUserListItem[]> {
    const response = await apiClient.get('/api/v1/admin/users', { params })
    return response.data
  },

  /**
   * 获取用户总数
   */
  async getAdminUsersCount(params?: {
    keyword?: string
    status?: string
    role?: string
  }): Promise<{ count: number }> {
    const response = await apiClient.get('/api/v1/admin/users/count', { params })
    return response.data
  },

  /**
   * 获取用户详情
   */
  async getAdminUserDetail(userId: string): Promise<AdminUserDetail> {
    const response = await apiClient.get(`/api/v1/admin/users/${userId}`)
    return response.data
  },

  /**
   * 调整用户积分
   */
  async adjustUserPoints(userId: string, data: {
    points_change: number
    reason: string
  }): Promise<{ success: boolean; old_points: number; new_points: number; points_change: number }> {
    const response = await apiClient.post(`/api/v1/admin/users/${userId}/points`, data)
    return response.data
  },

  /**
   * 调整用户余额
   */
  async adjustUserBalance(userId: string, data: {
    points_change: number
    reason: string
  }): Promise<{ success: boolean; old_balance: number; new_balance: number; balance_change: number }> {
    const response = await apiClient.post(`/api/v1/admin/users/${userId}/balance`, data)
    return response.data
  },

  /**
   * 封禁用户
   */
  async banUser(userId: string, data: { reason: string }): Promise<{
    success: boolean
    old_status: string
    new_status: string
  }> {
    const response = await apiClient.post(`/api/v1/admin/users/${userId}/ban`, data)
    return response.data
  },

  /**
   * 解封用户
   */
  async unbanUser(userId: string): Promise<{
    success: boolean
    old_status: string
    new_status: string
  }> {
    const response = await apiClient.post(`/api/v1/admin/users/${userId}/unban`)
    return response.data
  },

  /**
   * 设置管理员
   */
  async setAdmin(userId: string): Promise<{
    success: boolean
    old_role: string
    new_role: string
  }> {
    const response = await apiClient.post(`/api/v1/admin/users/${userId}/set-admin`)
    return response.data
  },

  /**
   * 取消管理员
   */
  async removeAdmin(userId: string): Promise<{
    success: boolean
    old_role: string
    new_role: string
  }> {
    const response = await apiClient.post(`/api/v1/admin/users/${userId}/remove-admin`)
    return response.data
  },

  /**
   * 获取平台统计数据
   */
  async getAdminStatistics(): Promise<AdminStatistics> {
    const response = await apiClient.get('/api/v1/admin/statistics')
    return response.data
  },

  /**
   * 获取所有系统配置
   */
  async getSystemConfigs(): Promise<SystemConfigItem[]> {
    const response = await apiClient.get('/api/v1/admin/system-config/list')
    return response.data
  },

  /**
   * 获取单个系统配置
   */
  async getSystemConfig(configKey: string): Promise<SystemConfigItem> {
    const response = await apiClient.get(`/api/v1/admin/system-config/get/${configKey}`)
    return response.data
  },

  /**
   * 更新单个系统配置
   */
  async updateSystemConfig(data: {
    config_key: string
    config_value: string
    description?: string
  }): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/api/v1/admin/system-config/update', data)
    return response.data
  },

  /**
   * 批量更新系统配置
   */
  async batchUpdateSystemConfigs(configs: Record<string, string>): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/api/v1/admin/system-config/batch-update', { configs })
    return response.data
  },

  // ==================== 提现相关API ====================

  /**
   * 创建提现申请
   */
  async createWithdrawal(data: {
    amount: number
    withdrawal_method: string
    withdrawal_account: string
    withdrawal_name: string
    user_note?: string
  }): Promise<{ success: boolean; message: string; data: any }> {
    const response = await apiClient.post('/api/v1/withdrawal/create', data)
    return response.data
  },

  /**
   * 获取我的提现记录
   */
  async getMyWithdrawals(params?: {
    limit?: number
    offset?: number
  }): Promise<WithdrawalRecord[]> {
    const response = await apiClient.get('/api/v1/withdrawal/my-withdrawals', { params })
    return response.data
  },

  /**
   * 获取我的提现记录总数
   */
  async getMyWithdrawalsCount(): Promise<{ count: number }> {
    const response = await apiClient.get('/api/v1/withdrawal/my-withdrawals/count')
    return response.data
  },

  /**
   * 取消提现申请
   */
  async cancelWithdrawal(withdrawalId: string): Promise<{ success: boolean; message: string; data: any }> {
    const response = await apiClient.post(`/api/v1/withdrawal/cancel/${withdrawalId}`)
    return response.data
  },

  /**
   * 获取提现列表（管理员）
   */
  async getWithdrawalsList(params?: {
    status?: string
    limit?: number
    offset?: number
  }): Promise<AdminWithdrawalRecord[]> {
    const response = await apiClient.get('/api/v1/admin/withdrawals', { params })
    return response.data
  },

  /**
   * 获取提现记录总数（管理员）
   */
  async getWithdrawalsCount(params?: {
    status?: string
  }): Promise<{ count: number }> {
    const response = await apiClient.get('/api/v1/admin/withdrawals/count', { params })
    return response.data
  },

  /**
   * 审核通过提现（管理员）
   */
  async approveWithdrawal(withdrawalId: string, data: {
    note?: string
  }): Promise<{ success: boolean; message: string; data: any }> {
    const response = await apiClient.post(`/api/v1/admin/withdrawals/${withdrawalId}/approve`, data)
    return response.data
  },

  /**
   * 审核拒绝提现（管理员）
   */
  async rejectWithdrawal(withdrawalId: string, data: {
    reason: string
  }): Promise<{ success: boolean; message: string; data: any }> {
    const response = await apiClient.post(`/api/v1/admin/withdrawals/${withdrawalId}/reject`, data)
    return response.data
  },

  /**
   * 标记已打款（管理员）
   */
  async markWithdrawalPaid(withdrawalId: string, data: {
    payment_proof?: string
  }): Promise<{ success: boolean; message: string; data: any }> {
    const response = await apiClient.post(`/api/v1/admin/withdrawals/${withdrawalId}/mark-paid`, data)
    return response.data
  },

  /**
   * 导出待打款订单Excel（管理员）
   */
  async exportWithdrawals(params?: {
    start_date?: string
    end_date?: string
  }): Promise<Blob> {
    const response = await apiClient.get('/api/v1/admin/withdrawals/export', {
      params,
      responseType: 'blob'
    })
    return response.data
  },

  // ==================== 案例管理相关API ====================

  /**
   * 获取已发布案例列表（用户）
   */
  async getPublishedCases(params?: {
    category?: string
    keyword?: string
    limit?: number
    offset?: number
  }): Promise<Case[]> {
    const response = await apiClient.get('/api/v1/cases', { params })
    return response.data
  },

  /**
   * 获取已发布案例总数
   */
  async getPublishedCasesCount(params?: {
    category?: string
    keyword?: string
  }): Promise<{ count: number }> {
    const response = await apiClient.get('/api/v1/cases/count', { params })
    return response.data
  },

  /**
   * 获取所有行业分类
   */
  async getCaseCategories(): Promise<{ categories: Array<{ value: string; label: string }> }> {
    const response = await apiClient.get('/api/v1/cases/categories')
    return response.data
  },

  /**
   * 获取案例详情
   */
  async getCaseById(caseId: string): Promise<Case> {
    const response = await apiClient.get(`/api/v1/cases/${caseId}`)
    return response.data
  },

  /**
   * 使用案例模板
   */
  async useCaseTemplate(caseId: string): Promise<{ success: boolean; use_count: number }> {
    const response = await apiClient.post(`/api/v1/cases/${caseId}/use`)
    return response.data
  },

  /**
   * 创建案例（管理员）
   */
  async createCase(data: {
    title: string
    description?: string
    category: string
    tags?: string[]
    prompt: string
    negative_prompt?: string
    parameters?: Record<string, any>
    provider?: string
    model?: string
    is_published?: boolean
    sort_order?: number
  }, image?: File): Promise<Case> {
    const formData = new FormData()
    formData.append('title', data.title)
    if (data.description) formData.append('description', data.description)
    formData.append('category', data.category)
    if (data.tags && data.tags.length > 0) formData.append('tags', JSON.stringify(data.tags))
    formData.append('prompt', data.prompt)
    if (data.negative_prompt) formData.append('negative_prompt', data.negative_prompt)
    if (data.parameters) formData.append('parameters', JSON.stringify(data.parameters))
    if (data.provider) formData.append('provider', data.provider)
    if (data.model) formData.append('model', data.model)
    formData.append('is_published', String(data.is_published ?? true))
    formData.append('sort_order', String(data.sort_order ?? 0))
    if (image) formData.append('image', image)

    const response = await apiClient.post('/api/v1/admin/cases', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  /**
   * 获取案例列表（管理员）
   */
  async getAdminCases(params?: {
    category?: string
    is_published?: boolean
    keyword?: string
    limit?: number
    offset?: number
  }): Promise<Case[]> {
    const response = await apiClient.get('/api/v1/admin/cases', { params })
    return response.data
  },

  /**
   * 获取案例总数（管理员）
   */
  async getAdminCasesCount(params?: {
    category?: string
    is_published?: boolean
    keyword?: string
  }): Promise<{ count: number }> {
    const response = await apiClient.get('/api/v1/admin/cases/count', { params })
    return response.data
  },

  /**
   * 获取案例详情（管理员）
   */
  async getAdminCaseById(caseId: string): Promise<Case> {
    const response = await apiClient.get(`/api/v1/admin/cases/${caseId}`)
    return response.data
  },

  /**
   * 更新案例
   */
  async updateCase(caseId: string, data: {
    title?: string
    description?: string
    category?: string
    tags?: string[]
    prompt?: string
    negative_prompt?: string
    parameters?: Record<string, any>
    provider?: string
    model?: string
    is_published?: boolean
    sort_order?: number
  }): Promise<Case> {
    const response = await apiClient.put(`/api/v1/admin/cases/${caseId}`, data)
    return response.data
  },

  /**
   * 更新案例图片
   */
  async updateCaseImage(caseId: string, image: File): Promise<Case> {
    const formData = new FormData()
    formData.append('image', image)

    const response = await apiClient.post(`/api/v1/admin/cases/${caseId}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  /**
   * 切换案例发布状态
   */
  async toggleCasePublishStatus(caseId: string): Promise<Case> {
    const response = await apiClient.post(`/api/v1/admin/cases/${caseId}/toggle`)
    return response.data
  },

  /**
   * 删除案例
   */
  async deleteCase(caseId: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(`/api/v1/admin/cases/${caseId}`)
    return response.data
  },

  // ==================== 通知系统相关API ====================

  /**
   * 获取我的通知列表
   */
  async getMyNotifications(page: number = 1, pageSize: number = 20): Promise<{
    items: Array<{
      id: string
      title: string
      content: string
      priority: string
      announcement_type: string
      is_pinned: boolean
      cover_image_url: string | null
      published_at: string | null
      is_read: boolean
      read_at: string | null
      is_clicked: boolean
      clicked_at: string | null
    }>
    total: number
    page: number
    page_size: number
    total_pages: number
  }> {
    const response = await apiClient.get('/api/v1/notifications/my', {
      params: { page, page_size: pageSize }
    })
    return response.data
  },

  /**
   * 获取未读通知数量
   */
  async getUnreadCount(): Promise<{ count: number }> {
    const response = await apiClient.get('/api/v1/notifications/my/unread-count')
    return response.data
  },

  /**
   * 标记通知为已读
   */
  async markNotificationAsRead(announcementId: string): Promise<void> {
    await apiClient.post(`/api/v1/notifications/my/${announcementId}/read`)
  },

  /**
   * 标记所有通知为已读
   */
  async markAllNotificationsAsRead(): Promise<void> {
    await apiClient.post('/api/v1/notifications/my/read-all')
  },

  /**
   * 标记通知为已点击
   */
  async markNotificationAsClicked(announcementId: string): Promise<void> {
    await apiClient.post(`/api/v1/notifications/my/${announcementId}/click`)
  },

  /**
   * 忽略/删除通知
   */
  async dismissNotification(announcementId: string): Promise<void> {
    await apiClient.delete(`/api/v1/notifications/my/${announcementId}`)
  },

  /**
   * 获取公开公告列表（首页轮播）
   */
  async getPublicAnnouncements(page: number = 1, pageSize: number = 10): Promise<{
    items: Array<{
      id: string
      title: string
      content: string
      priority: string
      announcement_type: string
      is_pinned: boolean
      cover_image_url: string | null
      published_at: string | null
    }>
    total: number
    page: number
    page_size: number
    total_pages: number
  }> {
    const response = await apiClient.get('/api/v1/notifications/public', {
      params: { page, page_size: pageSize }
    })
    return response.data
  },

  /**
   * 获取公开公告详情
   */
  async getPublicAnnouncementById(announcementId: string): Promise<{
    id: string
    title: string
    content: string
    priority: string
    announcement_type: string
    is_pinned: boolean
    cover_image_url: string | null
    published_at: string | null
    view_count: number
    click_count: number
    created_at: string
  }> {
    const response = await apiClient.get(`/api/v1/notifications/public/${announcementId}`)
    return response.data
  },

  // ==================== 管理员-公告管理API ====================

  /**
   * 获取公告列表（管理员）
   */
  async getAdminAnnouncements(params?: {
    page?: number
    page_size?: number
    priority?: string
    announcement_type?: string
    is_published?: boolean
    target_audience?: string
  }): Promise<{
    items: Array<{
      id: string
      title: string
      content: string
      priority: string
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
      created_by: string | null
    }>
    total: number
    page: number
    page_size: number
    total_pages: number
  }> {
    const response = await apiClient.get('/api/v1/admin/announcements', { params })
    return response.data
  },

  /**
   * 创建公告
   */
  async createAnnouncement(data: {
    title: string
    content: string
    priority?: string
    announcement_type?: string
    is_pinned?: boolean
    is_published?: boolean
    target_audience?: string
    published_at?: string | null
    expires_at?: string | null
    cover_image_url?: string | null
  }): Promise<{
    id: string
    title: string
    content: string
    priority: string
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
    created_by: string | null
  }> {
    const response = await apiClient.post('/api/v1/admin/announcements', data)
    return response.data
  },

  /**
   * 获取公告详情（管理员）
   */
  async getAdminAnnouncementById(announcementId: string): Promise<{
    id: string
    title: string
    content: string
    priority: string
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
    created_by: string | null
  }> {
    const response = await apiClient.get(`/api/v1/admin/announcements/${announcementId}`)
    return response.data
  },

  /**
   * 更新公告
   */
  async updateAnnouncement(announcementId: string, data: {
    title?: string
    content?: string
    priority?: string
    announcement_type?: string
    is_pinned?: boolean
    is_published?: boolean
    target_audience?: string
    published_at?: string | null
    expires_at?: string | null
    cover_image_url?: string | null
  }): Promise<{
    id: string
    title: string
    content: string
    priority: string
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
    created_by: string | null
  }> {
    const response = await apiClient.put(`/api/v1/admin/announcements/${announcementId}`, data)
    return response.data
  },

  /**
   * 删除公告
   */
  async deleteAnnouncement(announcementId: string): Promise<void> {
    await apiClient.delete(`/api/v1/admin/announcements/${announcementId}`)
  },

  /**
   * 发布公告
   */
  async publishAnnouncement(announcementId: string): Promise<{
    id: string
    title: string
    content: string
    priority: string
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
    created_by: string | null
  }> {
    const response = await apiClient.post(`/api/v1/admin/announcements/${announcementId}/publish`)
    return response.data
  },

  /**
   * 上传公告封面图片
   */
  async uploadAnnouncementCover(announcementId: string, file: File): Promise<{
    url: string
    filename: string
  }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post(
      `/api/v1/admin/announcements/${announcementId}/upload-cover`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    )
    return response.data
  },

  // ==================== 用户配置相关API ====================

  /**
   * 获取用户API配置
   */
  async getUserConfig(): Promise<{
    api_key_hint: string | null
    default_model: string | null
    has_api_key: boolean
  }> {
    const response = await apiClient.get('/api/v1/user/config')
    return response.data
  },

  /**
   * 保存用户API配置
   */
  async saveUserConfig(data: {
    api_key: string
    default_model?: string
  }): Promise<{
    success: boolean
    message: string
    api_key_hint: string
  }> {
    const response = await apiClient.post('/api/v1/user/config', data)
    return response.data
  },

  /**
   * 删除用户API配置
   */
  async deleteUserConfig(): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete('/api/v1/user/config')
    return response.data
  },
}

// ==================== 类型定义 ====================

export interface User {
  id: string
  username: string
  phone?: string
  email?: string
  role?: string
  status: string
  created_at?: string
}

export interface AccountInfo {
  user_id: string
  balance: number
  balance_yuan: number
  points: number  // 永久积分
  gift_points: number  // 临时积分（签到赠送）
  gift_points_expiry: string | null  // 临时积分过期时间
  total_points: number  // 总可用积分 = points + gift_points
  subscription_plan?: string
  subscription_expires_at?: string
  total_generated: number
  total_spent: number
  total_points_earned: number  // 历史累计获得积分
}

export interface Transaction {
  id: string
  transaction_type: string
  amount: number
  points_change: number
  balance_after: number
  points_after: number
  description: string
  status: string
  created_at: string
}

export interface ConsumptionRecord {
  id: string
  model_name: string
  provider: string
  cost_type: string  // 'free' | 'subscription' | 'points' | 'balance'
  points_used: number
  amount: number  // 分
  prompt?: string
  image_count: number
  image_urls?: string[]
  status: 'success' | 'failed'  // 新增
  error_reason?: string  // 新增：失败原因
  created_at: string
}

export interface ModelPrice {
  model_name: string
  display_name: string
  points: number
  amount: number
  amount_yuan: number
  description: string
}

export interface RechargeOption {
  id: string
  name: string
  amount: number
  amount_yuan: number
  points: number
  bonus: number
  popular: boolean
}

export interface BillingConfig {
  billing: {
    mode: string
    currency: string
    currency_symbol: string
  }
  initial_quota: {
    free_generations: number
  }
  limits: {
    guest: {
      daily_limit: number
    }
    order_expire_minutes: number
  }
}

export interface SystemConfigItem {
  config_key: string
  config_value: string
  config_type: string
  category: string
  description?: string
  updated_at?: string
}

export interface Order {
  order_id: string
  order_type: string
  amount: number
  amount_yuan: number
  payment_method: string
  status: string
  subject: string
  created_at: string
  paid_at?: string
}

// ==================== 提现类型定义 ====================

export interface WithdrawalRecord {
  id: string
  withdrawal_id: string
  amount: number
  amount_yuan: number
  withdrawal_method: string
  withdrawal_account: string
  withdrawal_name: string
  status: string
  user_note?: string
  review_note?: string
  created_at?: string
  reviewed_at?: string
  completed_at?: string
}

export interface AdminWithdrawalRecord extends WithdrawalRecord {
  user_id: string
  username: string
  phone: string
  admin_id?: string
  payment_proof?: string
}

// ==================== 案例类型定义 ====================

export interface Case {
  id: string
  title: string
  description?: string
  category: string
  tags?: string[]
  thumbnail_url?: string
  image_url?: string
  prompt: string
  negative_prompt?: string
  parameters?: Record<string, any>
  provider?: string
  model?: string
  is_published: boolean
  sort_order: number
  view_count: number
  use_count: number
  created_by?: string
  created_at: string
  updated_at: string
}

// ==================== 生成历史类型定义 ====================

export interface GenerationRecord {
  id: string
  user_request_id: string
  provider: string
  model: string
  prompt: string
  negative_prompt: string
  width: number
  height: number
  n: number
  style?: string
  quality?: string
  status: 'completed' | 'failed' | 'pending' | 'processing'
  image_urls: string[]
  image_paths: string[]
  processing_time?: number
  start_time?: string
  end_time?: string
  created_at: string
  extra_params?: Record<string, any>
}

export interface UnifiedGenerationRecord {
  id: string
  type: 'chat' | 'async'
  model: string
  prompt: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  image_urls: string[]
  timestamp: string
  created_at: string
  provider?: string
  platform?: string
  processing_time?: number
  error?: string
}

// ==================== 管理员类型定义 ====================

export interface AdminUserListItem {
  id: string
  phone: string
  username: string
  status: string
  role: string
  created_at: string
  last_login_at: string
  points: number
  balance: number
  gift_points: number
  total_generated: number
  total_spent: number
  invite_count: number
}

export interface AdminUserDetail {
  id: string
  phone: string
  username: string
  status: string
  role: string
  created_at: string
  last_login_at: string
  last_login_ip: string
  phone_verified: boolean
  points: number
  balance: number
  gift_points: number
  total_generated: number
  total_spent: number
  invite_code: string
  invite_count: number
  inviter_id: string
  last_checkin_date: string
  consecutive_checkin_days: number
}

export interface AdminStatistics {
  total_users: number
  active_users: number
  total_generated: number
  total_revenue: number
  today_users: number
  today_generated: number
  today_revenue: number
}

// 导出axios实例以供高级用法
export default apiClient
