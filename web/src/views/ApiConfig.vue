<template>
  <div class="h-screen flex overflow-hidden bg-background-dark text-ink-950 font-display">
    <!-- 左侧导航 (hidden on mobile) -->
    <MainSidebar />

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col relative bg-white/50 min-w-0">
      <header class="h-14 md:h-16 border-b border-border-dark flex items-center justify-between px-4 md:px-8 bg-white/80 backdrop-blur-xl sticky top-0 z-10">
        <h2 class="text-base md:text-lg font-bold">中转站配置</h2>
        <span v-if="!isAdmin" class="text-xs text-red-500">需要管理员权限</span>
      </header>

      <!-- 配置内容区 -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-3 xs:p-4 sm:p-5 md:p-6 lg:p-8">
        <div class="max-w-full sm:max-w-3xl md:max-w-4xl mx-auto space-y-4 xs:space-y-5 md:space-y-6 lg:space-y-8">

          <!-- 非管理员提示 -->
          <div v-if="!isAdmin" class="bg-yellow-50 border border-yellow-200 rounded-2xl p-4 text-yellow-800">
            <p class="font-medium">权限不足</p>
            <p class="text-sm mt-1">此页面仅管理员可访问。请联系系统管理员配置中转站 API。</p>
          </div>

          <!-- 管理员配置 -->
          <template v-else>
            <!-- 中转站配置 -->
            <div class="bg-white border border-border-dark rounded-2xl p-3 xs:p-4 sm:p-5 md:p-6 space-y-3 xs:space-y-4 shadow-lg">
              <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3 xs:mb-4">
                <h3 class="text-base md:text-lg font-semibold">中转站 API 配置</h3>
                <button
                  @click="testConnection"
                  :disabled="!config.relayApiKey || isLoading"
                  class="px-3 xs:px-4 py-2 text-sm font-medium rounded-lg border border-border-dark bg-white hover:bg-primary/5 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap">
                  <span class="material-symbols-outlined !text-base align-middle mr-1">sync</span>
                  测试连接
                </button>
              </div>

              <div class="space-y-4">
                <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Base URL</label>
                  <input
                    type="text"
                    v-model="config.relayBaseUrl"
                    placeholder="https://api.example.com"
                    class="w-full bg-white border border-border-dark rounded-xl px-4 py-3 text-sm focus:ring-1 focus:ring-primary focus:border-primary">
                  <p class="text-xs text-slate-500 mt-1">中转站的 API 地址</p>
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-2">API Key</label>
                  <div class="relative">
                    <input
                      :type="showApiKey ? 'text' : 'password'"
                      v-model="config.relayApiKey"
                      :placeholder="hasExistingApiKey ? '已配置（点击修改）' : 'sk-...'"
                      class="w-full bg-white border border-border-dark rounded-xl px-4 py-3 pr-16 text-sm focus:ring-1 focus:ring-primary focus:border-primary">
                    <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                      <button
                        v-if="hasExistingApiKey && config.relayApiKey === '••••••••'"
                        @click="clearApiKey"
                        class="text-slate-400 hover:text-slate-600 p-1"
                        title="清除并重新输入">
                        <span class="material-symbols-outlined !text-lg">edit</span>
                      </button>
                      <button
                        @click="showApiKey = !showApiKey"
                        class="text-slate-400 hover:text-slate-600 p-1"
                        :title="showApiKey ? '隐藏' : '显示'">
                        <span class="material-symbols-outlined !text-lg">{{ showApiKey ? 'visibility_off' : 'visibility' }}</span>
                      </button>
                    </div>
                  </div>
                  <p class="text-xs text-slate-500 mt-1">
                    <template v-if="hasExistingApiKey">已配置 API Key（加密存储），点击编辑图标可修改</template>
                    <template v-else>中转站的 API Key，将加密存储</template>
                  </p>
                </div>
              <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-2">模型配置 API URL</label>
                  <input
                    type="text"
                    v-model="config.configApiUrl"
                    placeholder="https://config.example.com"
                    class="w-full bg-white border border-border-dark rounded-xl px-4 py-3 text-sm focus:ring-1 focus:ring-primary focus:border-primary">
                  <p class="text-xs text-slate-500 mt-1">用于获取模型列表和配置的 API 地址（可选）</p>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex flex-col sm:flex-row gap-2 xs:gap-3 md:gap-4">
              <button
                @click="saveConfig"
                :disabled="isLoading"
                class="flex-1 py-3 bg-primary-strong text-white rounded-xl font-semibold hover:bg-primary-deep transition-colors text-sm xs:text-base shadow-lg disabled:opacity-50 disabled:cursor-not-allowed">
                <span v-if="isLoading" class="material-symbols-outlined !text-base align-middle mr-1 animate-spin">refresh</span>
                保存配置
              </button>
              <button
                @click="loadConfig"
                :disabled="isLoading"
                class="flex-1 py-3 bg-white border border-border-dark text-ink-700 rounded-xl font-semibold hover:bg-primary/5 transition-colors text-sm xs:text-base disabled:opacity-50 disabled:cursor-not-allowed">
                重置
              </button>
            </div>

            <!-- 配置说明 -->
            <div class="bg-blue-50 border border-blue-200 rounded-2xl p-4 text-blue-800">
              <p class="font-medium">配置说明</p>
              <ul class="text-sm mt-2 space-y-1 list-disc list-inside">
                <li>此配置为全局配置，所有用户将使用相同的 API Key</li>
                <li>API Key 会被加密存储在数据库中</li>
                <li>修改配置后立即生效，无需重启服务</li>
              </ul>
            </div>
          </template>
        </div>
      </div>

      <!-- 移动端底部 tab 导航 -->
      <nav class="md:hidden flex border-t border-border-dark bg-white/90 shrink-0">
        <button
          @click="appStore.setCurrentPage('agent')"
          class="flex-1 flex flex-col items-center py-3 text-[10px] gap-1 text-ink-500 transition-colors">
          <span class="material-symbols-outlined !text-xl">smart_toy</span>
          工作室
        </button>
        <button
          class="flex-1 flex flex-col items-center py-3 text-[10px] gap-1 text-primary">
          <span class="material-symbols-outlined !text-xl">api</span>
          配置
        </button>
      </nav>
    </main>
  </div>
