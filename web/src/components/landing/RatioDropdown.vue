<template>
  <div class="relative">
    <el-button round class="landing-select-trigger" @click="isOpen = true" :title="currentRatioLabel">
      <span class="material-symbols-outlined !text-lg text-primary">crop_free</span>
      <span class="hidden text-sm font-medium xs:inline">{{ currentRatio?.desc || '自适应' }}</span>
    </el-button>

    <el-dialog
      v-model="isOpen"
      align-center
      append-to-body
      class="landing-ratio-dialog"
      width="min(560px, calc(100vw - 32px))"
    >
      <template #header>
        <div>
          <h3 class="text-lg font-semibold text-ink-950">选择比例</h3>
          <p class="mt-1 text-sm text-ink-500">根据当前质量自动计算尺寸。</p>
        </div>
      </template>

      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
          <el-button
            v-for="ratio in ratioOptions"
            :key="ratio.value"
            :type="selectedRatio === ratio.value ? 'primary' : 'default'"
            :plain="selectedRatio !== ratio.value"
            class="ratio-option-button !h-auto !whitespace-normal !px-3 !py-3"
            @click="selectRatio(ratio)"
          >
            <div class="flex flex-col items-center gap-1 text-center">
              <div class="flex h-9 w-9 items-center justify-center">
                <div
                  :style="getRatioBoxStyle(ratio)"
                  :class="[
                    'rounded-sm border-2 transition-colors',
                    selectedRatio === ratio.value ? 'border-white' : 'border-slate-400'
                  ]"
                ></div>
              </div>
              <span class="text-xs font-semibold">{{ ratio.label }}</span>
              <span class="text-[10px] opacity-80">{{ ratio.desc }}</span>
            </div>
          </el-button>
        </div>

        <div v-if="selectedRatio === 'custom'" class="space-y-3 border-t border-border-dark pt-4">
          <div class="grid grid-cols-2 gap-3">
            <el-input-number v-model="customWidth" :min="64" :max="8192" controls-position="right" />
            <el-input-number v-model="customHeight" :min="64" :max="8192" controls-position="right" />
          </div>
          <el-button type="primary" class="w-full" @click="applyCustomRatio">应用自定义尺寸</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const generatorStore = useGeneratorStore()
const isOpen = ref(false)
const selectedRatio = ref('auto')
const customWidth = ref(1024)
const customHeight = ref(1024)

const ratioOptions = [
  { value: 'auto', label: 'Auto', desc: '自动', w: 0, h: 0 },
  { value: '1:1', label: '1:1', desc: '方形', w: 1024, h: 1024 },
  { value: '3:4', label: '3:4', desc: '竖版', w: 768, h: 1024 },
  { value: '4:3', label: '4:3', desc: '横版', w: 1024, h: 768 },
  { value: '9:16', label: '9:16', desc: '竖版', w: 576, h: 1024 },
  { value: '16:9', label: '16:9', desc: '横版', w: 1024, h: 576 },
  { value: '2:3', label: '2:3', desc: '竖版', w: 683, h: 1024 },
  { value: '3:2', label: '3:2', desc: '横版', w: 1024, h: 683 },
  { value: '4:5', label: '4:5', desc: '竖版', w: 819, h: 1024 },
  { value: '5:4', label: '5:4', desc: '横版', w: 1024, h: 819 },
  { value: '21:9', label: '21:9', desc: '影院', w: 1024, h: 439 },
  { value: 'custom', label: '自定义', desc: '更多', w: null, h: null }
]

const currentRatioLabel = computed(() => {
  if (selectedRatio.value === 'custom') {
    return `${generatorStore.width}×${generatorStore.height}`
  }
  const current = ratioOptions.find((ratio) => ratio.value === selectedRatio.value)
  return current ? `${current.label} ${current.desc}` : '选择比例'
})

const currentRatio = computed(() => {
  return ratioOptions.find((ratio) => ratio.value === selectedRatio.value)
})

const getRatioBoxStyle = (ratio) => {
  if (!ratio.w || !ratio.h) return { width: '20px', height: '20px' }
  const maxDim = 24
  const ratioValue = ratio.w / ratio.h
  if (ratioValue >= 1) {
    return { width: `${maxDim}px`, height: `${Math.round(maxDim / ratioValue)}px` }
  }
  return { width: `${Math.round(maxDim * ratioValue)}px`, height: `${maxDim}px` }
}

const selectRatio = (ratio) => {
  if (ratio.value === 'custom') {
    customWidth.value = generatorStore.width
    customHeight.value = generatorStore.height
    selectedRatio.value = 'custom'
    return
  }

  selectedRatio.value = ratio.value
  isOpen.value = false

  if (ratio.value === 'auto') {
    generatorStore.width = 0
    generatorStore.height = 0
    generatorStore.aspectRatio = 'auto'
    return
  }

  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  const maxDim = maxDimMap[generatorStore.quality] || 2048
  const ratioValue = ratio.w / ratio.h

  if (ratioValue >= 1) {
    generatorStore.width = maxDim
    generatorStore.height = Math.round(maxDim / ratioValue)
  } else {
    generatorStore.height = maxDim
    generatorStore.width = Math.round(maxDim * ratioValue)
  }

  generatorStore.aspectRatio = ratio.value
}

const applyCustomRatio = () => {
  if (customWidth.value >= 64 && customWidth.value <= 8192 && customHeight.value >= 64 && customHeight.value <= 8192) {
    generatorStore.width = customWidth.value
    generatorStore.height = customHeight.value
    generatorStore.aspectRatio = 'custom'
    selectedRatio.value = 'custom'
    isOpen.value = false
  }
}

watch(
  () => [generatorStore.width, generatorStore.height],
  () => {
    // width/height 为 0 表示 auto
    if (!generatorStore.width || !generatorStore.height) {
      selectedRatio.value = 'auto'
      return
    }
    const ratio = generatorStore.width / generatorStore.height
    if (Math.abs(ratio - 1) < 0.01) selectedRatio.value = '1:1'
    else if (Math.abs(ratio - 4 / 3) < 0.01) selectedRatio.value = '4:3'
    else if (Math.abs(ratio - 16 / 9) < 0.01) selectedRatio.value = '16:9'
    else if (Math.abs(ratio - 3 / 4) < 0.01) selectedRatio.value = '3:4'
    else if (Math.abs(ratio - 9 / 16) < 0.01) selectedRatio.value = '9:16'
    else if (Math.abs(ratio - 2 / 3) < 0.01) selectedRatio.value = '2:3'
    else if (Math.abs(ratio - 3 / 2) < 0.01) selectedRatio.value = '3:2'
    else if (Math.abs(ratio - 4 / 5) < 0.01) selectedRatio.value = '4:5'
    else if (Math.abs(ratio - 5 / 4) < 0.01) selectedRatio.value = '5:4'
    else if (Math.abs(ratio - 21 / 9) < 0.01) selectedRatio.value = '21:9'
    else selectedRatio.value = 'custom'
  },
  { immediate: true }
)
</script>

<style scoped>
.landing-select-trigger {
  border-radius: 999px;
}
</style>
