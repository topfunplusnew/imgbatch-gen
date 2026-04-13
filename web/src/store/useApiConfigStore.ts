import { defineStore } from 'pinia'
import { DEFAULT_IMAGE_MODEL } from '@/utils/modelSelection'

const API_CONFIG_STORAGE_KEY = 'apiConfig'
const DEFAULT_MODEL = DEFAULT_IMAGE_MODEL
const ENV_API_ENDPOINT = String(import.meta.env.VITE_API_BASE_URL || '').trim()
const FORCE_SAME_ORIGIN_API = !import.meta.env.DEV && !ENV_API_ENDPOINT

type StoredApiConfig = {
  apiKey?: string
  defaultModel?: string
  apiEndpoint?: string
}

export const useApiConfigStore = defineStore('apiConfig', {
  state: () => ({
    apiKey: '',
    apiEndpoint: import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || ''),
    defaultModel: DEFAULT_MODEL,
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
          if (FORCE_SAME_ORIGIN_API) {
            const sanitized = { ...saved }
            delete sanitized.apiEndpoint
            if (Object.keys(sanitized).length > 0) {
              localStorage.setItem(API_CONFIG_STORAGE_KEY, JSON.stringify(sanitized))
            } else {
              localStorage.removeItem(API_CONFIG_STORAGE_KEY)
            }
          } else {
            this.apiEndpoint = saved.apiEndpoint
          }
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
      this.defaultModel = DEFAULT_MODEL
    },
    configureFromEnv() {
      const endpoint = ENV_API_ENDPOINT

      if (endpoint && endpoint !== this.apiEndpoint) {
        this.setApiEndpoint(endpoint)
        console.log('API endpoint configured from environment:', endpoint)
      }

      if (!endpoint && FORCE_SAME_ORIGIN_API && this.apiEndpoint) {
        this.setApiEndpoint('')
        console.info('Using same-origin API routing in production.')
      }

      return { endpoint: this.apiEndpoint, hasKey: !!this.apiKey }
    },
    async initializeConfig() {
      if (this.isInitialized) return

      try {
        this.loadConfigFromStorage()
        this.configureFromEnv()

        if (import.meta.env.DEV && !ENV_API_ENDPOINT) {
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
