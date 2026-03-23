<template>
  <div class="h-screen flex overflow-hidden bg-background-dark text-ink-950 font-display">
    <!-- 左侧导航 (hidden on mobile) -->
    <MainSidebar />

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col relative bg-white/50 min-w-0">
      <header class="h-14 md:h-16 border-b border-border-dark flex items-center justify-between px-4 md:px-8 bg-white/80 backdrop-blur-xl sticky top-0 z-10">
        <h2 class="text-base md:text-lg font-bold">API 配置</h2>
      </header>

      <!-- 配置内容区 -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-3 xs:p-4 sm:p-5 md:p-6 lg:p-8">
        <div class="max-w-full sm:max-w-3xl md:max-w-4xl mx-auto space-y-4 xs:space-y-5 md:space-y-6 lg:space-y-8">
          <!-- API 配置 -->
          <div class="bg-white border border-border-dark rounded-2xl p-3 xs:p-4 sm:p-5 md:p-6 space-y-3 xs:space-y-4 shadow-lg">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3 xs:mb-4">
              <h3 class="text-base md:text-lg font-semibold">API 配置</h3>
              <button
                @click="testConnection"
                :disabled="!apiStore.apiKey"
                class="px-3 xs:px-4 py-2 text-sm font-medium rounded-lg border border-border-dark bg-white hover:bg-primary/5 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap">
                <span class="material-symbols-outlined !text-base align-middle mr-1">sync</span>
                测试连接
              </button>
            </div>

            <div class="space-y-4">
              <div>
                <label class="block text-xs font-bold text-slate-500 uppercase mb-2">API Key</label>
                <input
                  type="password"
                  :value="apiStore.apiKey"
                  @input="apiStore.setApiKey($event.target.value)"
                  placeholder="输入您的 API Key"
                  class="w-full bg-white border border-border-dark rounded-xl px-4 py-3 text-sm focus:ring-1 focus:ring-primary focus:border-primary">
              </div>
            </div>
          </div>

          <!-- 默认模型设置 -->
          <div class="bg-white border border-border-dark rounded-2xl p-3 xs:p-4 sm:p-5 md:p-6 space-y-3 xs:space-y-4 shadow-lg">
            <h3 class="text-base md:text-lg font-semibold mb-4">默认模型设置</h3>
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase mb-2">默认模型</label>
              <select
                v-model="apiStore.defaultModel"
                @change="apiStore.setDefaultModel($event.target.value)"
                :disabled="isLoadingModels"
                class="w-full bg-white border border-border-dark rounded-xl px-4 py-3 text-sm focus:ring-1 focus:ring-primary focus:border-primary disabled:opacity-50 disabled:cursor-not-allowed">
                <option v-if="isLoadingModels" value="">加载模型中...</option>
                <option v-else-if="models.length === 0" value="">暂无可用模型</option>
                <option v-else-if="!apiStore.defaultModel" value="">请选择默认模型</option>
                <option v-for="model in models" :key="model.id" :value="model.model_name">
                  {{ model.model_name }}
                </option>
              </select>
              <div class="flex items-center justify-between mt-1">
                <p v-if="!isLoadingModels && models.length > 0" class="text-[10px] text-slate-500">
                  共 {{ models.length }} 个可用模型
                </p>
                <button
                  v-if="!isLoadingModels"
                  @click="loadModels"
                  class="text-xs text-primary hover:text-primary/80 flex items-center gap-1">
                  <span class="material-symbols-outlined !text-sm">refresh</span>
                  刷新列表
                </button>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex flex-col sm:flex-row gap-2 xs:gap-3 md:gap-4">
            <button
              @click="saveConfig"
              class="flex-1 py-3 bg-primary-strong text-white rounded-xl font-semibold hover:bg-primary-deep transition-colors text-sm xs:text-base shadow-lg">
              保存配置
            </button>
            <button
              @click="apiStore.resetConfig()"
              class="flex-1 py-3 bg-white border border-border-dark text-ink-700 rounded-xl font-semibold hover:bg-primary/5 transition-colors text-sm xs:text-base">
              重置配置
            </button>
          </div>
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
import { useApiConfigStore } from '@/store/useApiConfigStore'
import { useAppStore } from '@/store/useAppStore'
import { onMounted, ref } from 'vue'
import { api } from '@/services/api'

const apiStore = useApiConfigStore()
const appStore = useAppStore()
const models = ref([])
const isLoadingModels = ref(false)

// 加载模型列表
async function loadModels() {
  isLoadingModels.value = true
  try {
    const response = await api.getModels('image')
    models.value = response.models || []

    // 按模型名称排序
    models.value.sort((a, b) => a.model_name.localeCompare(b.model_name))

    // 如果当前默认模型不在列表中，设置为第一个模型
    if (models.value.length > 0 && !models.value.find(m => m.model_name === apiStore.defaultModel)) {
      apiStore.setDefaultModel(models.value[0].model_name)
    }

    console.log(`已加载 ${models.value.length} 个图像模型`)
  } catch (error) {
    console.error('加载模型列表失败:', error)
    models.value = []
    alert('加载模型列表失败，请检查后端连接')
  } finally {
    isLoadingModels.value = false
  }
}

const testConnection = async () => {
  // API 端点已固定，直接测试
  if (!apiStore.apiKey) {
    alert('请先填写 API Key')
    return
  }

  // 显示加载状态
  const button = event.target
  const originalText = button.innerHTML
  button.innerHTML = '<span class="material-symbols-outlined !text-base align-middle mr-1 animate-spin">refresh</span> 测试中...'
  button.disabled = true

  try {
    const success = await apiStore.testConnection()
    if (success) {
      alert('✅ 连接测试成功！\n\n后端服务正常运行。')

      // 如果连接成功，重新加载模型列表
      await loadModels()
    } else {
      alert('❌ 连接测试失败\n\n请检查后端服务是否正常运行')
    }
  } catch (error) {
    alert('❌ 连接测试出错：' + (error?.message || String(error)))
  } finally {
    button.innerHTML = originalText
    button.disabled = false
  }
}

const saveConfig = () => {
  // 保存到本地存储（API端点固定，不保存）
  localStorage.setItem('apiConfig', JSON.stringify({
    apiKey: apiStore.apiKey,
    // apiEndpoint 使用相对路径，不需要保存
    defaultModel: apiStore.defaultModel
  }))
  alert('✅ 配置已保存到本地存储！')
}

// 组件挂载时加载保存的配置
onMounted(async () => {
  // API 端点已固定，直接设置
  apiStore.setApiEndpoint('')

  const savedConfig = localStorage.getItem('apiConfig')
  if (savedConfig) {
    try {
      const config = JSON.parse(savedConfig)
      // 只加载 API key 和默认模型
      if (config.apiKey) apiStore.setApiKey(config.apiKey)
      if (config.defaultModel) apiStore.setDefaultModel(config.defaultModel)
      // API endpoint 保持固定值
    } catch (error) {
      console.error('加载保存的配置失败:', error)
    }
  }

  // 加载模型列表
  await loadModels()
})
</script>

