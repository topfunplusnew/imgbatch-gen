<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/20 p-4 backdrop-blur-sm"
    @click="close"
  >
    <div class="max-h-[95vh] w-full max-w-7xl overflow-auto rounded-2xl bg-white shadow-xl" @click.stop>
      <div class="sticky top-0 z-10 flex items-center justify-between border-b border-border-dark bg-white/95 px-4 py-3 backdrop-blur-xl">
        <h3 class="text-base font-semibold text-ink-950">生成结果（{{ images.length }}）</h3>
        <button @click="close" class="text-ink-500 transition-colors hover:text-ink-950" type="button">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <div class="p-4">
        <div class="grid gap-4" :class="gridClass">
          <div
            v-for="(url, index) in images"
            :key="index"
            class="group relative overflow-hidden rounded-xl border border-border-dark bg-background-dark"
          >
            <img :src="url" class="w-full h-auto" @load="onImageLoad" />
            <div class="absolute inset-0 flex items-center justify-center bg-ink-950/0 transition-colors group-hover:bg-ink-950/20">
              <button
                @click="downloadImage(url, index)"
                class="scale-90 transform rounded-lg border border-white/40 bg-white/90 px-4 py-2 text-sm font-medium text-ink-950 opacity-0 transition-all hover:bg-white group-hover:scale-100 group-hover:opacity-100"
                type="button"
              >
                <span class="material-symbols-outlined mr-1 align-middle !text-base">download</span>
                下载
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const visible = ref(false)
const images = ref([])
const imageCount = ref(0)

const gridClass = computed(() => {
  const count = images.value.length

  if (count === 1) return 'mx-auto max-w-3xl grid-cols-1'
  if (count === 2) return 'grid-cols-1 md:grid-cols-2'
  return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
})

const show = (urls) => {
  images.value = urls
  imageCount.value = 0
  visible.value = true
}

const close = () => {
  visible.value = false
}

const onImageLoad = () => {
  imageCount.value++
}

const downloadImage = async (url, index) => {
  try {
    const response = await fetch(url)
    const blob = await response.blob()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `image_${Date.now()}_${index + 1}.jpg`
    link.click()
  } catch (error) {
    console.error('下载失败:', error)
  }
}

defineExpose({ show })
</script>
