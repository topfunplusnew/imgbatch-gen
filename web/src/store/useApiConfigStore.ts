import { defineStore } from 'pinia'

const API_CONFIG_STORAGE_KEY = 'apiConfig'

type StoredApiConfig = {
  apiKey?: string
  defaultModel?: string
  apiEndpoint?: string
}

export const useApiConfigStore = defineStore('apiConfig', {
  state: () => ({
    apiKey: '',
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
    loadConfigFromStorage() {
      if (typeof window === 'undefined') return

      const raw = localStorage.getItem(API_CONFIG_STORAGE_KEY)
      if (!raw) return

      try {
        const saved = JSON.parse(raw) as StoredApiConfig
        if (typeof saved.apiKey === 'string') {
          this.apiKey = saved.apiKey
        }
        if (typeof saved.defaultModel === 'string' && saved.defaultModel.trim()) {
          this.defaultModel = saved.defaultModel
        }
        if (typeof saved.apiEndpoint === 'string') {
          this.apiEndpoint = saved.apiEndpoint
        }
      } catch (error) {
        console.error('Failed to load API config from localStorage:', error)
      }
    },
    async testConnection(): Promise<boolean> {
      try {
        const { api } = await import('@/services/api')
        const response = await api.healthCheck()
        return response?.status === 'healthy'
      } catch (error) {
        console.error('Connection test failed:', error)
        return false
      }
    },
    resetConfig() {
      this.apiKey = ''
      this.apiEndpoint = ''
      this.defaultModel = 'Stable Diffusion XL v1.0'
    },
    configureFromEnv() {
      const endpoint = import.meta.env.VITE_API_BASE_URL

      if (endpoint && endpoint !== this.apiEndpoint) {
        this.setApiEndpoint(endpoint)
        console.log('API endpoint configured from environment:', endpoint)
      }

      return { endpoint: this.apiEndpoint, hasKey: !!this.apiKey }
    },
    async initializeConfig() {
      if (this.isInitialized) return

      try {
        this.loadConfigFromStorage()

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
