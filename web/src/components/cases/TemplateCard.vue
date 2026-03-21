<template>
  <div
    @click="viewDetails"
    class="template-card group cursor-pointer border border-border-dark hover:border-primary/50 hover:shadow-md transition-all duration-200 rounded-lg bg-white p-3 xs:p-4"
  >
    <div class="flex gap-3">
      <!-- Thumbnail on left -->
      <div class="relative w-16 xs:w-20 md:w-20 h-16 xs:h-20 md:h-20 flex-shrink-0 overflow-hidden bg-gray-100 rounded-lg">
        <img
          :src="caseData.thumbnail_url || caseData.image_url || '/placeholder-case.png'"
          :alt="caseData.title"
          class="w-full h-full object-cover"
          @error="handleImageError"
        >
      </div>

      <!-- Content on right -->
      <div class="flex-1 min-w-0 flex flex-col justify-center">
        <!-- Title -->
        <h3 class="font-semibold text-ink-950 text-sm xs:text-base leading-tight line-clamp-1 mb-1">
          {{ caseData.title }}
        </h3>

        <!-- Description -->
        <p v-if="caseData.description" class="text-xs text-gray-500 line-clamp-2 mb-2">
          {{ caseData.description }}
        </p>

        <!-- Category badge and tags -->
        <div class="flex items-center gap-2">
          <span class="inline-block px-2 py-0.5 rounded-md text-xs font-medium bg-primary/10 text-primary whitespace-nowrap">
            {{ caseData.category }}
          </span>

          <div v-if="caseData.tags && caseData.tags.length > 0" class="flex gap-1 flex-wrap">
            <span
              v-for="tag in caseData.tags.slice(0, 2)"
              :key="tag"
              class="px-1.5 py-0.5 rounded text-xs text-gray-500 bg-gray-100"
            >
              {{ tag }}
            </span>
            <span v-if="caseData.tags.length > 2" class="px-1.5 py-0.5 rounded text-xs text-gray-400">
              +{{ caseData.tags.length - 2 }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAppStore } from '@/store/useAppStore'

const props = defineProps({
  caseData: {
    type: Object,
    required: true
  }
})

const appStore = useAppStore()

const handleImageError = (event) => {
  event.target.src = '/placeholder-case.png'
}

const viewDetails = () => {
  console.log('viewDetails clicked', props.caseData)
  try {
    appStore.setSelectedCase(props.caseData)
    console.log('setSelectedCase called successfully')
  } catch (error) {
    console.error('Error in viewDetails:', error)
  }
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
</style>
