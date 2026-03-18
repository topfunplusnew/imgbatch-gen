/**
 * API服务模块
 * 封装所有与后端API的交互
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { useApiConfigStore } from '@/store/useApiConfigStore'

// API响应类型定义
export interface ImageTask {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  params?: any
  result?: any
  error?: string
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

      // 设置API密钥（如果存在）
      if (apiConfig.apiKey) {
        config.headers.Authorization = `Bearer ${apiConfig.apiKey}`
      }

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
        return '禁止访问'
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
  async getBatchTaskStatus(batchId: string): Promise<any> {
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
        ...(apiConfig.apiKey ? { Authorization: `Bearer ${apiConfig.apiKey}` } : {}),
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
}

// 导出axios实例以供高级用法
export default apiClient
