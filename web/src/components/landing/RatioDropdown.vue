<template>
  <div class="relative" ref="dropdownRef">
    <button
      @click="toggleDropdown"
      class="w-full flex items-center justify-between px-3 py-2 bg-white border border-border-dark rounded-lg hover:border-primary/50 transition-colors">
      <span class="text-sm">{{ currentRatioLabel }}</span>
      <span class="material-symbols-outlined !text-lg text-ink-500 shrink-0">expand_more</span>
    </button>

    <Transition name="dropdown">
      <div
        v-if="isOpen"
        class="absolute top-full left-0 right-0 mt-1 bg-white border border-border-dark rounded-lg shadow-lg z-50 overflow-hidden">
        <div class="max-h-48 overflow-y-auto custom-scrollbar p-1">
          <div
            v-for="ratio in ratioOptions"
            :key="ratio.value"
            @click="selectRatio(ratio)"
            :class="[
              'flex items-center justify-between px-3 py-2 rounded-lg text-sm cursor-pointer transition-colors',
              selectedRatio === ratio.value ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-gray-50'
            ]">
            <div class="flex items-center gap-2">
              <span class="font-medium">{{ ratio.label }}</span>
              <span class="text-xs text-ink-500">{{ ratio.desc }}</span>
            </div>
            <div class="flex items-center gap-1 text-xs text-ink-500">
              <span>{{ ratio.w }}×{{ ratio.h }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Custom Ratio Modal -->
    <div
      v-if="showCustomModal"
      @click="showCustomModal = false"
      class="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/10 p-4 backdrop-blur-sm">
      <div
        @click.stop
        class="bg-white border border-border-dark rounded-xl p-4 max-w-sm w-full shadow-xl">
        <h3 class="text-sm font-semibold mb-3">自定义比例</h3>
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
        <p class="text-xs text-ink-500 mt-2">提示：输入宽高后，将根据当前质量设置自动调整</p>
        <div class="flex justify-end gap-2 mt-3">
          <button
            @click="showCustomModal = false"
            class="px-4 py-2 text-sm text-ink-700 hover:bg-gray-100 rounded-lg transition-colors">
            取消
          </button>
          <button
            @click="applyCustomRatio"
            class="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-strong transition-colors">
            确定
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const generatorStore = useGeneratorStore()
const isOpen = ref(false)
const selectedRatio = ref('1:1')
const showCustomModal = ref(false)
const customWidth = ref(1024)
const customHeight = ref(1024)
const dropdownRef = ref(null)

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

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const selectRatio = (ratio) => {
  if (ratio.value === 'custom') {
    // Open custom ratio modal
    customWidth.value = generatorStore.width
    customHeight.value = generatorStore.height
    showCustomModal.value = true
    isOpen.value = false
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
    showCustomModal.value = false
  }
}

const handleClickOutside = (event) => {
  // Don't close if clicking on the modal
  if (showCustomModal.value) return
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
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
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // Initialize selected ratio from store
  if (generatorStore.aspectRatio) {
    selectedRatio.value = generatorStore.aspectRatio
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #d1d8d3;
  border-radius: 10px;
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.dropdown-enter-active > div,
.dropdown-leave-active > div {
  transition: transform 0.2s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
}
.dropdown-enter-from > div,
.dropdown-leave-to > div {
  transform: translateY(-8px);
}
</style>
