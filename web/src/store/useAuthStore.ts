/**
 * 认证状态管理 Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, type User, type AccountInfo, type ConsumptionRecord } from '@/services/api'

const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user_info'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_TOKEN_KEY))
  const user = ref<User | null>(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))
  const accountInfo = ref<AccountInfo | null>(null)
  const loading = ref(false)

  // 消费记录
  const consumptionRecords = ref<ConsumptionRecord[]>([])
  const consumptionLoading = ref(false)
  const consumptionError = ref<string | null>(null)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userId = computed(() => user.value?.id || null)
  const userName = computed(() => user.value?.username || '')
  const userUsername = computed(() => user.value?.username || '')
  const userRole = computed(() => user.value?.role || 'user')
  const userStatus = computed(() => user.value?.status || 'active')
  const userPhone = computed(() => user.value?.phone || null)
  const userEmail = computed(() => user.value?.email || null)
  const userCreatedAt = computed(() => user.value?.created_at || null)
  const createdAt = computed(() => user.value?.created_at || null)

  // 设置token
  function setTokens(access: string, refresh: string) {
    token.value = access
    refreshToken.value = refresh
    localStorage.setItem(TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  }

  // 设置用户信息
  function setUser(userInfo: User) {
    user.value = userInfo
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
  }

  // 清除认证信息
  function clearAuth() {
    token.value = null
    refreshToken.value = null
    user.value = null
    accountInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  // 用户名注册
  async function registerByUsername(data: {
    username: string
    password: string
    password_confirmation: string
    invite_code?: string
  }) {
    loading.value = true
    try {
      const result = await api.registerByUsername(data)
      setTokens(result.access_token, result.refresh_token)
      setUser(result.user)
      return result
    } catch (error: any) {
      console.error('用户名注册失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 用户名登录
  async function loginByUsername(username: string, password: string) {
    loading.value = true
    try {
      const result = await api.loginByUsername(username, password)
      setTokens(result.access_token, result.refresh_token)
      setUser(result.user)
      return result
    } catch (error: any) {
      console.error('用户名登录失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 刷新token
  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('没有刷新令牌')
    }
    try {
      const result = await api.refreshToken(refreshToken.value)
      token.value = result.access_token
      localStorage.setItem(TOKEN_KEY, result.access_token)
      return result
    } catch (error: any) {
      console.error('刷新令牌失败:', error)
      clearAuth()
      throw error
    }
  }

  // 获取当前用户信息
  async function fetchCurrentUser() {
    if (!isAuthenticated.value) return null

    try {
      const userInfo = await api.getCurrentUser()
      setUser(userInfo)
      return userInfo
    } catch (error: any) {
      console.error('获取用户信息失败:', error)
      if (error.response?.status === 401) {
        clearAuth()
      }
      throw error
    }
  }

  // 获取账户信息
  async function fetchAccountInfo() {
    if (!isAuthenticated.value) {
      accountInfo.value = null
      return
    }

    try {
      const info = await api.getAccountInfo()
      accountInfo.value = info
      return info
    } catch (error: any) {
      console.error('获取账户信息失败:', error)
      throw error
    }
  }

  // 每日签到
  async function dailyCheckin() {
    try {
      const result = await api.dailyCheckin()
      // 签到成功后刷新账户信息
      await fetchAccountInfo()
      return result
    } catch (error: any) {
      console.error('签到失败:', error)
      throw error
    }
  }

  // 获取签到状态
  async function getCheckinStatus() {
    try {
      return await api.getCheckinStatus()
    } catch (error: any) {
      console.error('获取签到状态失败:', error)
      throw error
    }
  }

  // 获取邀请码
  async function getMyInviteCode() {
    try {
      return await api.getMyInviteCode()
    } catch (error: any) {
      console.error('获取邀请码失败:', error)
      throw error
    }
  }

  // 使用邀请码
  async function applyInviteCode(inviteCode: string) {
    try {
      const result = await api.applyInviteCode(inviteCode)
      // 使用邀请码成功后刷新账户信息
      await fetchAccountInfo()
      return result
    } catch (error: any) {
      console.error('使用邀请码失败:', error)
      throw error
    }
  }

  // 获取邀请记录
  async function getInviteRecords() {
    try {
      return await api.getInviteRecords()
    } catch (error: any) {
      console.error('获取邀请记录失败:', error)
      throw error
    }
  }

  // 获取消费记录
  async function fetchConsumptionRecords(limit: number = 50, offset: number = 0) {
    consumptionLoading.value = true
    consumptionError.value = null
    try {
      const records = await api.getConsumptionRecords(limit, offset)
      // 如果是分页加载（offset > 0），追加数据；否则替换
      if (offset > 0) {
        consumptionRecords.value = [...consumptionRecords.value, ...records]
      } else {
        consumptionRecords.value = records
      }
      return records
    } catch (error: any) {
      consumptionError.value = error?.message || '获取消费记录失败'
      console.error('获取消费记录失败:', error)
      throw error
    } finally {
      consumptionLoading.value = false
    }
  }

  // 记录下载
  async function recordDownload(data: {
    image_url: string
    file_name: string
    file_size?: number
    request_id?: string
    consumption_record_id?: string
  }) {
    try {
      return await api.recordDownload(data)
    } catch (error: any) {
      console.error('记录下载失败:', error)
      throw error
    }
  }

  // 登出
  async function logout() {
    try {
      await api.logout()
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      clearAuth()
    }
  }

  // 初始化（从localStorage恢复状态）
  function init() {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    const savedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    const savedUser = localStorage.getItem(USER_KEY)

    if (savedToken && savedRefreshToken) {
      token.value = savedToken
      refreshToken.value = savedRefreshToken

      if (savedUser) {
        try {
          user.value = JSON.parse(savedUser)
        } catch {
          user.value = null
        }
      }
    }
  }

  return {
    // 状态
    token,
    user,
    accountInfo,
    loading,
    consumptionRecords,
    consumptionLoading,
    consumptionError,

    // 计算属性
    isAuthenticated,
    userId,
    userName,
    userUsername,
    userRole,
    userStatus,
    userPhone,
    userEmail,
    userCreatedAt,
    createdAt,

    // 方法
    setTokens,
    setUser,
    clearAuth,
    registerByUsername,
    loginByUsername,
    refreshAccessToken,
    fetchCurrentUser,
    fetchAccountInfo,
    dailyCheckin,
    getCheckinStatus,
    getMyInviteCode,
    applyInviteCode,
    getInviteRecords,
    fetchConsumptionRecords,
    recordDownload,
    logout,
    init,
  }
})
