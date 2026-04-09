<template>
  <Teleport to="body">
    <!-- Backdrop for mobile -->
    <div
      v-if="visible"
      class="fixed inset-0 z-[100] md:hidden"
      @click="$emit('close')"
    ></div>

    <!-- Backdrop for desktop (transparent, catches clicks outside popup) -->
    <div
      v-if="visible && isDesktop()"
      class="fixed inset-0 z-[150]"
      @click="$emit('close')"
    ></div>

    <!-- Popup container -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-if="visible"
        ref="popupRef"
        class="fixed rounded-t-2xl md:rounded-[16px] bg-white shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-gray-200/50 overflow-hidden z-[200]"
        :class="isDesktop() ? '' : 'bottom-0 left-0 right-0'"
        :style="popupStyle"
        @click.stop
      >
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined !text-lg text-primary">auto_awesome</span>
          <span class="text-sm font-medium text-gray-900">选择模型</span>
        </div>
        <button
          @click="$emit('close')"
          class="p-1 hover:bg-gray-100 rounded-lg transition-colors md:hidden"
        >
          <span class="material-symbols-outlined !text-lg text-gray-500">close</span>
        </button>
      </div>

      <!-- Category tabs -->
      <div class="flex items-center gap-1 px-3 py-2 border-b border-gray-100 overflow-x-auto">
        <button
          v-for="tab in categoryTabs"
          :key="tab.value"
          @click="activeCategory = tab.value"
          :class="[
            'px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all',
            activeCategory === tab.value
              ? 'bg-primary text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          ]"
        >
          {{ tab.label }}
          <span
            v-if="getCategoryCount(tab.value) > 0"
            :class="activeCategory === tab.value ? 'text-white/80' : 'text-gray-400'"
            class="ml-1"
          >({{ getCategoryCount(tab.value) }})</span>
        </button>
      </div>

      <!-- Search bar -->
      <div class="px-3 py-2">
        <div class="relative">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 !text-base text-gray-400">search</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索模型..."
            class="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/30"
          />
        </div>
      </div>

      <!-- Model list -->
      <div class="max-h-[320px] md:max-h-[280px] overflow-y-auto custom-scrollbar">
        <!-- Loading state -->
        <div v-if="loading" class="flex flex-col items-center justify-center py-8 text-gray-500">
          <span class="material-symbols-outlined !text-2xl animate-spin text-primary">refresh</span>
          <p class="mt-2 text-xs">加载中...</p>
        </div>

        <!-- Empty state - no models available -->
        <el-empty v-else-if="models.length === 0" description="暂无可用模型" :image-size="60" />

        <!-- Empty state - search/filter no results -->
        <el-empty v-else-if="filteredModels.length === 0" description="未找到匹配的模型" :image-size="60" />

        <!-- Model groups -->
        <div v-else class="py-1">
          <template v-for="group in modelGroups" :key="group.type">
            <!-- Group header -->
            <div
              v-if="group.models.length > 0"
              class="px-4 py-1.5 text-[11px] font-medium text-gray-400 uppercase tracking-wide"
            >
              {{ group.label }}
            </div>

            <!-- Model items -->
            <button
              type="button"
              v-for="model in group.models"
              :key="model.model_name"
              :data-model="model.model_name"
              @click.stop="selectModel(model)"
              :class="[
                'w-full flex items-center gap-2.5 px-4 py-2.5 text-left transition-colors',
                currentModel === model.model_name
                  ? 'bg-primary/5'
                  : 'hover:bg-gray-50'
              ]"
            >
              <!-- Model icon -->
              <div
                :class="[
                  'w-7 h-7 rounded-lg flex items-center justify-center shrink-0',
                  currentModel === model.model_name
                    ? 'bg-primary/10'
                    : 'bg-gray-100'
                ]"
              >
                <span
                  :class="[
                    'material-symbols-outlined !text-sm',
                    currentModel === model.model_name
                      ? 'text-primary'
                      : 'text-gray-500'
                  ]"
                >
                  {{ getModelIcon(model.vendor_name, model.model_type) }}
                </span>
              </div>

              <!-- Model info -->
              <div class="flex-1 min-w-0 overflow-hidden mr-2">
                <div class="flex items-center gap-1.5 min-w-0 overflow-hidden">
                  <span
                    :class="[
                      'text-sm font-medium overflow-hidden text-ellipsis whitespace-nowrap flex-1 min-w-0 block',
                      currentModel === model.model_name
                        ? 'text-primary'
                        : 'text-gray-900'
                    ]"
                    :title="model.display_name || model.model_name"
                  >
                    {{ model.display_name || model.model_name }}
                  </span>
                  <!-- NEW badge -->
                  <span
                    v-if="model.is_new"
                    class="px-1.5 py-0.5 text-[10px] font-medium bg-gradient-to-r from-[#4649F6] to-[#AF46F6] text-white rounded shrink-0"
                  >
                    NEW
                  </span>
                </div>
                <p class="text-[11px] text-gray-500 overflow-hidden text-ellipsis whitespace-nowrap">
                  {{ model.vendor_name || model.provider || '' }}
                </p>
              </div>

              <!-- Check icon for selected model -->
              <span
                v-if="currentModel === model.model_name"
                class="material-symbols-outlined !text-base text-primary shrink-0"
              >
                check
              </span>
            </button>
          </template>
        </div>
      </div>
    </div>
  </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { api } from '@/services/api'
