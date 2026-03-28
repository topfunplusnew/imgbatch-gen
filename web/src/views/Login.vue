<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-primary-soft/30 via-white to-primary-soft/20">
    <div class="w-full max-w-md">
      <!-- Logo和标题 -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-[70%] h-auto mb-4">
          <img src="/photo/logo.png" alt="Logo" class="w-full h-auto object-contain rounded-xl" />
        </div>
        <p class="text-ink-500 mt-2">{{ isLoginMode ? '欢迎回来' : '创建新账户' }}</p>
      </div>

      <div
        v-if="appStore.authRedirectNotice"
        class="mb-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-left shadow-sm"
      >
        <div class="flex items-start gap-3">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600">
            <span class="material-symbols-outlined !text-lg">lock</span>
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-sm font-semibold text-amber-900">{{ appStore.authRedirectNotice.title }}</p>
                <p class="mt-1 text-sm leading-6 text-amber-800">{{ appStore.authRedirectNotice.message }}</p>
              </div>
              <button
                type="button"
                class="rounded-lg p-1 text-amber-500 transition-colors hover:bg-amber-100 hover:text-amber-700"
                @click="appStore.clearAuthRedirectNotice()"
              >
                <span class="material-symbols-outlined !text-base">close</span>
              </button>
            </div>
            <p class="mt-2 text-xs text-amber-700/90">登录后可继续进行图片生成、历史记录查看和账户相关操作。</p>
          </div>
        </div>
      </div>

      <!-- 登录/注册表单 -->
      <div class="bg-white rounded-2xl shadow-xl overflow-hidden">
        <div class="p-6">
          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-ink-700 mb-1">用户名</label>
              <input
                v-model="form.username"
                type="text"
                required
                minlength="2"
                maxlength="20"
                placeholder="2-20位字符"
                class="w-full px-4 py-3 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-ink-700 mb-1">密码</label>
              <input
                v-model="form.password"
                type="password"
                required
                minlength="6"
                placeholder="至少6位字符"
                class="w-full px-4 py-3 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
              />
            </div>

            <!-- 忘记密码链接（仅登录模式显示） -->
            <div v-if="isLoginMode" class="text-right">
              <button
                type="button"
                @click="showForgotPassword = true"
                class="text-sm text-primary hover:text-primary-strong transition-colors"
              >
                忘记密码？
              </button>
            </div>

            <div v-if="!isLoginMode">
              <label class="block text-sm font-medium text-ink-700 mb-1">确认密码</label>
              <input
                v-model="form.passwordConfirmation"
                type="password"
                required
                minlength="6"
                placeholder="再次输入密码"
                class="w-full px-4 py-3 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
              />
            </div>

            <div v-if="!isLoginMode">
              <label class="block text-sm font-medium text-ink-700 mb-1">邀请码（可选）</label>
              <input
                v-model="form.inviteCode"
                type="text"
                placeholder="填写邀请码，邀请人可获得奖励"
                maxlength="20"
                class="w-full px-4 py-3 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
              />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary-strong disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {{ loading ? '处理中...' : (isLoginMode ? '登录' : '注册并登录') }}
            </button>
          </form>

          <!-- 提示信息 -->
          <div v-if="!isLoginMode" class="mt-4 p-3 bg-blue-50 rounded-xl">
            <p class="text-sm text-blue-700 flex items-start gap-2">
              <svg class="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
              </svg>
              <span>注册即送100积分，每日签到额外获得40积分</span>
            </p>
          </div>

          <!-- 切换登录/注册 -->
          <div class="mt-4 pt-4 border-t border-border-dark">
            <button
              @click="toggleMode"
              :disabled="loading"
              class="w-full py-2.5 text-sm text-primary hover:text-primary-strong transition-colors font-medium"
            >
              {{ isLoginMode ? '没有账户？立即注册' : '已有账户？返回登录' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 忘记密码弹窗 -->
      <transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="showForgotPassword"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <!-- 背景遮罩 -->
          <div
            @click="showForgotPassword = false"
            class="absolute inset-0 bg-black/50 backdrop-blur-sm"
          ></div>

          <!-- 弹窗内容 -->
          <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            <!-- 头部 -->
            <div class="sticky top-0 bg-white border-b border-border-dark px-6 py-4 flex items-center justify-between rounded-t-2xl">
              <h2 class="text-xl font-bold text-ink-950">重置密码</h2>
              <button
                @click="showForgotPassword = false"
                class="p-1 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <span class="material-symbols-outlined !text-2xl text-ink-500">close</span>
              </button>
            </div>

            <!-- 内容 -->
            <div class="p-6">
              <!-- 步骤1: 输入邮箱 -->
              <div v-if="resetStep === 1" class="space-y-4">
                <p class="text-sm text-ink-600 mb-4">请输入您的注册邮箱，我们将发送验证码到您的邮箱</p>

                <div>
                  <label class="block text-sm font-medium text-ink-700 mb-1.5">邮箱地址</label>
                  <input
                    v-model="resetForm.email"
                    type="email"
                    placeholder="请输入邮箱地址"
                    class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                  />
                </div>

                <button
                  @click="sendResetCode"
                  :disabled="!resetForm.email || resetSending"
                  class="w-full py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary-strong disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
                >
                  {{ resetSending ? '发送中...' : '发送验证码' }}
                </button>
              </div>

              <!-- 步骤2: 输入验证码和新密码 -->
              <div v-else-if="resetStep === 2" class="space-y-4">
                <p class="text-sm text-ink-600 mb-4">请输入收到的验证码和新密码</p>

                <div>
                  <label class="block text-sm font-medium text-ink-700 mb-1.5">验证码</label>
                  <div class="flex gap-2">
                    <input
                      v-model="resetForm.code"
                      type="text"
                      placeholder="请输入6位验证码"
                      maxlength="6"
                      class="flex-1 px-4 py-2.5 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                    />
                    <button
                      v-if="resetCountdown > 0"
                      type="button"
                      disabled
                      class="px-4 py-2.5 bg-gray-100 text-gray-500 rounded-xl text-sm font-medium"
                    >
                      {{ resetCountdown }}s
                    </button>
                    <button
                      v-else
                      type="button"
                      @click="sendResetCode"
                      :disabled="resetSending"
                      class="px-4 py-2.5 bg-primary-soft text-primary rounded-xl hover:bg-primary/20 disabled:opacity-50 text-sm font-medium"
                    >
                      重新发送
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-ink-700 mb-1.5">新密码</label>
                  <input
                    v-model="resetForm.newPassword"
                    type="password"
                    placeholder="至少6位字符"
                    minlength="6"
                    class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-ink-700 mb-1.5">确认新密码</label>
                  <input
                    v-model="resetForm.confirmPassword"
                    type="password"
                    placeholder="再次输入新密码"
                    minlength="6"
                    class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                  />
                </div>

                <button
                  @click="resetPassword"
                  :disabled="!resetForm.code || !resetForm.newPassword || resetLoading"
                  class="w-full py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary-strong disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
                >
                  {{ resetLoading ? '重置中...' : '重置密码' }}
                </button>

                <button
                  type="button"
                  @click="resetStep = 1"
                  class="w-full py-2.5 text-sm text-ink-500 hover:text-ink-700 transition-colors"
                >
                  返回上一步
                </button>
              </div>

              <!-- 步骤3: 成功 -->
              <div v-else-if="resetStep === 3" class="text-center py-8">
                <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
                  <span class="material-symbols-outlined !text-4xl text-green-600">check</span>
                </div>
                <h3 class="text-xl font-bold text-ink-950 mb-2">密码重置成功！</h3>
                <p class="text-ink-600 mb-6">请使用新密码登录</p>
                <button
                  @click="closeForgotPassword"
                  class="w-full py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary-strong transition-all shadow-lg"
                >
                  返回登录
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- 返回首页 -->
      <div class="mt-6 text-center">
        <button
          @click="backToHome"
          class="text-sm text-ink-500 hover:text-ink-700 flex items-center justify-center gap-1 mx-auto transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回首页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/store/useAuthStore'
import { useAppStore } from '@/store/useAppStore'
import { api } from '@/services/api'
import { notification } from '@/utils/notification'

const authStore = useAuthStore()
const appStore = useAppStore()

// 状态
const isLoginMode = ref(true) // 默认登录模式
const loading = ref(false)

// 忘记密码弹窗状态
const showForgotPassword = ref(false)
const resetStep = ref(1) // 1: 输入邮箱, 2: 输入验证码和新密码, 3: 成功
const resetSending = ref(false)
const resetLoading = ref(false)
const resetCountdown = ref(0)

// 忘记密码表单
const resetForm = ref({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

// 表单
const form = ref({
  username: '',
  password: '',
  passwordConfirmation: '',
  inviteCode: ''
})

// 切换登录/注册模式
function toggleMode() {
  isLoginMode.value = !isLoginMode.value
  // 重置表单
  form.value = { username: '', password: '', passwordConfirmation: '', inviteCode: '' }
}

// 返回首页
function backToHome() {
  appStore.setCurrentPage('agent')
}

// 处理表单提交
async function handleSubmit() {
  loading.value = true
  try {
    if (isLoginMode.value) {
      // 登录
      await authStore.loginByUsername(form.value.username, form.value.password)
    } else {
      // 注册
      if (form.value.password !== form.value.passwordConfirmation) {
        notification.error('注册失败', '两次输入的密码不一致')
        return
      }
      await authStore.registerByUsername({
        username: form.value.username,
        password: form.value.password,
        password_confirmation: form.value.passwordConfirmation,
        invite_code: form.value.inviteCode || undefined
      })
    }

    // 成功后跳转
    appStore.setCurrentPage('agent')
  } catch (error) {
    notification.error('操作失败', error?.response?.data?.detail || '请重试')
  } finally {
    loading.value = false
  }
}

// 发送重置验证码
async function sendResetCode() {
  if (!resetForm.value.email) {
    notification.error('错误', '请输入邮箱地址')
    return
  }

  resetSending.value = true
  try {
    await api.sendVerifyCode(resetForm.value.email, 'email')
    notification.success('发送成功', '验证码已发送到您的邮箱')

    // 开始倒计时
    resetCountdown.value = 60
    const timer = setInterval(() => {
      resetCountdown.value--
      if (resetCountdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)

    // 进入下一步
    resetStep.value = 2
  } catch (error) {
    notification.error('发送失败', error?.response?.data?.detail || '请稍后重试')
  } finally {
    resetSending.value = false
  }
}

// 重置密码
async function resetPassword() {
  if (!resetForm.value.code || !resetForm.value.newPassword) {
    notification.error('错误', '请填写完整信息')
    return
  }

  if (resetForm.value.newPassword.length < 6) {
    notification.error('错误', '密码至少需要6位字符')
    return
  }

  if (resetForm.value.newPassword !== resetForm.value.confirmPassword) {
    notification.error('错误', '两次输入的密码不一致')
    return
  }

  resetLoading.value = true
  try {
    await api.resetPassword(
      resetForm.value.email,
      resetForm.value.code,
      resetForm.value.newPassword,
      'email'
    )
    notification.success('重置成功', '密码已成功重置')

    // 进入成功步骤
    resetStep.value = 3
  } catch (error) {
    notification.error('重置失败', error?.response?.data?.detail || '请稍后重试')
  } finally {
    resetLoading.value = false
  }
}

// 关闭忘记密码弹窗
function closeForgotPassword() {
  showForgotPassword.value = false
  // 重置状态
  resetStep.value = 1
  resetForm.value = {
    email: '',
    code: '',
    newPassword: '',
    confirmPassword: ''
  }
  resetCountdown.value = 0
}
</script>
