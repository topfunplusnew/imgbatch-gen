<template>
  <div class="flex flex-col h-full bg-transparent">
    <!-- 标题和搜索栏 -->
    <div class="px-3 py-2.5 border-b border-border-dark space-y-2.5 shrink-0">

      <!-- 搜索框 -->
      <div class="relative">
        <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-500 !text-sm">search</span>
        <input
          v-model="searchInput"
          @input="handleSearch"
          type="text"
          placeholder="搜索案例..."
          class="w-full bg-white border border-border-dark rounded-lg pl-8 pr-2.5 py-1.5 text-xs focus:ring-1 focus:ring-primary focus:border-primary"
        >
      </div>

      <!-- 分类筛选器 -->
      <div class="relative flex items-center gap-1">
        <!-- 左箭头按钮 -->
        <button
          v-if="canScrollLeft"
          @click="scrollCategories('left')"
          class="flex-shrink-0 w-5 h-5 bg-white shadow-sm rounded flex items-center justify-center text-gray-500 hover:text-primary hover:shadow transition-all text-xs"
        >
          <span class="material-symbols-outlined !text-sm">chevron_left</span>
        </button>

        <!-- 滚动容器 -->
        <div
          ref="categoryScrollRef"
          class="flex items-center gap-1.5 overflow-x-auto overflow-y-hidden pb-1 scrollbar-hide scroll-smooth"
          @scroll="updateScrollState"
          style="max-width: calc(100% - 40px);"
        >
          <button
            @click="selectCategory(null)"
            :class="[
              'px-2 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors flex-shrink-0',
              !caseStore.selectedCategory
                ? 'bg-primary text-white'
                : 'bg-white text-ink-700 hover:bg-gray-50 border border-border-dark'
            ]"
          >
            全部
          </button>
          <button
            v-for="cat in caseStore.categories"
            :key="cat"
            @click="selectCategory(cat)"
            :class="[
              'px-2 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors flex-shrink-0',
              caseStore.selectedCategory === cat
                ? 'bg-primary text-white'
                : 'bg-white text-ink-700 hover:bg-gray-50 border border-border-dark'
            ]"
          >
            {{ cat }}
          </button>
        </div>

        <!-- 右箭头按钮 -->
        <button
          v-if="canScrollRight"
          @click="scrollCategories('right')"
          class="flex-shrink-0 w-5 h-5 bg-white shadow-sm rounded flex items-center justify-center text-gray-500 hover:text-primary hover:shadow transition-all text-xs"
        >
          <span class="material-symbols-outlined !text-sm">chevron_right</span>
        </button>
      </div>

      <!-- 结果统计 -->
      <div v-if="caseStore.searchQuery || caseStore.selectedCategory" class="flex items-center justify-between">
        <span class="text-xs text-ink-500">
          找到 {{ caseStore.filteredCases.length }} 个案例
        </span>
        <button
          @click="caseStore.resetFilters()"
          class="text-xs text-primary hover:text-primary-strong"
        >
          清除
        </button>
      </div>
    </div>

    <!-- 案例列表 -->
    <div
      ref="galleryRef"
      class="flex-1 overflow-y-auto custom-scrollbar px-2.5 py-2"
      @scroll="handleScroll"
    >
      <!-- 加载状态 -->
      <div v-if="caseStore.loading && caseStore.cases.length === 0" class="flex items-center justify-center py-12">
        <div class="flex flex-col items-center gap-3">
          <div class="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p class="text-sm text-ink-500">加载案例中...</p>
        </div>
      </div>

      <!-- 案例列表 -->
      <div v-else class="case-list">
        <CaseCard
          v-for="caseItem in displayCases"
          :key="caseItem.id"
          :case-data="caseItem"
        />

        <!-- 加载更多 -->
        <div v-if="caseStore.loading && caseStore.cases.length > 0" class="flex items-center justify-center py-6">
          <div class="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>

        <!-- 没有更多 -->
        <div v-else-if="!caseStore.hasMore && caseStore.cases.length > 0" class="text-center py-6">
          <p class="text-xs text-ink-500">没有更多案例了</p>
        </div>

        <!-- 空状态 -->
        <div v-else-if="caseStore.cases.length === 0" class="text-center py-12">
          <span class="material-symbols-outlined !text-5xl text-ink-300 mb-3 block">photo_library</span>
          <p class="text-sm text-ink-500 mb-1">暂无案例</p>
          <p class="text-xs text-ink-400">
            {{ caseStore.searchQuery || caseStore.selectedCategory ? '试试其他筛选条件' : '管理员还未添加案例' }}
          </p>
        </div>
      </div>
    </div>

    <!-- 全部工具滑动栏 -->
    <div class="model-slider-wrapper bg-white border-t border-border-dark">
      <!-- 标题和筛选 -->
      <div class="flex items-center justify-between px-2.5 py-2">
        <h3 class="text-xs font-semibold text-gray-900">全部工具</h3>

        <!-- 分类筛选按钮 -->
        <div class="flex items-center gap-1">
          <button
            @click="modelFilter = 'all'"
            :class="[
              'px-2 py-1 rounded-md text-xs font-medium transition-colors',
              modelFilter === 'all'
                ? 'bg-primary text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50 border border-border-dark'
            ]"
          >
            全部
          </button>
          <button
            @click="modelFilter = 'image'"
            :class="[
              'px-2 py-1 rounded-md text-xs font-medium transition-colors',
              modelFilter === 'image'
                ? 'bg-primary text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50 border border-border-dark'
            ]"
          >
            图像
          </button>
          <button
            @click="modelFilter = 'chat'"
            :class="[
              'px-2 py-1 rounded-md text-xs font-medium transition-colors',
              modelFilter === 'chat'
                ? 'bg-primary text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50 border border-border-dark'
            ]"
          >
            文本
          </button>
        </div>
      </div>

      <!-- 模型滑动栏 -->
      <div class="relative">
        <!-- 左箭头 -->
        <button
          v-if="canScrollModelsLeft"
          @click="scrollModels('left')"
          class="absolute left-1 top-1/2 -translate-y-1/2 z-10 w-6 h-6 bg-white shadow-md rounded-full flex items-center justify-center text-gray-500 hover:text-primary hover:shadow-lg transition-all"
        >
          <span class="material-symbols-outlined !text-sm">chevron_left</span>
        </button>

        <!-- 模型列表容器 -->
        <div
          ref="modelsSliderRef"
          class="flex gap-2 overflow-x-auto overflow-y-hidden px-2.5 py-2 scroll-smooth custom-scrollbar"
          @scroll="updateModelsScrollState"
        >
          <!-- 加载状态 -->
          <div v-if="modelsLoading" class="flex items-center gap-3 w-full justify-center py-4">
            <div class="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
            <span class="text-xs text-gray-500">加载模型中...</span>
          </div>

          <!-- 模型卡片 -->
          <div
            v-for="model in filteredModels"
            :key="model.model_name"
            @click="selectModel(model)"
            :class="[
              'model-card flex-shrink-0 w-28 rounded-lg border transition-all cursor-pointer',
              isModelSelected(model) ? 'border-primary bg-primary/5' : 'border-border-dark hover:border-primary/50 hover:shadow-md'
            ]"
          >
            <!-- 模型图标 -->
            <div class="relative w-full aspect-square overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100 rounded-t-lg">
              <div class="absolute inset-0 flex items-center justify-center">
                <span class="material-symbols-outlined !text-3xl text-gray-400">
                  {{ getModelIcon(model.vendor_name) }}
                </span>
              </div>

              <!-- 模型类型标签 -->
              <div class="absolute top-1 right-1">
                <span
                  :class="[
                    'px-1.5 py-0.5 rounded text-[10px] font-medium',
                    model.model_type === '图像'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-blue-100 text-blue-700'
                  ]"
                >
                  {{ model.model_type === '图像' ? '图像' : '文本' }}
                </span>
              </div>

              <!-- 异步标记 -->
              <div v-if="model.is_async" class="absolute top-1 left-1">
                <span class="px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded text-[10px] font-medium">
                  异步
                </span>
              </div>
            </div>

            <!-- 模型信息 -->
            <div class="p-2">
              <h4 class="text-xs font-medium text-gray-900 line-clamp-1 leading-tight mb-0.5">
                {{ model.model_name }}
              </h4>
              <p class="text-[10px] text-gray-500 line-clamp-1">
                {{ model.vendor_name }}
              </p>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="!modelsLoading && filteredModels.length === 0" class="flex items-center justify-center w-full py-8">
            <div class="text-center">
              <span class="material-symbols-outlined !text-4xl text-gray-300 mb-2 block">model_training</span>
              <p class="text-xs text-gray-500">暂无模型</p>
            </div>
          </div>
        </div>

        <!-- 右箭头 -->
        <button
          v-if="canScrollModelsRight"
          @click="scrollModels('right')"
          class="absolute right-1 top-1/2 -translate-y-1/2 z-10 w-6 h-6 bg-white shadow-md rounded-full flex items-center justify-center text-gray-500 hover:text-primary hover:shadow-lg transition-all"
        >
          <span class="material-symbols-outlined !text-sm">chevron_right</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCaseStore } from '@/store/useCaseStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useAppStore } from '@/store/useAppStore'