</template>

<script setup>
import MainSidebar from '../components/sidebar/MainSidebar.vue'
import { useAppStore } from '@/store/useAppStore'
import { onMounted, ref, reactive, computed } from 'vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/store/useAuthStore'

const appStore = useAppStore()
const authStore = useAuthStore()
const isLoading = ref(false)
const showApiKey = ref(false)

// 使用 authStore 的 userRole 计算属性
const isAdmin = computed(() => authStore.userRole === 'admin')

const config = reactive({
  relayBaseUrl: '',
  relayApiKey: '',
  configApiUrl: ''
})

// 记录原始 API Key 是否已配置（用于判断是否需要保存）
const hasExistingApiKey = ref(false)

// 检查管理员权限并加载配置
async function initPage() {
  // 如果未登录，等待 authStore 初始化
  if (!authStore.isAuthenticated) {
    authStore.init()
  }

  // 如果是管理员，加载配置
  if (isAdmin.value) {
    await loadConfig()
  }
}

// 加载配置
async function loadConfig() {
  if (!isAdmin.value) return

  isLoading.value = true
  try {
    const configs = await api.getSystemConfigs()

    // 解析配置
    for (const item of configs) {
      if (item.config_key === 'relay.base_url') {
        config.relayBaseUrl = item.config_value || ''
      } else if (item.config_key === 'relay.api_key') {
        // API Key 是加密存储的，后端返回占位符表示已配置
        if (item.config_value === '••••••••') {
          config.relayApiKey = '••••••••'
          hasExistingApiKey.value = true
        } else {
          config.relayApiKey = ''
          hasExistingApiKey.value = false
        }
      } else if (item.config_key === 'config.api_url') {
        config.configApiUrl = item.config_value || ''
      }
    }

    console.log('配置加载完成')
  } catch (error) {
    console.error('加载配置失败:', error)
    // 如果是权限错误，可能不是管理员
    if (error?.response?.status === 403) {
      alert('权限不足：此页面仅管理员可访问')
    } else {
      alert('加载配置失败: ' + (error?.response?.data?.detail || error?.message || '未知错误'))
    }
  } finally {
    isLoading.value = false
  }
}

// 保存配置
async function saveConfig() {
  if (!isAdmin.value) return

  console.log('saveConfig - 当前 config 对象:', JSON.stringify(config, null, 2))

  if (!config.relayBaseUrl) {
    alert('请填写 Base URL')
    return
  }

  isLoading.value = true
  try {
    const configs = {
      'relay.base_url': config.relayBaseUrl,
      'config.api_url': config.configApiUrl
    }

    // 只有当 API Key 不是占位符时才保存（表示用户输入了新值）
    if (config.relayApiKey && config.relayApiKey !== '••••••••') {
      configs['relay.api_key'] = config.relayApiKey
    }

    console.log('saveConfig - 准备发送的配置:', JSON.stringify(configs, null, 2))
    await api.batchUpdateSystemConfigs(configs)

    alert('配置保存成功！')

    // 重新加载配置
    await loadConfig()
  } catch (error) {
    console.error('保存配置失败:', error)
    alert('保存配置失败: ' + (error?.response?.data?.detail || error?.message || '未知错误'))
  } finally {
    isLoading.value = false
  }
}

// 测试连接
async function testConnection() {
  isLoading.value = true
  try {
    // 调用模型列表接口测试连接
    const response = await api.getModels('image')
    const count = response.models?.length || 0
    alert(`连接测试成功！\n\n发现 ${count} 个可用模型。`)
  } catch (error) {
    console.error('连接测试失败:', error)
    alert('连接测试失败: ' + (error?.response?.data?.detail || error?.message || '未知错误'))
  } finally {
    isLoading.value = false
  }
}

// 清空 API Key（允许用户重新输入）
function clearApiKey() {
  config.relayApiKey = ''
  hasExistingApiKey.value = false
}

// 组件挂载
onMounted(async () => {
  await initPage()
})
</script>