import { filterSelectableFrontendModels } from '@/utils/modelSelection'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  currentModel: {
    type: String,
    default: ''
  },
  attachments: {
    type: Array,
    default: () => []
  },
  triggerElement: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['select', 'close'])

const loading = ref(false)
const models = ref([])
const searchQuery = ref('')
const activeCategory = ref('image') // 默认选中生图分类
const popupRef = ref(null)
const popupStyle = ref({})

// 是否为桌面端
const isDesktop = () => window.innerWidth >= 768

// 计算弹窗位置（桌面端）
const updatePopupPosition = () => {
  // 移动端不计算位置，使用默认的 bottom-0
  if (!isDesktop()) {
    popupStyle.value = {}
    return
  }

  // 桌面端如果没有 triggerElement，使用默认位置（向上弹出）
  if (!props.triggerElement) {
    popupStyle.value = {
      position: 'fixed',
      top: 'auto',
      bottom: '140px', // 上移更多，避免被遮挡
      left: '50%',
      transform: 'translateX(-50%)',
      width: '320px',
      maxWidth: 'calc(100vw - 32px)'
    }
    return
  }

  const triggerRect = props.triggerElement.getBoundingClientRect()
  const popupWidth = triggerRect.width // 与按钮等宽

  // 确保不超出左边界
  let left = triggerRect.left
  if (left < 16) {
    left = 16
  }

  // 确保不超出右边界
  if (left + popupWidth > window.innerWidth - 16) {
    left = window.innerWidth - popupWidth - 16
  }

  // 使用 bottom 定位，弹窗底部紧贴按钮顶部，无需估计高度
  popupStyle.value = {
    position: 'fixed',
    top: 'auto',
    bottom: `${window.innerHeight - triggerRect.top}px`,  // 弹窗底部 = 按钮顶部
    left: `${left}px`,
    width: `${popupWidth}px`,
    maxWidth: 'calc(100vw - 32px)',
    minWidth: '280px', // 最小宽度，确保内容可读
    right: 'auto'
  }
}

const categoryTabs = [
  { label: '思考', value: 'reasoning', icon: 'psychology' },
  { label: '对话', value: 'chat', icon: 'chat' },
  { label: '生图', value: 'image', icon: 'image' },
  { label: '异步', value: 'async', icon: 'sync' }
]

// 分类类型配置
const typeConfig = {
  'reasoning': { label: '思考', icon: 'psychology', color: 'text-purple-600' },
  'chat': { label: '对话', icon: 'chat', color: 'text-blue-600' },
  'image': { label: '生图', icon: 'image', color: 'text-green-600' },
  'async': { label: '异步', icon: 'sync', color: 'text-orange-600' }
}

// 根据模型属性判断分类
const getModelCategories = (model) => {
  const categories = []
  const modelType = model.model_type || ''
  const tags = model.tags || []

  let tagList = []
  if (Array.isArray(tags)) {
    tagList = tags
  } else if (typeof tags === 'string') {
    tagList = tags.split(',').map(t => t.trim())
  }
  const tagSet = new Set(tagList)

  // Reasoning models
  if (tagSet.has('reasoning') || tagSet.has('思考') || tagSet.has('推理') ||
      modelType.includes('reasoning') || modelType.includes('o1') ||
      model.model_name?.toLowerCase().includes('o1')) {
    categories.push('reasoning')
  }

  // Image models
  if (modelType === '图像' || modelType.includes('image') ||
      tagSet.has('image') || tagSet.has('生图') || tagSet.has('图像') ||
      tagSet.has('绘图') || tagSet.has('drawing') || tagSet.has('绘画')) {
    categories.push('image')
  }

  // Async models
  if (tagSet.has('异步') || model.is_async === true) {
    categories.push('async')
  }

  // Chat models (default for text models)
  if (modelType === '文本' || modelType.includes('text') ||
      modelType.includes('chat') || tagSet.has('chat') ||
      tagSet.has('对话') || model.model_name?.toLowerCase().includes('gpt') ||
      model.model_name?.toLowerCase().includes('claude')) {
    categories.push('chat')
  }

  // If no category matched, default to chat
  if (categories.length === 0) {
    categories.push('chat')
  }

  return categories
}

