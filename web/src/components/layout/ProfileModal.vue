<template>
  <!-- 个人资料弹窗 -->
  <transition
    enter-active-class="transition ease-out duration-200"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition ease-in duration-150"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="appStore.showProfileModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-3 xs:p-4"
    >
      <!-- 背景遮罩 -->
      <div
        @click="appStore.showProfileModal = false"
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
      ></div>

      <!-- 弹窗内容 -->
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-[95vw] sm:max-w-md max-h-[90vh] overflow-y-auto">
        <!-- 头部 -->
        <div class="sticky top-0 bg-white border-b border-border-dark px-4 xs:px-6 py-3 xs:py-4 flex items-center justify-between rounded-t-2xl">
          <h2 class="text-lg xs:text-xl font-bold text-ink-950">个人资料</h2>
          <button
            @click="appStore.showProfileModal = false"
            class="p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <span class="material-symbols-outlined !text-xl xs:!text-2xl text-ink-500">close</span>
          </button>
        </div>

        <!-- 内容 -->
        <div class="p-4 xs:p-5 sm:p-6 space-y-4 xs:space-y-5 sm:space-y-6">
          <!-- 头像区域 -->
          <div class="flex items-center gap-3 xs:gap-4">
            <div class="w-16 xs:w-20 h-16 xs:h-20 rounded-full bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center text-white text-xl xs:text-2xl font-bold shadow-lg">
              {{ userInitial }}
            </div>
            <div>
              <p class="text-base xs:text-lg font-semibold text-ink-950">{{ displayName }}</p>
              <p class="text-xs xs:text-sm text-ink-500">{{ displayEmail || '未设置邮箱' }}</p>
            </div>
          </div>

          <!-- 用户信息表单 -->
          <form @submit.prevent="handleSaveProfile" class="space-y-3 xs:space-y-4">
            <!-- 用户名 -->
            <div>
              <label class="block text-sm font-medium text-ink-700 mb-1.5">用户名</label>
              <input
                v-model="profileForm.username"
                type="text"
                placeholder="2-20位字符"
                minlength="2"
                maxlength="20"
                class="w-full px-3 xs:px-4 py-2 xs:py-2.5 text-sm xs:text-base border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
              />
            </div>

            <!-- 邮箱（只读） -->
            <div>
              <label class="block text-sm font-medium text-ink-700 mb-1.5">邮箱</label>
              <div class="relative">
                <input
                  :value="authStore.userEmail || '未绑定'"
                  type="email"
                  readonly
                  class="w-full px-3 xs:px-4 py-2 xs:py-2.5 text-sm xs:text-base border border-border-dark rounded-xl bg-gray-50 text-ink-500 cursor-not-allowed"
                />
                <span v-if="authStore.userEmail" class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-primary bg-primary-soft px-2 py-0.5 rounded-full">
                  已验证
                </span>
              </div>
            </div>

            <!-- 手机号（只读） -->
            <div>
              <label class="block text-sm font-medium text-ink-700 mb-1.5">手机号</label>
              <div class="relative">
                <input
                  :value="authStore.userPhone || '未绑定'"
                  type="tel"
                  readonly
                  class="w-full px-3 xs:px-4 py-2 xs:py-2.5 text-sm xs:text-base border border-border-dark rounded-xl bg-gray-50 text-ink-500 cursor-not-allowed"
                />
                <span v-if="authStore.userPhone" class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-primary bg-primary-soft px-2 py-0.5 rounded-full">
                  已验证
                </span>
              </div>
            </div>

            <!-- 用户ID（只读） -->
            <div>
              <label class="block text-sm font-medium text-ink-700 mb-1.5">用户ID</label>
              <input
                :value="authStore.userId?.slice(0, 8) + '...' || ''"
                type="text"
                readonly
                class="w-full px-3 xs:px-4 py-2 xs:py-2.5 text-sm xs:text-base border border-border-dark rounded-xl bg-gray-50 text-ink-500 cursor-not-allowed font-mono"
              />
            </div>

            <!-- 注册时间（只读） -->
            <div>
              <label class="block text-sm font-medium text-ink-700 mb-1.5">注册时间</label>
              <input
                :value="formatDate(authStore.createdAt)"
                type="text"
                readonly
                class="w-full px-3 xs:px-4 py-2 xs:py-2.5 text-sm xs:text-base border border-border-dark rounded-xl bg-gray-50 text-ink-500 cursor-not-allowed"
              />
            </div>

            <!-- 按钮组 -->
            <div class="flex gap-2 xs:gap-3 pt-4">
              <button
                type="button"
                @click="appStore.showProfileModal = false"
                class="flex-1 py-2.5 px-3 xs:px-4 border border-border-dark rounded-xl text-ink-700 hover:bg-gray-50 transition-colors font-medium text-sm xs:text-base"
              >
                取消
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="flex-1 py-2.5 px-3 xs:px-4 bg-gradient-to-r from-primary to-primary-deep text-white rounded-xl hover:from-primary-strong hover:to-primary-deep disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-lg text-sm xs:text-base"
              >
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/store/useAuthStore'
import { useAppStore } from '@/store/useAppStore'
import { api } from '@/services/api'

const authStore = useAuthStore()
const appStore = useAppStore()

const saving = ref(false)

// 个人资料表单
const profileForm = ref({
  username: ''
})

// 显示的用户名
const displayName = computed(() => {
  return authStore.userName || authStore.userEmail || authStore.userPhone || '用户'
})

// 显示的邮箱/手机号
const displayEmail = computed(() => {
  return authStore.userEmail || authStore.userPhone || ''
})

// 用户名首字母（头像）
const userInitial = computed(() => {
  const name = displayName.value
  return name.charAt(0).toUpperCase()
})

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return '-'
  let normalized = dateStr
  if (typeof dateStr === 'string' && !dateStr.endsWith('Z') && !dateStr.includes('+') && !/[+-]\d{2}:\d{2}$/.test(dateStr)) {
    normalized = dateStr.replace(' ', 'T') + 'Z'
  }
  const date = new Date(normalized)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 监听弹窗打开，初始化表单数据
watch(() => appStore.showProfileModal, (isOpen) => {
  if (isOpen) {
    profileForm.value.username = authStore.userName || ''
  }
})

// 保存个人资料
async function handleSaveProfile() {
  if (!profileForm.value.username || profileForm.value.username.length < 2) {
    alert('用户名至少需要2个字符')
    return
  }

  if (profileForm.value.username.length > 20) {
    alert('用户名不能超过20个字符')
    return
  }

  saving.value = true
  try {
    // 调用API更新用户信息
    const updatedUser = await api.updateProfile({ username: profileForm.value.username })

    // 更新本地状态
    authStore.setUser(updatedUser)

    alert('个人资料已更新')
    appStore.showProfileModal = false
  } catch (error) {
    alert(error?.response?.data?.detail || error?.message || '更新失败，请重试')
  } finally {
    saving.value = false
  }
}
</script>