import CaseCard from './CaseCard.vue'

const router = useRouter()
const caseStore = useCaseStore()
const generatorStore = useGeneratorStore()
const appStore = useAppStore()
const galleryRef = ref(null)
const categoryScrollRef = ref(null)
const searchInput = ref('')

// 模型滑动栏相关
const modelsSliderRef = ref(null)
const modelsLoading = ref(true)
const models = ref([])
const modelFilter = ref('all')
const canScrollModelsLeft = ref(false)
const canScrollModelsRight = ref(false)

// 分类滚动状态
const canScrollLeft = ref(false)
const canScrollRight = ref(false)

// 更新滚动状态
const updateScrollState = () => {
  if (!categoryScrollRef.value) return

  const el = categoryScrollRef.value
  canScrollLeft.value = el.scrollLeft > 0
  canScrollRight.value = el.scrollLeft < el.scrollWidth - el.clientWidth - 1
}

// 滚动分类
const scrollCategories = (direction) => {
  if (!categoryScrollRef.value) return

  const el = categoryScrollRef.value
  const scrollAmount = 150 // 每次滚动的像素

  if (direction === 'left') {
    el.scrollBy({ left: -scrollAmount, behavior: 'smooth' })
  } else {
    el.scrollBy({ left: scrollAmount, behavior: 'smooth' })
  }
}