// Check if has image attachment
const hasImageAttachment = computed(() => {
  return props.attachments.some((file) => {
    const type = file.type || ''
    return type.startsWith('image/')
  })
})

// Filter models by category and search
const filteredModels = computed(() => {
  let result = [...models.value]

  // Filter by category using getModelCategories
  if (activeCategory.value !== 'all') {
    result = result.filter(m => {
      const categories = getModelCategories(m)
      return categories.includes(activeCategory.value)
    })
  }

  // Filter by image attachment support
  if (hasImageAttachment.value) {
    result = result.filter(m => m.tags?.includes('识图'))
  }

  // Filter by search query
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(m =>
      m.model_name?.toLowerCase().includes(query) ||
      m.display_name?.toLowerCase().includes(query) ||
      m.description?.toLowerCase().includes(query) ||
      m.vendor_name?.toLowerCase().includes(query)
    )
  }

  return result
})

// Group models by type for display
const modelGroups = computed(() => {
  const groups = {
    reasoning: [],
    chat: [],
    image: [],
    async: []
  }

  const addedModels = new Set()

  filteredModels.value.forEach(model => {
    const categories = getModelCategories(model)

    // 如果选中了某个分类，只把模型添加到该分类的分组中
    if (activeCategory.value !== 'all') {
      const cat = activeCategory.value
      if (groups[cat]) {
        const modelKey = `${cat}-${model.model_name}`
        if (!addedModels.has(modelKey)) {
          groups[cat].push(model)
          addedModels.add(modelKey)
        }
      }
    } else {
      // 如果没有选中分类，把模型添加到所有它的分类中
      categories.forEach(cat => {
        if (groups[cat]) {
          const modelKey = `${cat}-${model.model_name}`
          if (!addedModels.has(modelKey)) {
            groups[cat].push(model)
            addedModels.add(modelKey)
          }
        }
      })
    }
  })

  // 按顺序返回非空分组
  const typeOrder = ['reasoning', 'chat', 'image', 'async']
  return typeOrder
    .filter(key => groups[key].length > 0)
    .map(key => ({
      type: key,
      label: typeConfig[key].label,
      models: groups[key]
    }))
})

// Get count for each category
const getCategoryCount = (categoryValue) => {
  const countedModels = new Set()

  const count = models.value.filter(model => {
    const categories = getModelCategories(model)
    if (categories.includes(categoryValue)) {
      const modelKey = `${categoryValue}-${model.model_name}`
      if (!countedModels.has(modelKey)) {
        countedModels.add(modelKey)
        return true
      }
    }
    return false
  }).length

  return count
}

// Get model icon based on vendor or type
const getModelIcon = (vendorName, modelType) => {
  const icons = {
    'Google': 'smart_toy',
    'OpenAI': 'auto_awesome',
    'Doubao (豆包)': 'psychology',
    'Tencent': 'language',
    'Ideogram': 'image',
    'Stable Diffusion': 'gradient',
    'Midjourney': 'palette',
    'Anthropic': 'chat',
    'Claude': 'chat',
    'Gemini': 'smart_toy'
  }

  if (icons[vendorName]) return icons[vendorName]

  // Fallback based on model type
  if (modelType === '图像') return 'image'
  if (modelType === '文本') return 'chat'
  return 'deployed_code'
}

// Load models from API
const loadModels = async () => {
  loading.value = true
  try {
    const response = await api.getModels()
    if (response?.models) {
      models.value = filterSelectableFrontendModels(response.models)
    }
  } catch (error) {
    console.error('Failed to load models:', error)
  } finally {
    loading.value = false
  }
}

// Select a model
const selectModel = (model) => {
  emit('select', model)
  emit('close')
}

// Load models when component is mounted
onMounted(() => {
  loadModels()
})

// Scroll to current model when popup opens
const scrollToCurrentModel = () => {
  if (!props.currentModel) return

  nextTick(() => {
    const listContainer = popupRef.value?.querySelector('.max-h-\\[320px\\]')
    if (!listContainer) return

    const currentModelElement = listContainer.querySelector(`[data-model="${props.currentModel}"]`)
    if (currentModelElement) {
      currentModelElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

// Reset search when popup closes and update position when opens
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    searchQuery.value = ''
  } else {
    // 弹窗打开时更新位置并滚动到当前模型
    nextTick(() => {
      updatePopupPosition()
      scrollToCurrentModel()
    })
  }
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
  background: #e5e7eb;
  border-radius: 999px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #d1d5db;
}
</style>
