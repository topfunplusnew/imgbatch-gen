<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between p-3 border-b border-border-dark shrink-0">
      <span class="font-bold text-sm uppercase tracking-wider text-ink-950">全部模板</span>
      <button @click="appStore.closeTemplateDrawer()" class="text-ink-500 hover:text-ink-950 transition-colors">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <!-- Category Filter -->
    <div class="shrink-0 px-3 py-2.5 border-b border-border-dark">
      <div class="relative flex items-center gap-1">
        <!-- Left arrow button -->
        <button
          v-if="canScrollLeft"
          @click="scrollCategories('left')"
          class="flex-shrink-0 w-5 h-5 bg-white shadow-sm rounded flex items-center justify-center text-gray-500 hover:text-primary hover:shadow transition-all text-xs"
        >
          <span class="material-symbols-outlined !text-sm">chevron_left</span>
        </button>

        <!-- Scrollable category container -->
        <div
          ref="categoryScrollRef"
          class="flex items-center gap-1.5 overflow-x-auto overflow-y-hidden pb-1 scrollbar-hide scroll-smooth flex-1"
          @scroll="updateScrollState"
        >
          <button
            @click="selectCategory(null)"
            :class="[
              'px-2 xs:px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors flex-shrink-0',
              !selectedCategory
                ? 'bg-primary text-white'
                : 'bg-white text-ink-700 hover:bg-gray-50 border border-border-dark'
            ]"
          >
            全部
          </button>
          <button
            v-for="cat in categories"
            :key="cat"
            @click="selectCategory(cat)"
            :class="[
              'px-2 xs:px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors flex-shrink-0',
              selectedCategory === cat
                ? 'bg-primary text-white'
                : 'bg-white text-ink-700 hover:bg-gray-50 border border-border-dark'
            ]"
          >
            {{ cat }}
          </button>
        </div>

        <!-- Right arrow button -->
        <button
          v-if="canScrollRight"
          @click="scrollCategories('right')"
          class="flex-shrink-0 w-5 h-5 bg-white shadow-sm rounded flex items-center justify-center text-gray-500 hover:text-primary hover:shadow transition-all text-xs"
        >
          <span class="material-symbols-outlined !text-sm">chevron_right</span>
        </button>
      </div>
    </div>

    <!-- Template Grid -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-3">
      <!-- Loading state -->
      <div v-if="loading && displayCases.length === 0" class="flex items-center justify-center py-8">
        <div class="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>

      <!-- Empty state -->
      <div v-else-if="displayCases.length === 0 && !loading" class="text-center py-12">
        <span class="material-symbols-outlined text-4xl text-gray-300 mb-2">search_off</span>
        <p class="text-sm text-gray-500">暂无模板</p>
      </div>

      <!-- Template cards grid -->
      <div v-else class="space-y-2 xs:space-y-2.5">
        <TemplateCard
          v-for="caseItem in displayCases"
          :key="caseItem.id"
          :case-data="caseItem"
        />
      </div>

      <!-- Load more indicator -->
      <div v-if="loading && displayCases.length > 0" class="flex items-center justify-center py-4">
        <div class="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>

      <!-- No more -->
      <div v-else-if="!hasMore && displayCases.length > 0" class="text-center py-4">
        <p class="text-xs text-gray-400">已加载全部模板</p>
      </div>

      <!-- Load more button -->
      <div v-else-if="hasMore && displayCases.length > 0" class="text-center py-3">
        <button
          @click="loadMore"
          class="px-4 py-1.5 text-xs font-medium text-primary hover:bg-primary/5 rounded-lg transition-colors"
        >
          加载更多
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useCaseStore } from '@/store/useCaseStore'
import { useAppStore } from '@/store/useAppStore'
import TemplateCard from './TemplateCard.vue'

const caseStore = useCaseStore()
const appStore = useAppStore()
const categoryScrollRef = ref(null)
const selectedCategory = ref(null)

// Category scroll state
const canScrollLeft = ref(false)
const canScrollRight = ref(false)

// Get categories
const categories = computed(() => {
  return caseStore.categories
})

// Get cases
const cases = computed(() => caseStore.cases)
const loading = computed(() => caseStore.loading)
const hasMore = computed(() => caseStore.hasMore)

// Filtered and searched cases
const displayCases = computed(() => {
  let result = cases.value

  // Filter by category
  if (selectedCategory.value) {
    result = result.filter(c => c.category === selectedCategory.value)
  }

  return result
})

const selectCategory = (category) => {
  selectedCategory.value = category
}

// Update scroll state
const updateScrollState = () => {
  if (!categoryScrollRef.value) return

  const el = categoryScrollRef.value
  canScrollLeft.value = el.scrollLeft > 0
  canScrollRight.value = el.scrollLeft < el.scrollWidth - el.clientWidth - 1
}

// Scroll categories
const scrollCategories = (direction) => {
  if (!categoryScrollRef.value) return

  const el = categoryScrollRef.value
  const scrollAmount = 150

  if (direction === 'left') {
    el.scrollBy({ left: -scrollAmount, behavior: 'smooth' })
  } else {
    el.scrollBy({ left: scrollAmount, behavior: 'smooth' })
  }
}

// Load more cases
const loadMore = () => {
  caseStore.loadMore()
}

onMounted(() => {
  // Initialize cases if not already loaded
  if (caseStore.cases.length === 0) {
    caseStore.initialize()
  }

  // Initialize scroll state
  setTimeout(() => {
    updateScrollState()
  }, 100)
})

onUnmounted(() => {
  // Clean up if needed
})

// Watch for category changes to update scroll state
watch(() => categories, () => {
  setTimeout(() => {
    updateScrollState()
  }, 100)
}, { deep: true })
</script>

<style scoped>
/* Smooth scrolling */
.scroll-smooth {
  scroll-behavior: smooth;
}

/* Hide scrollbar but keep functionality */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* Custom scrollbar */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}
</style>
