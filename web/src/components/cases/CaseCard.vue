<template>
  <div
    class="item group relative flex items-center gap-2 p-2 rounded-lg border border-border-dark bg-white transition-all duration-200 hover:border-primary/50 hover:bg-primary/5 cursor-pointer"
    @click="viewDetails"
  >
    <!-- Cover Image -->
    <div class="cover shrink-0 w-10 h-10 xs:w-12 xs:h-12 rounded overflow-hidden bg-gray-100 flex items-center justify-center">
      <img
        v-if="caseData.thumbnail_url || caseData.image_url"
        :src="imageSources[0]"
        :data-fallback-src="imageSources[1] || ''"
        :alt="caseData.title"
        class="w-full h-full object-cover"
        @error="handleImageError"
      />
      <span v-else class="material-symbols-outlined !text-xl text-gray-400">image</span>
    </div>

    <!-- Title -->
    <div class="text flex-1 min-w-0">
      <h3 class="line-clamp-1 text-xs font-medium text-gray-900 xs:text-sm">
        {{ caseData.title }}
      </h3>
      <p v-if="caseData.category" class="text-[10px] text-gray-500 mt-0.5">
        {{ caseData.category }}
      </p>
    </div>

    <!-- Arrow -->
    <span class="material-symbols-outlined arrow absolute right-2 text-gray-400 group-hover:text-primary transition-colors !text-lg">
      chevron_right
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import { handleImageFallback, resolveImageSrcCandidates } from '@/utils/imageFallback'

const emit = defineEmits(['requestClose'])

const props = defineProps({
  caseData: {
    type: Object,
    required: true
  }
})

const appStore = useAppStore()

const imageSources = computed(() => {
  return resolveImageSrcCandidates(props.caseData.thumbnail_url, props.caseData.image_url)
})

const viewDetails = () => {
  try {
    appStore.setSelectedCase(props.caseData)
    emit('requestClose')
  } catch (error) {
    console.error('Error in viewDetails:', error)
  }
}

const handleImageError = (event) => {
  handleImageFallback(event)
}
</script>

<style scoped>
.item {
  width: 100%;
}

.cover {
  aspect-ratio: 1;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
