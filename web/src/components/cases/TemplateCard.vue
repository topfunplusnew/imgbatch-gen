<template>
  <div
    @click="viewDetails"
    class="template-card group cursor-pointer border border-border-dark hover:border-primary/50 hover:shadow-md active:border-primary active:shadow-lg transition-all duration-200 rounded-lg bg-white p-2 xs:p-2.5 sm:p-3.5 md:p-4 lg:p-5 select-none"
  >
    <div class="flex items-start gap-2 xs:gap-2.5 sm:gap-3">
      <div class="flex-1 min-w-0 flex flex-col justify-center">
        <!-- Title -->
        <h3 class="font-semibold text-ink-950 text-[11px] xs:text-xs sm:text-sm md:text-base lg:text-base leading-tight line-clamp-1 mb-0.5 xs:mb-1 sm:mb-1.5 md:mb-2">
          {{ caseData.title }}
        </h3>

        <!-- Description -->
        <p v-if="caseData.description" class="text-[9px] xs:text-[10px] sm:text-xs md:text-xs text-gray-500 line-clamp-1 xs:line-clamp-2 sm:line-clamp-2 md:line-clamp-2 lg:line-clamp-3 mb-1 xs:mb-1.5 sm:mb-2 md:mb-2.5 break-words hidden xs:block">
          {{ caseData.description }}
        </p>

        <!-- Category badge and tags -->
        <div class="flex items-center gap-1 xs:gap-1.5 sm:gap-2 md:gap-2.5">
          <span class="inline-block px-1 xs:px-1.5 sm:px-2 md:px-2.5 py-0.5 rounded-md text-[9px] xs:text-[10px] sm:text-xs md:text-sm font-medium bg-primary/10 text-primary whitespace-nowrap">
            {{ caseData.category }}
          </span>

          <div v-if="caseData.tags && caseData.tags.length > 0" class="flex gap-0.5 xs:gap-1 sm:gap-1.5 flex-wrap">
            <span
              v-for="tag in caseData.tags.slice(0, 2)"
              :key="tag"
              class="px-0.5 xs:px-1 sm:px-1.5 py-0.5 rounded text-[9px] xs:text-[10px] sm:text-xs text-gray-500 bg-gray-100 hidden xs:inline-block"
            >
              {{ tag }}
            </span>
            <span v-if="caseData.tags.length > 2" class="px-0.5 xs:px-1 sm:px-1.5 py-0.5 rounded text-[9px] xs:text-[10px] sm:text-xs text-gray-400 hidden xs:inline-block">
              +{{ caseData.tags.length - 2 }}
            </span>
          </div>
        </div>
      </div>

      <button
        class="shrink-0 rounded-md bg-primary px-2 py-1 text-[10px] font-medium text-white transition-colors hover:bg-primary-strong xs:px-2.5 xs:text-xs sm:px-3 sm:py-1.5"
        @click.stop="useTemplate"
      >
        使用
      </button>
    </div>
  </div>
</template>

<script setup>
import { useAppStore } from '@/store/useAppStore'
import { useCaseStore } from '@/store/useCaseStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const props = defineProps({
  caseData: {
    type: Object,
    required: true
  }
})

const appStore = useAppStore()
const caseStore = useCaseStore()
const generatorStore = useGeneratorStore()

const viewDetails = () => {
  console.log('viewDetails clicked', props.caseData)
  try {
    appStore.setSelectedCase(props.caseData)
    console.log('setSelectedCase called successfully')
  } catch (error) {
    console.error('Error in viewDetails:', error)
  }
}

const useTemplate = async () => {
  generatorStore.prompt = props.caseData.prompt
  generatorStore.negativePrompt = props.caseData.negative_prompt || ''

  if (props.caseData.parameters) {
    const params = props.caseData.parameters
    if (params.width) generatorStore.width = params.width
    if (params.height) generatorStore.height = params.height
    if (params.style) generatorStore.style = params.style
    if (params.quality) generatorStore.quality = params.quality
    if (params.seed) generatorStore.seed = params.seed
  }

  if (props.caseData.model) {
    generatorStore.model = props.caseData.model
  }

  await caseStore.useCaseTemplate(props.caseData.id)
}
</script>

<style scoped>
.template-card {
  width: 100%;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

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
