<template>
  <div
    @click="viewDetails"
    class="group relative rounded-lg overflow-hidden border border-border-dark hover:border-primary/50 hover:shadow-lg transition-all duration-200 bg-white cursor-pointer"
  >
    <!-- 图片 -->
    <div class="relative w-full aspect-[4/3] overflow-hidden bg-gray-100">
      <img
        :src="imageSources[0]"
        :data-fallback-src="imageSources[1] || ''"
        :alt="caseData.title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        @error="handleImageFallback"
      >

      <!-- 分类标签 -->
      <div class="absolute top-2 left-2">
        <span class="px-2 py-1 bg-primary/90 text-white text-xs font-medium rounded">
          {{ caseData.category }}
        </span>
      </div>

      <!-- 悬浮操作遮罩 -->
      <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-2">
        <button
          @click.stop="copyPrompt"
          class="p-2 bg-white/90 hover:bg-white rounded-lg transition-colors"
          title="复制提示词"
        >
          <span class="material-symbols-outlined !text-lg text-gray-700">content_copy</span>
        </button>
        <button
          @click.stop="useTemplate"
          class="p-2 bg-primary hover:bg-primary-strong rounded-lg transition-colors"
          title="使用模板"
        >
          <span class="material-symbols-outlined !text-lg text-white">auto_awesome</span>
        </button>
      </div>
    </div>

    <!-- 信息区域 -->
    <div class="p-2">
      <h4 class="font-semibold text-gray-900 text-sm leading-tight line-clamp-2 mb-1">{{ caseData.title }}</h4>
      <div class="flex items-center gap-1 text-xs text-gray-500">
        <span class="material-symbols-outlined !text-sm">visibility</span>
        <span>{{ caseData.view_count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useCaseStore } from '@/store/useCaseStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAppStore } from '@/store/useAppStore'
import { handleImageFallback, resolveImageSrcCandidates } from '@/utils/imageFallback'

const props = defineProps({
  caseData: {
    type: Object,
    required: true
  }
})

const caseStore = useCaseStore()
const generatorStore = useGeneratorStore()
const appStore = useAppStore()

const imageSources = computed(() => {
  return resolveImageSrcCandidates(props.caseData.thumbnail_url, props.caseData.image_url)
})

const viewDetails = () => {
  appStore.setSelectedCase(props.caseData)
}

const copyPrompt = async () => {
  const success = await caseStore.copyCasePrompt(props.caseData.id)
  // 显示简短提示
  console.log(success ? '已复制' : '复制失败')
}

const useTemplate = async () => {
  // 应用模板参数
  generatorStore.prompt = props.caseData.prompt
  generatorStore.negativePrompt = props.caseData.negative_prompt || ''

  // 应用其他参数
  if (props.caseData.parameters) {
    const params = props.caseData.parameters
    if (params.width) generatorStore.width = params.width
    if (params.height) generatorStore.height = params.height
    if (params.style) generatorStore.style = params.style
    if (params.quality) generatorStore.quality = params.quality
    if (params.seed) generatorStore.seed = params.seed
  }

  // 设置模型
  if (props.caseData.model) {
    generatorStore.model = props.caseData.model
  }

  // 记录使用
  await caseStore.useCaseTemplate(props.caseData.id)

  console.log('模板已应用')
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