// 显示的案例（考虑搜索和筛选）
const displayCases = computed(() => {
  if (caseStore.searchQuery || caseStore.selectedCategory) {
    return caseStore.filteredCases
  }
  return caseStore.cases
})

// 筛选后的模型
const filteredModels = computed(() => {
  if (modelFilter.value === 'all') {
    return models.value
  }
  if (modelFilter.value === 'image') {
    return models.value.filter(m => m.model_type === '图像')
  }
  if (modelFilter.value === 'chat') {
    return models.value.filter(m => m.model_type === '文本')
  }
  return models.value
})

// 判断模型是否被选中
const isModelSelected = (model) => {
  return generatorStore.model === model.model_name ||
         (generatorStore.selectedModelInfo && generatorStore.selectedModelInfo.model_name === model.model_name)
}

// 获取模型图标
const getModelIcon = (vendorName) => {
  const iconMap = {
    'midjourney': 'brush',
    'ideogram': 'palette',
    'openai': 'smart_toy',
    'replicate': 'auto_awesome',
    'fal-ai': 'flash_on',
    'google': 'google',
    'gemini': 'diamond',
    'tencent': 'chat',
    'baidu': 'psychology',
    'aliyun': 'image',
    'kling': 'videocam',
    'doubao': 'bubble_chart'
  }

  const vendorLower = vendorName.toLowerCase()
  for (const [key, icon] of Object.entries(iconMap)) {
    if (vendorLower.includes(key)) {
      return icon
    }
  }
  return 'model_training'
}

const handleSearch = () => {
  // 使用防抖来减少API调用
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    caseStore.setSearch(searchInput.value)
  }, 300)
}

let searchTimeout = null

const selectCategory = (category) => {
  caseStore.setCategory(category)
}

// 模型滑动栏相关函数
const scrollModels = (direction) => {
  if (!modelsSliderRef.value) return

  const el = modelsSliderRef.value
  const scrollAmount = 300

  if (direction === 'left') {
    el.scrollBy({ left: -scrollAmount, behavior: 'smooth' })
  } else {
    el.scrollBy({ left: scrollAmount, behavior: 'smooth' })
  }
}

const updateModelsScrollState = () => {
  if (!modelsSliderRef.value) return

  const el = modelsSliderRef.value
  canScrollModelsLeft.value = el.scrollLeft > 0
  canScrollModelsRight.value = el.scrollLeft < el.scrollWidth - el.clientWidth - 1
}

const selectModel = (model) => {
  generatorStore.setSelectedModel(model.model_name)
  generatorStore.setSelectedModelInfo(model)

  // 切换到生成页面
  router.push('/')
}

const loadModels = async () => {
  modelsLoading.value = true
  try {
    const response = await fetch('/api/v1/models?model_type=image')
    if (!response.ok) {
      throw new Error('获取模型列表失败')
    }
    const data = await response.json()
    models.value = data.models || []
  } catch (error) {
    console.error('加载模型失败:', error)
    models.value = []
  } finally {
    modelsLoading.value = false
  }
}

const handleScroll = () => {
  if (!galleryRef.value) return

  const { scrollTop, scrollHeight, clientHeight } = galleryRef.value

  // 距离底部100px时加载更多
  if (scrollHeight - scrollTop - clientHeight < 100) {
    caseStore.loadMore()
  }
}

// 监听搜索输入，同步到store
watch(() => caseStore.searchQuery, (newVal) => {
  if (newVal !== searchInput.value) {
    searchInput.value = newVal
  }
})

// 监听分类变化，更新滚动状态
watch(() => caseStore.categories, () => {
  setTimeout(() => {
    updateScrollState()
  }, 100)
}, { deep: true })

onMounted(() => {
  caseStore.initialize()

  // 初始化滚动状态
  setTimeout(() => {
    updateScrollState()
  }, 100)
})
</script>

<style scoped>
/* 单列列表布局 - 适合侧边栏窄宽度 */
.case-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* 平滑滚动 */
.scroll-smooth {
  scroll-behavior: smooth;
}

/* 隐藏滚动条但保持滚动功能 */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* 自定义滚动条 */
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
