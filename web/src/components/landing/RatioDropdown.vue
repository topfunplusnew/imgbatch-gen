<template>
  <div>
    <button
      @click="isOpen = true"
      class="flex items-center justify-center p-2 bg-white border border-border-dark rounded-lg hover:border-primary/50 transition-colors"
      :title="currentRatioLabel">
      <span class="material-symbols-outlined !text-xl text-primary">crop_free</span>
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
            class="bg-white border border-border-dark rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
            <!-- Header -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-border-dark">
              <h3 class="text-sm font-bold text-ink-950">选择比例</h3>
              <button @click="isOpen = false" class="text-ink-500 hover:text-ink-950 transition-colors">
                <span class="material-symbols-outlined !text-xl">close</span>
              </button>
            </div>

            <!-- Ratio Grid -->
            <div class="p-4 grid grid-cols-3 gap-2 max-h-[60vh] overflow-y-auto custom-scrollbar">
              <button
                v-for="ratio in ratioOptions"
                :key="ratio.value"
                @click="selectRatio(ratio)"
                :class="[
                  'flex flex-col items-center justify-center gap-1 p-3 rounded-xl transition-colors',
                  selectedRatio === ratio.value
                    ? 'bg-primary-strong text-white shadow-sm'
                    : 'bg-white text-ink-700 border border-border-dark hover:bg-primary/5'
                ]">
                <!-- 比例预览框 -->
                <div class="flex items-center justify-center w-8 h-8">
                  <div
                    :style="getRatioBoxStyle(ratio)"
                    :class="[
                      'rounded-sm border-2',
                      selectedRatio === ratio.value ? 'border-white' : 'border-slate-500'
                    ]">
                  </div>
                </div>
                <span class="text-xs font-bold leading-tight">{{ ratio.label }}</span>
                <span class="text-[10px] opacity-80">{{ ratio.desc }}</span>
              </button>
            </div>

            <!-- Custom Ratio Input -->
            <div v-if="selectedRatio === 'custom'" class="px-4 pb-4 border-t border-border-dark">
              <div class="grid grid-cols-2 gap-2">
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
              </div>
              <button
                @click="applyCustomRatio"
                class="w-full mt-2 px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-strong transition-colors">
                应用自定义尺寸
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const generatorStore = useGeneratorStore()
const isOpen = ref(false)
const selectedRatio = ref('1:1')
const customWidth = ref(1024)
const customHeight = ref(1024)

const ratioOptions = [
  { value: 'auto',  label: 'Auto',  desc: '自动',   w: 1024, h: 1024 },
  { value: '1:1',   label: '1:1',   desc: '方形',   w: 1024, h: 1024 },
  { value: '3:4',   label: '3:4',   desc: '竖版',   w: 768,  h: 1024 },
  { value: '4:3',   label: '4:3',   desc: '横版',   w: 1024, h: 768  },
  { value: '9:16',  label: '9:16',  desc: '竖版',   w: 576,  h: 1024 },
  { value: '16:9',  label: '16:9',  desc: '横版',   w: 1024, h: 576  },
  { value: '2:3',   label: '2:3',   desc: '竖版',   w: 683,  h: 1024 },
  { value: '3:2',   label: '3:2',   desc: '横版',   w: 1024, h: 683  },
  { value: '4:5',   label: '4:5',   desc: '竖版',   w: 819,  h: 1024 },
  { value: '5:4',   label: '5:4',   desc: '横版',   w: 1024, h: 819  },
  { value: '21:9',  label: '21:9',  desc: '影院',   w: 1024, h: 439  },
  { value: 'custom',label: '自定义', desc: '更多',   w: null, h: null },
]

const currentRatioLabel = computed(() => {
  if (selectedRatio.value === 'custom') {
    return `${generatorStore.width}×${generatorStore.height}`
  }
  const current = ratioOptions.find(r => r.value === selectedRatio.value)
  return current ? `${current.label} ${current.desc}` : '选择比例'
})

const getRatioBoxStyle = (ratio) => {
  if (!ratio.w || !ratio.h) return { width: '20px', height: '20px' }
  const maxDim = 24
  const r = ratio.w / ratio.h
  if (r >= 1) {
    return { width: `${maxDim}px`, height: `${Math.round(maxDim / r)}px` }
  } else {
    return { width: `${Math.round(maxDim * r)}px`, height: `${maxDim}px` }
  }
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

  // Calculate dimensions based on current quality
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

  // Also update the aspect ratio in store
  generatorStore.aspectRatio = ratio.value
}

const applyCustomRatio = () => {
  if (customWidth.value >= 64 && customWidth.value <= 8192 &&
      customHeight.value >= 64 && customHeight.value <= 8192) {
    generatorStore.width = customWidth.value
    generatorStore.height = customHeight.value
    generatorStore.aspectRatio = 'custom'
    selectedRatio.value = 'custom'
    isOpen.value = false
  }
}

// Watch for store changes to sync selected ratio
watch(() => [generatorStore.width, generatorStore.height], () => {
  const ratio = generatorStore.width / generatorStore.height
  // Allow some tolerance for floating point comparison
  if (Math.abs(ratio - 1) < 0.01) selectedRatio.value = '1:1'
  else if (Math.abs(ratio - 4/3) < 0.01) selectedRatio.value = '4:3'
  else if (Math.abs(ratio - 16/9) < 0.01) selectedRatio.value = '16:9'
  else if (Math.abs(ratio - 3/4) < 0.01) selectedRatio.value = '3:4'
  else if (Math.abs(ratio - 9/16) < 0.01) selectedRatio.value = '9:16'
  else if (Math.abs(ratio - 2/3) < 0.01) selectedRatio.value = '2:3'
  else if (Math.abs(ratio - 3/2) < 0.01) selectedRatio.value = '3:2'
  else if (Math.abs(ratio - 4/5) < 0.01) selectedRatio.value = '4:5'
  else if (Math.abs(ratio - 5/4) < 0.01) selectedRatio.value = '5:4'
  else if (Math.abs(ratio - 21/9) < 0.01) selectedRatio.value = '21:9'
  else selectedRatio.value = 'custom'
}, { immediate: true })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

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
