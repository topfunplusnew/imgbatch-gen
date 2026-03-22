<template>
  <div class="relative" ref="dropdownRef">
    <button
      @click="toggleDropdown"
      class="w-full flex items-center justify-between px-3 py-2 bg-white border border-border-dark rounded-lg hover:border-primary/50 transition-colors">
      <span class="text-sm">{{ currentResolutionLabel }}</span>
      <span class="material-symbols-outlined !text-lg text-ink-500 shrink-0">expand_more</span>
    </button>

    <Transition name="dropdown">
      <div
        v-if="isOpen"
        class="absolute top-full left-0 right-0 mt-1 bg-white border border-border-dark rounded-lg shadow-lg z-50 overflow-hidden">
        <div class="p-1">
          <div
            v-for="quality in qualityOptions"
            :key="quality.value"
            @click="selectQuality(quality.value)"
            :class="[
              'flex items-center justify-between px-3 py-2 rounded-lg text-sm cursor-pointer transition-colors',
              generatorStore.quality === quality.value ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-gray-50'
            ]">
            <span class="font-medium">{{ quality.label }}</span>
            <span class="text-xs text-ink-500">{{ quality.desc }}</span>
          </div>
          <div class="border-t border-border-dark mt-1 pt-1">
            <div
              @click="openCustomResolution"
              class="flex items-center justify-between px-3 py-2 rounded-lg text-sm cursor-pointer transition-colors hover:bg-gray-50">
              <span class="font-medium">自定义</span>
              <span class="text-xs text-ink-500">输入尺寸</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Custom Resolution Modal -->
    <div
      v-if="showCustomModal"
      @click="showCustomModal = false"
      class="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/10 p-4 backdrop-blur-sm">
      <div
        @click.stop
        class="bg-white border border-border-dark rounded-xl p-4 max-w-sm w-full shadow-xl">
        <h3 class="text-sm font-semibold mb-3">自定义分辨率</h3>
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
        <div class="flex justify-end gap-2 mt-3">
          <button
            @click="showCustomModal = false"
            class="px-4 py-2 text-sm text-ink-700 hover:bg-gray-100 rounded-lg transition-colors">
            取消
          </button>
          <button
            @click="applyCustomResolution"
            class="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-strong transition-colors">
            确定
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const generatorStore = useGeneratorStore()
const isOpen = ref(false)
const showCustomModal = ref(false)
const customWidth = ref(1024)
const customHeight = ref(1024)
const dropdownRef = ref(null)

const qualityOptions = [
  { value: '720p', label: '720P', desc: '快速生成' },
  { value: '2k',   label: '2K',   desc: '标准' },
  { value: '4k',   label: '4K',   desc: '超清' },
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

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
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

const openCustomResolution = () => {
  customWidth.value = generatorStore.width
  customHeight.value = generatorStore.height
  showCustomModal.value = true
  isOpen.value = false
}

const applyCustomResolution = () => {
  if (customWidth.value >= 64 && customWidth.value <= 8192 &&
      customHeight.value >= 64 && customHeight.value <= 8192) {
    generatorStore.width = customWidth.value
    generatorStore.height = customHeight.value
    generatorStore.quality = 'custom'
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

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
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
