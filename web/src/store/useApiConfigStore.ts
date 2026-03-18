import { defineStore } from 'pinia'

export const useApiConfigStore = defineStore('apiConfig', {
  state: () => ({
    apiKey: '',
    // 开发环境走vite代理（空字符串），生产环境使用环境变量
    apiEndpoint: import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || ''),
    defaultModel: 'Stable Diffusion XL v1.0',
    isInitialized: false,
  }),
  actions: {
    setApiKey(apiKey: string) {
      this.apiKey = apiKey
    },
    setApiEndpoint(endpoint: string) {
      this.apiEndpoint = endpoint
    },
    setDefaultModel(model: string) {
      this.defaultModel = model
    },
    async testConnection(): Promise<boolean> {
      // API 端点已固定，直接测试
      try {
        // 动态导入API模块以避免循环依赖
        const { api } = await import('@/services/api')
        const response = await api.healthCheck()
        return response?.status === 'healthy'
      } catch (error) {
        console.error('连接测试失败:', error)
        return false
      }
    },
    resetConfig() {
      this.apiKey = ''
      this.apiEndpoint = ''
      this.defaultModel = 'Stable Diffusion XL v1.0'
    },

    /**
     * 从环境变量配置API
     */
    configureFromEnv() {
      const endpoint = import.meta.env.VITE_API_BASE_URL

      if (endpoint && endpoint !== this.apiEndpoint) {
        this.setApiEndpoint(endpoint)
        console.log('API endpoint configured from environment:', endpoint)
      }

      return { endpoint: this.apiEndpoint, hasKey: !!this.apiKey }
    },

    /**
     * 初始化API配置
     */
    async initializeConfig() {
      if (this.isInitialized) return

      try {
        if (!import.meta.env.VITE_API_BASE_URL) {
          console.warn('VITE_API_BASE_URL environment variable not found')
        }

        if (this.apiEndpoint) {
          const isConnected = await this.testConnection()
          if (isConnected) {
            console.log('API connection successful')
          } else {
            console.error('API connection failed')
          }
        }

        this.isInitialized = true
      } catch (error) {
        console.error('Failed to initialize API config:', error)
      }
    },
  },
})

