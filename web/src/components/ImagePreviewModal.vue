<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-[120] flex items-center justify-center bg-ink-950/82 p-3 sm:p-6 backdrop-blur-md"
    @click="close"
  >
    <div
      class="flex max-h-[94vh] w-full max-w-6xl flex-col overflow-hidden rounded-[28px] border border-white/10 bg-ink-950 shadow-[0_32px_120px_rgba(0,0,0,0.45)]"
      @click.stop
    >
      <div class="flex items-center justify-between border-b border-white/10 px-4 py-3 text-white sm:px-5">
        <div class="min-w-0">
          <p class="text-sm font-medium text-white/70">图片预览</p>
          <p class="truncate text-sm sm:text-base">{{ currentImage.alt || '生成结果' }}</p>
        </div>

        <div class="ml-4 flex items-center gap-2 sm:gap-3">
          <span class="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/75">
            {{ currentIndex + 1 }} / {{ images.length }}
          </span>
          <button
            type="button"
            class="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/10 p-2 text-white transition-colors hover:bg-white/20"
            title="下载当前图片"
            @click="downloadCurrent"
          >
            <span class="material-symbols-outlined !text-[20px]">download</span>
          </button>
          <button
            type="button"
            class="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/10 p-2 text-white transition-colors hover:bg-white/20"
            title="关闭预览"
            @click="close"
          >
            <span class="material-symbols-outlined !text-[20px]">close</span>
          </button>
        </div>
      </div>

      <div class="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.12),transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))] px-4 py-5 sm:px-6">
        <button
          v-if="hasMultiple"
          type="button"
          class="absolute left-3 top-1/2 z-10 inline-flex -translate-y-1/2 items-center justify-center rounded-full border border-white/15 bg-black/35 p-2 text-white transition-colors hover:bg-black/55 sm:left-5"
          title="上一张"
          @click="showPrev"
        >
          <span class="material-symbols-outlined">chevron_left</span>
        </button>

        <div class="flex h-full w-full items-center justify-center">
          <img
            v-if="currentImage.url"
            :key="currentImage.url"
            :src="currentImage.url"
            :alt="currentImage.alt || '生成结果'"
            class="max-h-[72vh] max-w-full rounded-2xl object-contain shadow-[0_20px_80px_rgba(0,0,0,0.45)]"
          >
        </div>

        <button
          v-if="hasMultiple"
          type="button"
          class="absolute right-3 top-1/2 z-10 inline-flex -translate-y-1/2 items-center justify-center rounded-full border border-white/15 bg-black/35 p-2 text-white transition-colors hover:bg-black/55 sm:right-5"
          title="下一张"
          @click="showNext"
        >
          <span class="material-symbols-outlined">chevron_right</span>
        </button>
      </div>

      <div v-if="hasMultiple" class="border-t border-white/10 bg-white/[0.03] px-4 py-3 sm:px-5">
        <div class="flex gap-3 overflow-x-auto pb-1">
          <button
            v-for="(image, index) in images"
            :key="`${image.url}-${index}`"
            type="button"
            class="relative h-16 w-16 shrink-0 overflow-hidden rounded-2xl border transition-all sm:h-20 sm:w-20"
            :class="index === currentIndex ? 'border-white shadow-[0_0_0_2px_rgba(255,255,255,0.2)]' : 'border-white/10 opacity-70 hover:opacity-100'"
            @click="setCurrent(index)"
          >
            <img :src="image.url" :alt="image.alt || `预览图 ${index + 1}`" class="h-full w-full object-cover" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, getCurrentInstance, onUnmounted, ref, watch } from 'vue'

const emit = defineEmits(['download'])

const visible = ref(false)
const images = ref([])
const currentIndex = ref(0)
const instance = getCurrentInstance()

const currentImage = computed(() => images.value[currentIndex.value] || { url: '', alt: '' })
const hasMultiple = computed(() => images.value.length > 1)

function normalizeImage(image, index) {
  if (!image) return null
  if (typeof image === 'string') {
    return {
      url: image,
      alt: `图片 ${index + 1}`,
    }
  }

  const url = image.url || image.src || ''
  if (!url) return null

  return {
    ...image,
    url,
    alt: image.alt || image.name || `图片 ${index + 1}`,
  }
}

function show(items, startIndex = 0) {
  const normalizedImages = (Array.isArray(items) ? items : [items])
    .map((image, index) => normalizeImage(image, index))
    .filter(Boolean)

  if (normalizedImages.length === 0) return

  images.value = normalizedImages
  currentIndex.value = Math.min(Math.max(startIndex, 0), normalizedImages.length - 1)
  visible.value = true
}

function close() {
  visible.value = false
}

function setCurrent(index) {
  currentIndex.value = index
}

function showPrev() {
  if (!hasMultiple.value) return
  currentIndex.value = (currentIndex.value - 1 + images.value.length) % images.value.length
}

function showNext() {
  if (!hasMultiple.value) return
  currentIndex.value = (currentIndex.value + 1) % images.value.length
}

async function fallbackDownload(image) {
  const response = await fetch(image.url)
  if (!response.ok) throw new Error(`下载失败: ${response.status}`)

  const blob = await response.blob()
  const blobUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  const ext = blob.type.includes('jpeg') ? 'jpg' : (blob.type.split('/')[1] || 'png')

  link.href = blobUrl
  link.download = `${image.alt || 'image'}-${Date.now()}.${ext}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(blobUrl)
}

async function downloadCurrent() {
  const image = currentImage.value
  if (!image?.url) return

  if (instance?.vnode?.props?.onDownload) {
    emit('download', image, currentIndex.value)
    return
  }

  await fallbackDownload(image)
}

function handleKeydown(event) {
  if (!visible.value) return

  if (event.key === 'Escape') {
    close()
  } else if (event.key === 'ArrowLeft') {
    showPrev()
  } else if (event.key === 'ArrowRight') {
    showNext()
  }
}

watch(visible, (isVisible) => {
  if (isVisible) {
    window.addEventListener('keydown', handleKeydown)
  } else {
    window.removeEventListener('keydown', handleKeydown)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

defineExpose({ show, close })
</script>
