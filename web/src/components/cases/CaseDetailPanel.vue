<template>
  <Transition
    enter-active-class="transition ease-out duration-200"
    enter-from-class="transform -translate-y-4 opacity-0"
    enter-to-class="transform translate-y-0 opacity-100"
    leave-active-class="transition ease-in duration-150"
    leave-from-class="transform translate-y-0 opacity-100"
    leave-to-class="transform -translate-y-4 opacity-0"
  >
    <div
      v-if="caseData"
      class="mx-auto md:mx-0 mb-4 px-4 py-4 bg-white rounded-xl shadow-lg border border-gray-200"
    >
      <div class="flex items-start justify-between gap-4">
        <!-- 左侧图片 -->
        <div class="w-48 flex-shrink-0">
          <div class="relative rounded-lg overflow-hidden bg-gray-100 aspect-video">
            <img
              :src="caseData.image_url || caseData.thumbnail_url || '/placeholder-case.png'"
              :alt="caseData.title"
              class="w-full h-full object-cover"
            >
            <div class="absolute top-2 left-2">
              <span class="px-2 py-1 bg-primary/90 text-white text-xs font-medium rounded backdrop-blur-sm">
                {{ caseData.category }}
              </span>
            </div>
          </div>
        </div>

        <!-- 右侧信息 -->
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-4 mb-2">
            <div class="flex-1">
              <h2 class="text-lg font-bold text-gray-900 mb-1">{{ caseData.title }}</h2>
              <p v-if="caseData.description" class="text-sm text-gray-600 line-clamp-2">{{ caseData.description }}</p>
            </div>
            <button
              @click="closeDetail"
              class="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
            >
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <!-- 标签 -->
          <div v-if="caseData.tags && caseData.tags.length > 0" class="flex flex-wrap gap-1.5 mb-3">
            <span
              v-for="tag in caseData.tags"
              :key="tag"
              class="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-full"
            >
              {{ tag }}
            </span>
          </div>

          <!-- 统计信息 -->
          <div class="flex items-center gap-4 text-xs text-gray-500 mb-3">
            <span class="flex items-center gap-1">
              <span class="material-symbols-outlined !text-sm">visibility</span>
              {{ caseData.view_count }}
            </span>
            <span class="flex items-center gap-1">
              <span class="material-symbols-outlined !text-sm">favorite</span>
              {{ caseData.use_count }}
            </span>
            <span v-if="caseData.model" class="flex items-center gap-1">
              <span class="material-symbols-outlined !text-sm">model_training</span>
              {{ caseData.model.split(' ')[0] }}
            </span>
          </div>

          <!-- 提示词预览 -->
          <div class="mb-3">
            <div class="flex items-center justify-between mb-1">
              <h4 class="text-xs font-semibold text-gray-900">提示词</h4>
              <button
                @click="copyPrompt"
                class="text-xs text-primary hover:text-primary-strong flex items-center gap-1"
              >
                <span class="material-symbols-outlined !text-sm">content_copy</span>
                复制
              </button>
            </div>
            <div class="p-2.5 bg-gray-50 rounded-lg max-h-20 overflow-y-auto">
              <p class="text-xs text-gray-700 line-clamp-3">{{ caseData.prompt }}</p>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-2">
            <button
              @click="copyPrompt"
              class="flex-1 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg transition-colors flex items-center justify-center gap-1.5"
            >
              <span class="material-symbols-outlined !text-base">content_copy</span>
              复制提示词
            </button>
            <button
              @click="useTemplate"
              class="flex-1 px-3 py-1.5 text-sm font-medium text-white bg-primary hover:bg-primary-strong rounded-lg transition-colors flex items-center justify-center gap-1.5"
            >
              <span class="material-symbols-outlined !text-base">auto_awesome</span>
              使用此模板
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import { useCaseStore } from '@/store/useCaseStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const appStore = useAppStore()
const caseStore = useCaseStore()
const generatorStore = useGeneratorStore()

const caseData = computed(() => {
  console.log('caseData computed:', appStore.selectedCase)
  return appStore.selectedCase
})

const closeDetail = () => {
  appStore.clearSelectedCase()
}

const copyPrompt = async () => {
  if (!caseData.value) return
  const success = await caseStore.copyCasePrompt(caseData.value.id)
  if (success) {
    // 显示简短的复制成功提示
    showToast('提示词已复制')
  }
}

const useTemplate = async () => {
  if (!caseData.value) return

  // 应用模板参数
  generatorStore.prompt = caseData.value.prompt
  generatorStore.negativePrompt = caseData.value.negative_prompt || ''

  // 应用其他参数
  if (caseData.value.parameters) {
    const params = caseData.value.parameters
    if (params.width) generatorStore.width = params.width
    if (params.height) generatorStore.height = params.height
    if (params.style) generatorStore.style = params.style
    if (params.quality) generatorStore.quality = params.quality
    if (params.seed) generatorStore.seed = params.seed
  }

  // 设置模型
  if (caseData.value.model) {
    generatorStore.model = caseData.value.model
  }

  // 记录使用
  await caseStore.useCaseTemplate(caseData.value.id)

  // 关闭详情面板
  closeDetail()

  showToast('模板已应用')
}

// 简单的 toast 提示
const showToast = (message) => {
  // 这里可以集成一个全局的 toast 组件
  // 暂时使用 console
  console.log(message)
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
