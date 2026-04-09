<template>
  <div class="relative">
    <el-button round class="landing-select-trigger" @click="isOpen = true" :title="currentResolutionLabel">
      <span class="material-symbols-outlined !text-lg text-primary">high_quality</span>
      <span class="hidden text-sm font-medium xs:inline">{{ currentQuality?.label || '2K' }}</span>
    </el-button>

    <el-dialog
      v-model="isOpen"
      align-center
      append-to-body
      class="landing-resolution-dialog"
      width="min(460px, calc(100vw - 32px))"
    >
      <template #header>
        <div>
          <h3 class="text-lg font-semibold text-ink-950">图像质量</h3>
          <p class="mt-1 text-sm text-ink-500">切换质量时会同步调整当前尺寸上限。</p>
        </div>
      </template>

      <div class="space-y-3">
        <el-card
          v-for="quality in qualityOptions"
          :key="quality.value"
          shadow="hover"
          class="resolution-option cursor-pointer"
          :class="{ 'resolution-option--active': generatorStore.quality === quality.value }"
          @click="selectQuality(quality.value)"
        >
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="text-sm font-semibold text-ink-950">{{ quality.label }}</div>
              <div class="mt-1 text-xs text-ink-500">{{ quality.desc }}</div>
            </div>
            <div class="text-right">
              <div class="text-[11px] text-ink-500">最大尺寸</div>
              <div class="text-sm font-semibold text-primary">{{ getMaxDim(quality.value) }}px</div>
            </div>
          </div>
        </el-card>

        <div class="space-y-3 border-t border-border-dark pt-4">
          <el-button class="w-full justify-between" @click="showCustomInput = !showCustomInput">
            <div class="flex flex-col items-start">
              <span class="text-sm font-medium text-ink-700">自定义尺寸</span>
              <span class="text-xs text-ink-500">{{ generatorStore.width }}×{{ generatorStore.height }}</span>
            </div>
            <span class="material-symbols-outlined !text-lg text-ink-500">
              {{ showCustomInput ? 'expand_less' : 'expand_more' }}
            </span>
          </el-button>

          <div v-if="showCustomInput" class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <el-input-number v-model="customWidth" :min="64" :max="8192" controls-position="right" />
              <el-input-number v-model="customHeight" :min="64" :max="8192" controls-position="right" />
            </div>
            <el-button type="primary" class="w-full" @click="applyCustomResolution">应用自定义尺寸</el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const generatorStore = useGeneratorStore()
const isOpen = ref(false)
const showCustomInput = ref(false)
const customWidth = ref(1024)
const customHeight = ref(1024)

const qualityOptions = [
  { value: '720p', label: '720P', desc: '快速生成，适合预览' },
  { value: '2k', label: '2K', desc: '标准质量，平衡速度' },
  { value: '4k', label: '4K', desc: '超清质量，细节丰富' }
]

const currentResolutionLabel = computed(() => {
  const quality = qualityOptions.find((item) => item.value === generatorStore.quality)
  if (!generatorStore.width || !generatorStore.height) {
    return quality ? `${quality.label} ${quality.desc}` : '自动尺寸'
  }
  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  const maxDim = maxDimMap[generatorStore.quality]

  const ratio = generatorStore.width / generatorStore.height
  let expectedWidth
  let expectedHeight

  if (ratio >= 1) {
    expectedWidth = maxDim
    expectedHeight = Math.round(maxDim / ratio)
  } else {
    expectedHeight = maxDim
    expectedWidth = Math.round(maxDim * ratio)
  }

  if (generatorStore.width === expectedWidth && generatorStore.height === expectedHeight && quality) {
    return `${quality.label} ${quality.desc}`
  }

  return `${generatorStore.width}×${generatorStore.height}`
})

const currentQuality = computed(() => {
  return qualityOptions.find((item) => item.value === generatorStore.quality)
})

const getMaxDim = (qualityValue) => {
  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  return maxDimMap[qualityValue] || 2048
}

const selectQuality = (qualityValue) => {
  generatorStore.quality = qualityValue
  isOpen.value = false

  if (!generatorStore.width || !generatorStore.height) {
    return
  }

  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  const maxDim = maxDimMap[qualityValue]
  const ratio = generatorStore.width / generatorStore.height

  if (ratio >= 1) {
    generatorStore.width = maxDim
    generatorStore.height = Math.round(maxDim / ratio)
  } else {
    generatorStore.height = maxDim
    generatorStore.width = Math.round(maxDim * ratio)
  }
}

const applyCustomResolution = () => {
  if (customWidth.value >= 64 && customWidth.value <= 8192 && customHeight.value >= 64 && customHeight.value <= 8192) {
    generatorStore.width = customWidth.value
    generatorStore.height = customHeight.value
    isOpen.value = false
  }
}
</script>

<style scoped>
.landing-select-trigger {
  border-radius: 999px;
}

.resolution-option {
  border-radius: 20px;
  border-color: var(--color-border-dark);
}

.resolution-option--active {
  border-color: rgba(140, 42, 46, 0.3);
  background: rgba(140, 42, 46, 0.06);
}

.resolution-option :deep(.el-card__body) {
  padding: 14px 16px;
}
</style>
