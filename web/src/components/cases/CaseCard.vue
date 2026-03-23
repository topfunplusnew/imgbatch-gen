<template>
  <div class="case-card group relative rounded-lg overflow-hidden border border-border-dark hover:border-primary/50 hover:shadow-md transition-all duration-200 bg-white">
    <!-- 横向布局：左侧图片，右侧标题 -->
    <div class="flex gap-2 p-2 xs:p-2.5 items-center">
      <!-- 左侧图片 -->
      <div class="relative w-12 xs:w-14 sm:w-12 h-12 xs:h-14 sm:h-12 flex-shrink-0 overflow-hidden bg-gray-100 rounded">
        <img
          :src="caseData.thumbnail_url || caseData.image_url || '/placeholder-case.png'"
          :alt="caseData.title"
          class="w-full h-full object-cover"
          @error="handleImageError"
        >
      </div>

      <!-- 右侧标题 -->
      <div class="flex-1 min-w-0 flex items-center">
        <h3 class="font-semibold text-gray-900 text-xs xs:text-sm leading-tight line-clamp-1">{{ caseData.title }}</h3>
      </div>

      <!-- 操作按钮 -->
      <div class="flex items-center pl-1 border-l border-gray-200 flex-shrink-0">
        <button
          @click="viewDetails"
          class="p-1.5 xs:p-2 min-h-[40px] xs:min-h-[44px] min-w-[40px] xs:min-w-[44px] text-gray-500 hover:text-primary hover:bg-primary/5 rounded transition-colors flex items-center justify-center"
          title="查看详情"
        >
          <span class="material-symbols-outlined !text-base xs:!text-lg">more_horiz</span>
        </button>
      </div>
    </div>

    <!-- Toast 提示 -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="transform opacity-0 scale-90"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-90"
    >
      <div
        v-if="toast.show"
        :class="[
          'fixed bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg shadow-lg text-sm font-medium z-50',
          toast.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        ]"
      >
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined !text-base">
            {{ toast.type === 'success' ? 'check_circle' : 'error' }}
          </span>
          {{ toast.message }}
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useCaseStore } from '@/store/useCaseStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAppStore } from '@/store/useAppStore'

const props = defineProps({
  caseData: {
    type: Object,
    required: true
  }
})

const caseStore = useCaseStore()
const generatorStore = useGeneratorStore()
const appStore = useAppStore()

const toast = reactive({
  show: false,
  message: '',
  type: 'success'
})

let toastTimeout = null

const showToast = (message, type = 'success') => {
  toast.message = message
  toast.type = type
  toast.show = true

  if (toastTimeout) clearTimeout(toastTimeout)
  toastTimeout = setTimeout(() => {
    toast.show = false
  }, 2000)
}

const handleImageError = (event) => {
  event.target.src = '/placeholder-case.png'
}

const viewDetails = () => {
  console.log('viewDetails clicked', props.caseData)
  try {
    appStore.setSelectedCase(props.caseData)
    console.log('setSelectedCase called successfully')
  } catch (error) {
    console.error('Error in viewDetails:', error)
  }
}

const copyPrompt = async () => {
  console.log('copyPrompt clicked')
  try {
    const success = await caseStore.copyCasePrompt(props.caseData.id)
    if (success) {
      showToast('提示词已复制到剪贴板', 'success')
    } else {
      showToast('复制失败，请手动复制', 'error')
    }
  } catch (error) {
    console.error('Error in copyPrompt:', error)
    showToast('复制失败，请重试', 'error')
  }
}

const useTemplate = async () => {
  console.log('useTemplate clicked', props.caseData)
  try {
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
      if (params.negative_prompt) generatorStore.negativePrompt = params.negative_prompt
      if (params.seed) generatorStore.seed = params.seed
    }

    // 设置模型
    if (props.caseData.model) {
      generatorStore.model = props.caseData.model
    }

    // 记录使用
    await caseStore.useCaseTemplate(props.caseData.id)

    // 切换到生成页面
    appStore.setCurrentPage('agent')

    showToast('模板已应用，开始生成吧！', 'success')
  } catch (error) {
    console.error('Error in useTemplate:', error)
    showToast('应用模板失败，请重试', 'error')
  }
}
</script>

<style scoped>
.case-card {
  width: 100%;
  cursor: pointer;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
