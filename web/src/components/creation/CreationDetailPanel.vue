<template>
  <div v-if="creation" class="bg-white rounded-xl border border-border-dark shadow-sm overflow-hidden mb-6">
    <!-- 主要内容区域 -->
    <div class="flex flex-col lg:flex-row gap-6 p-6">
      <!-- 左侧图片区域 -->
      <div class="w-full lg:w-1/2">
        <div class="aspect-video rounded-lg overflow-hidden bg-gray-100">
          <img
            v-if="creation.image_urls && creation.image_urls.length > 0"
            :src="creation.image_urls[0]"
            :alt="creation.prompt"
            class="w-full h-full object-cover"
          >
          <div v-else class="w-full h-full flex items-center justify-center text-ink-300">
            <span class="material-symbols-outlined !text-6xl">image</span>
          </div>
        </div>

        <!-- 多图展示 -->
        <div
          v-if="creation.image_urls && creation.image_urls.length > 1"
          class="grid grid-cols-4 gap-2 mt-2"
        >
          <div
            v-for="(url, index) in creation.image_urls.slice(1, 5)"
            :key="index"
            class="aspect-video rounded-lg overflow-hidden bg-gray-100 cursor-pointer hover:ring-2 hover:ring-primary/50"
          >
            <img :src="url" :alt="`图片 ${index + 2}`" class="w-full h-full object-cover">
          </div>
        </div>
      </div>

      <!-- 右侧信息区域 -->
      <div class="w-full lg:w-1/2 flex flex-col">
        <div class="flex-1">
          <h3 class="text-lg font-bold text-ink-950 mb-3 line-clamp-2">
            {{ creation.prompt.substring(0, 100) }}{{ creation.prompt.length > 100 ? '...' : '' }}
          </h3>

          <!-- 元信息 -->
          <div class="space-y-2 mb-4">
            <div class="flex items-center gap-2 text-sm text-ink-600">
              <span class="material-symbols-outlined !text-base">model_training</span>
              <span>{{ creation.model || '未知模型' }}</span>
            </div>
            <div class="flex items-center gap-2 text-sm text-ink-600">
              <span class="material-symbols-outlined !text-base">schedule</span>
              <span>{{ formatDate(creation.timestamp || creation.created_at) }}</span>
            </div>
            <div v-if="creation.type" class="flex items-center gap-2 text-sm text-ink-600">
              <span class="material-symbols-outlined !text-base">category</span>
              <span>{{ creation.type === 'chat' ? '对话生成' : '异步任务' }}</span>
            </div>
          </div>

          <!-- 提示词预览 -->
          <div class="bg-gray-50 rounded-lg p-3 mb-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-medium text-ink-600">提示词</span>
              <button
                @click="copyPrompt"
                class="text-xs text-primary hover:text-primary-strong flex items-center gap-1"
              >
                <span class="material-symbols-outlined !text-sm">content_copy</span>
                复制
              </button>
            </div>
            <p class="text-sm text-ink-700 line-clamp-3">{{ creation.prompt }}</p>
          </div>

          <!-- 参数信息 -->
          <div v-if="creation.extra_params" class="bg-gray-50 rounded-lg p-3">
            <span class="text-xs font-medium text-ink-600 block mb-2">生成参数</span>
            <div class="grid grid-cols-2 gap-2 text-xs text-ink-600">
              <div v-if="creation.extra_params.width">
                <span class="font-medium">尺寸:</span> {{ creation.extra_params.width }}x{{ creation.extra_params.height }}
              </div>
              <div v-if="creation.extra_params.quality">
                <span class="font-medium">质量:</span> {{ creation.extra_params.quality }}
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex gap-2 mt-4">
          <button
            @click="useTemplate"
            class="flex-1 px-4 py-2 bg-primary hover:bg-primary-strong text-white rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-colors"
          >
            <span class="material-symbols-outlined !text-base">auto_awesome</span>
            使用此模板
          </button>
          <button
            @click="closeDetail"
            class="px-4 py-2 border border-border-dark hover:bg-gray-50 text-ink-700 rounded-lg font-medium text-sm transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const appStore = useAppStore()
const generatorStore = useGeneratorStore()

const creation = computed(() => appStore.selectedCreation)

const formatDate = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

const copyPrompt = async () => {
  if (!creation.value) return
  try {
    await navigator.clipboard.writeText(creation.value.prompt)
    console.log('提示词已复制')
  } catch (error) {
    console.error('复制失败:', error)
  }
}

const useTemplate = () => {
  if (!creation.value) return

  // 应用提示词
  generatorStore.prompt = creation.value.prompt

  // 应用参数
  if (creation.value.extra_params) {
    const params = creation.value.extra_params
    if (params.width) generatorStore.width = params.width
    if (params.height) generatorStore.height = params.height
    if (params.quality) generatorStore.quality = params.quality
    if (params.negative_prompt) generatorStore.negativePrompt = params.negative_prompt
  }

  // 设置模型
  if (creation.value.model) {
    generatorStore.model = creation.value.model
  }

  console.log('模板已应用')
}

const closeDetail = () => {
  appStore.setSelectedCreation(null)
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
