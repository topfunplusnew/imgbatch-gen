<template>
  <div class="flex flex-col h-full">
    <!-- 固定头部 -->
    <div class="flex items-center justify-between px-2.5 xs:px-3 sm:px-4 md:px-5 lg:px-6 py-2 xs:py-2.5 sm:py-3 md:py-3.5 border-b border-border-dark shrink-0">
      <h3 class="text-xs xs:text-sm sm:text-base md:text-lg lg:text-xl font-bold text-ink-950">模板库</h3>
      <button @click="appStore.closeTemplateDrawer()" class="text-ink-500 hover:text-ink-950 active:text-primary transition-colors p-1 xs:p-1.5 sm:p-2 rounded hover:bg-gray-100 active:bg-gray-200 min-w-[32px] xs:min-w-[36px] sm:min-w-[40px] min-h-[32px] xs:min-h-[36px] sm:min-h-[40px] flex items-center justify-center">
        <span class="material-symbols-outlined !text-xl">close</span>
      </button>
    </div>

    <!-- Category Filter -->
    <div class="shrink-0 px-2.5 xs:px-3 sm:px-4 md:px-5 lg:px-6 py-1.5 xs:py-2 sm:py-3 md:py-3.5 border-b border-border-dark">
      <div class="relative flex items-center gap-0.5 xs:gap-1 sm:gap-1.5 md:gap-2">
        <!-- Left arrow button -->
        <button
          v-if="canScrollLeft"
          @click="scrollCategories('left')"
          class="flex-shrink-0 w-6 h-6 xs:w-7 xs:h-7 sm:w-8 sm:h-8 bg-white shadow-sm rounded flex items-center justify-center text-gray-500 hover:text-primary hover:shadow active:scale-95 transition-all text-xs"
        >
          <span class="material-symbols-outlined !text-sm">chevron_left</span>
        </button>

        <!-- Scrollable category container -->
        <div
          ref="categoryScrollRef"
          class="flex items-center gap-0.5 xs:gap-1 sm:gap-1.5 md:gap-2 overflow-x-auto overflow-y-hidden pb-1 scrollbar-hide scroll-smooth flex-1"
          @scroll="updateScrollState"
        >
          <button
            @click="selectCategory(null)"
            :class="[
              'px-1 xs:px-1.5 sm:px-2 md:px-2.5 py-0.5 xs:py-1 rounded-md text-[9px] xs:text-[10px] sm:text-xs md:text-sm font-medium whitespace-nowrap transition-colors flex-shrink-0 min-h-[28px] xs:min-h-[30px] sm:min-h-[32px] md:min-h-[36px]',
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
              'px-1 xs:px-1.5 sm:px-2 md:px-2.5 py-0.5 xs:py-1 rounded-md text-[9px] xs:text-[10px] sm:text-xs md:text-sm font-medium whitespace-nowrap transition-colors flex-shrink-0 min-h-[28px] xs:min-h-[30px] sm:min-h-[32px] md:min-h-[36px]',
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
          class="flex-shrink-0 w-6 h-6 xs:w-7 xs:h-7 sm:w-8 sm:h-8 bg-white shadow-sm rounded flex items-center justify-center text-gray-500 hover:text-primary hover:shadow active:scale-95 transition-all text-xs"
        >
          <span class="material-symbols-outlined !text-sm">chevron_right</span>
        </button>
      </div>
    </div>

    <!-- Template Grid -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-2 xs:p-2.5 sm:p-3.5 md:p-4 lg:p-5">
      <!-- Loading state -->
      <div v-if="loading && displayCases.length === 0" class="flex items-center justify-center py-6 xs:py-7 sm:py-8">
        <div class="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>

      <!-- Empty state -->
      <div v-else-if="displayCases.length === 0 && !loading" class="text-center py-8 xs:py-10 sm:py-12">
        <span class="material-symbols-outlined text-3xl xs:text-4xl text-gray-300 mb-1.5 xs:mb-2">search_off</span>
        <p class="text-xs xs:text-sm text-gray-500">暂无模板</p>
      </div>

      <!-- Template cards grid -->
      <div v-else class="space-y-1.5 xs:space-y-2 sm:space-y-2.5 md:space-y-3 lg:space-y-3.5">
        <TemplateCard
          v-for="caseItem in displayCases"
          :key="caseItem.id"
          :case-data="caseItem"
        />
      </div>

      <!-- Load more indicator -->
      <div v-if="loading && displayCases.length > 0" class="flex items-center justify-center py-3 xs:py-4">
        <div class="w-5 h-5 xs:w-6 xs:h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>

      <!-- No more -->
      <div v-else-if="!hasMore && displayCases.length > 0" class="text-center py-3 xs:py-4">
        <p class="text-[10px] xs:text-xs text-gray-400">已加载全部模板</p>
      </div>

      <!-- Load more button -->
      <div v-else-if="hasMore && displayCases.length > 0" class="text-center py-2 xs:py-3">
        <button
          @click="loadMore"
          class="px-3 xs:px-4 py-1 xs:py-1.5 text-[10px] xs:text-xs font-medium text-primary hover:bg-primary/5 rounded-lg transition-colors"
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
