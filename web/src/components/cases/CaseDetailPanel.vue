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
      class="mx-auto mb-4 rounded-xl border border-gray-200 bg-white px-4 py-4 shadow-lg md:mx-0"
    >
      <div class="flex items-start justify-between gap-2 sm:gap-3 md:gap-4">
        <div class="w-24 shrink-0 sm:w-32 md:w-40 lg:w-48">
          <div class="relative aspect-video overflow-hidden rounded-lg bg-gray-100">
            <img
              :src="imageSources[0]"
              :data-fallback-src="imageSources[1] || ''"
              :alt="caseData.title"
              class="h-full w-full object-cover"
              @error="handleImageFallback"
            >
            <div class="absolute left-2 top-2">
              <span class="rounded bg-primary/90 px-2 py-1 text-xs font-medium text-white backdrop-blur-sm">
                {{ caseData.category }}
              </span>
            </div>
          </div>
        </div>

        <div class="min-w-0 flex-1">
          <div class="mb-2 flex items-start justify-between gap-4">
            <div class="flex-1">
              <h2 class="mb-1 text-lg font-bold text-gray-900">{{ caseData.title }}</h2>
              <p v-if="caseData.description" class="line-clamp-2 text-sm text-gray-600">
                {{ caseData.description }}
              </p>
            </div>
            <button
              class="rounded p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
              @click="closeDetail"
            >
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>
      </div>

      <div v-if="caseData.tags && caseData.tags.length > 0" class="mb-3 mt-4 flex w-full flex-wrap gap-1.5">
        <span
          v-for="tag in caseData.tags"
          :key="tag"
          class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
        >
          {{ tag }}
        </span>
      </div>

      <div class="mb-3 flex w-full items-center gap-4 text-xs text-gray-500">
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

      <div class="mb-3 w-full">
        <div class="mb-1 flex items-center justify-between">
          <h4 class="text-xs font-semibold text-gray-900">提示词</h4>
          <button
            class="flex items-center gap-1 text-xs text-primary hover:text-primary-strong"
            @click="copyPrompt"
          >
            <span class="material-symbols-outlined !text-sm">content_copy</span>
            复制
          </button>
        </div>
        <div class="max-h-20 w-full overflow-y-auto rounded-lg bg-gray-50 p-2.5">
          <p class="line-clamp-3 text-xs text-gray-700">{{ caseData.prompt }}</p>
        </div>
      </div>

      <div class="mt-4 flex w-full items-center gap-2">
        <button
          class="flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
          @click="copyPrompt"
        >
          <span class="material-symbols-outlined !text-base">content_copy</span>
          复制提示词
        </button>
        <button
          class="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-strong"
          @click="useTemplate"
        >
          <span class="material-symbols-outlined !text-base">auto_awesome</span>
          使用此模板
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import { useCaseStore } from '@/store/useCaseStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { handleImageFallback, resolveImageSrcCandidates } from '@/utils/imageFallback'

const appStore = useAppStore()
const caseStore = useCaseStore()
const generatorStore = useGeneratorStore()

const caseData = computed(() => appStore.selectedCase)
const imageSources = computed(() => {
  return resolveImageSrcCandidates(caseData.value?.image_url, caseData.value?.thumbnail_url)
})

const closeDetail = () => {
  appStore.clearSelectedCase()
}

const copyPrompt = async () => {
  if (!caseData.value) return

  const success = await caseStore.copyCasePrompt(caseData.value.id)
  if (success) {
    showToast('提示词已复制')
  }
}

const useTemplate = async () => {
  if (!caseData.value) return

  generatorStore.prompt = caseData.value.prompt
  generatorStore.negativePrompt = caseData.value.negative_prompt || ''

  if (caseData.value.parameters) {
    const params = caseData.value.parameters
    if (params.width) generatorStore.width = params.width
    if (params.height) generatorStore.height = params.height
    if (params.style) generatorStore.style = params.style
    if (params.quality) generatorStore.quality = params.quality
    if (params.seed) generatorStore.seed = params.seed
  }

  if (caseData.value.model) {
    generatorStore.model = caseData.value.model
  }

  await caseStore.useCaseTemplate(caseData.value.id)
  closeDetail()
  showToast('模板已应用')
}

const showToast = (message) => {
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
