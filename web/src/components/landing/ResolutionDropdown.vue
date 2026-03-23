<template>
  <div>
    <button
      @click="isOpen = true"
      class="flex items-center justify-center p-2 bg-white border border-border-dark rounded-lg hover:border-primary/50 transition-colors"
      :title="currentResolutionLabel">
      <span class="material-symbols-outlined !text-xl text-primary">high_quality</span>
    </button>

    <!-- Teleport Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="isOpen"
          @click="isOpen = false"
          class="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/10 backdrop-blur-sm p-4">
          <div
            @click.stop
            class="bg-white border border-border-dark rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
            <!-- Header -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-border-dark">
              <h3 class="text-sm font-bold text-ink-950">图像质量</h3>
              <button @click="isOpen = false" class="text-ink-500 hover:text-ink-950 transition-colors">
                <span class="material-symbols-outlined !text-xl">close</span>
              </button>
            </div>

            <!-- Quality Options -->
            <div class="p-4 space-y-3">
              <button
                v-for="quality in qualityOptions"
                :key="quality.value"
                @click="selectQuality(quality.value)"
                :class="[
                  'w-full flex items-center justify-between px-4 py-3 rounded-xl transition-colors',
                  generatorStore.quality === quality.value
                    ? 'bg-primary-strong text-white shadow-sm'
                    : 'bg-white text-ink-700 border border-border-dark hover:bg-primary/5'
                ]">
                <div class="flex flex-col items-start">
                  <span class="text-sm font-bold">{{ quality.label }}</span>
                  <span class="text-xs opacity-80">{{ quality.desc }}</span>
                </div>
                <div class="text-right">
                  <div class="text-xs opacity-80">最大尺寸</div>
                  <div class="text-sm font-bold">{{ getMaxDim(quality.value) }}px</div>
                </div>
              </button>

              <!-- Custom Resolution -->
              <div class="border-t border-border-dark pt-3 mt-3">
                <button
                  @click="showCustomInput = !showCustomInput"
                  class="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-border-dark hover:bg-primary/5 transition-colors">
                  <div class="flex flex-col items-start">
                    <span class="text-sm font-medium text-ink-700">自定义尺寸</span>
                    <span class="text-xs text-ink-500">{{ generatorStore.width }}×{{ generatorStore.height }}</span>
                  </div>
                  <span class="material-symbols-outlined !text-lg text-ink-500">
                    {{ showCustomInput ? 'expand_less' : 'expand_more' }}
                  </span>
                </button>

                <div v-if="showCustomInput" class="grid grid-cols-2 gap-2 mt-3">
                  <input
                    v-model.number="customWidth"
                    type="number"
                    placeholder="宽度"
                    min="64"
                    max="8192"
                    class="w-full px-3 py-2 border border-border-dark rounded-lg text-sm focus:ring-1 focus:ring-primary focus:outline-none">
                  <input
                    v-model.number="customHeight"
                    type="number"
                    placeholder="高度"
                    min="64"
                    max="8192"
                    class="w-full px-3 py-2 border border-border-dark rounded-lg text-sm focus:ring-1 focus:ring-primary focus:outline-none">
                  <button
                    @click="applyCustomResolution"
                    class="col-span-2 px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-strong transition-colors">
                    应用自定义尺寸
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
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
  { value: '2k',   label: '2K',   desc: '标准质量，平衡速度' },
  { value: '4k',   label: '4K',   desc: '超清质量，细节丰富' },
]

const currentResolutionLabel = computed(() => {
  const quality = qualityOptions.find(q => q.value === generatorStore.quality)
  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  const maxDim = maxDimMap[generatorStore.quality]

  // Check if current dimensions match the expected dimensions for this quality
  const ratio = generatorStore.width / generatorStore.height
  let expectedWidth, expectedHeight
  if (ratio >= 1) {
    expectedWidth = maxDim
    expectedHeight = Math.round(maxDim / ratio)
  } else {
    expectedHeight = maxDim
    expectedWidth = Math.round(maxDim * ratio)
  }

  // If dimensions match expected, show quality label
  if (generatorStore.width === expectedWidth && generatorStore.height === expectedHeight && quality) {
    return `${quality.label} ${quality.desc}`
  }

  // Otherwise show actual dimensions
  return `${generatorStore.width}×${generatorStore.height}`
})

const getMaxDim = (qualityValue) => {
  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  return maxDimMap[qualityValue] || 2048
}

const selectQuality = (qualityValue) => {
  generatorStore.quality = qualityValue
  isOpen.value = false

  // Adjust dimensions based on new quality
  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  const maxDim = maxDimMap[qualityValue]

  // Calculate current ratio
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
  if (customWidth.value >= 64 && customWidth.value <= 8192 &&
      customHeight.value >= 64 && customHeight.value <= 8192) {
    generatorStore.width = customWidth.value
    generatorStore.height = customHeight.value
    isOpen.value = false
  }
}
</script>

<style scoped>
/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-to,
.modal-leave-from {
  opacity: 1;
}

/* Scale animation */
.modal-enter-active > div > div:last-child,
.modal-leave-active > div > div:last-child {
  transition: transform 0.2s ease;
}
.modal-enter-from > div > div:last-child,
.modal-leave-to > div > div:last-child {
  transform: scale(0.95);
}
.modal-enter-to > div > div:last-child,
.modal-leave-from > div > div:last-child {
  transform: scale(1);
}
</style>
