<template>
  <!-- Backdrop for mobile -->
  <div
    v-if="visible"
    class="fixed inset-0 z-30 md:hidden"
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
      class="fixed bottom-0 left-0 right-0 z-40 md:absolute md:bottom-[calc(100%+8px)] md:left-0 md:right-auto md:w-[340px] rounded-t-2xl md:rounded-[16px] bg-white shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-gray-200/50 overflow-hidden"
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

        <!-- Empty state -->
        <div v-else-if="filteredModels.length === 0" class="flex flex-col items-center justify-center py-8 text-gray-500">
          <span class="material-symbols-outlined !text-2xl text-gray-300">search_off</span>
          <p class="mt-2 text-xs">未找到匹配的模型</p>
        </div>

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
              v-for="model in group.models"
              :key="model.model_name"
              @click="selectModel(model)"
              :class="[
                'w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors',
                currentModel === model.model_name
                  ? 'bg-primary/5'
                  : 'hover:bg-gray-50'
              ]"
            >
              <!-- Model icon -->
              <div
                :class="[
                  'w-8 h-8 rounded-lg flex items-center justify-center shrink-0',
                  currentModel === model.model_name
                    ? 'bg-primary/10'
                    : 'bg-gray-100'
                ]"
              >
                <span
                  :class="[
                    'material-symbols-outlined !text-base',
                    currentModel === model.model_name
                      ? 'text-primary'
                      : 'text-gray-500'
                  ]"
                >
                  {{ getModelIcon(model.vendor_name, model.model_type) }}
                </span>
              </div>

              <!-- Model info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span
                    :class="[
                      'text-sm font-medium truncate',
                      currentModel === model.model_name
                        ? 'text-primary'
                        : 'text-gray-900'
                    ]"
                  >
                    {{ model.display_name || model.model_name }}
                  </span>
                  <!-- NEW badge -->
                  <span
                    v-if="model.is_new"
                    class="px-1.5 py-0.5 text-[10px] font-medium bg-gradient-to-r from-[#4649F6] to-[#AF46F6] text-white rounded"
                  >
                    NEW
                  </span>
                </div>
                <p class="text-[11px] text-gray-500 truncate">
                  {{ model.vendor_name || model.provider || '' }}
                </p>
              </div>

              <!-- Check icon for selected model -->
              <span
                v-if="currentModel === model.model_name"
                class="material-symbols-outlined !text-lg text-primary shrink-0"
              >
                check
              </span>
            </button>
          </template>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '@/services/api'

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
  }
})

const emit = defineEmits(['select', 'close'])

const loading = ref(false)
const models = ref([])
const searchQuery = ref('')
const activeCategory = ref('all')

const categoryTabs = [
  { label: '全部', value: 'all' },
  { label: '热门', value: 'hot' },
  { label: '对话', value: 'chat' },
  { label: '图片', value: 'image' },
  { label: '视频', value: 'video' }
]

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

  // Filter by category
  if (activeCategory.value === 'chat') {
    result = result.filter(m => m.model_type === '文本')
  } else if (activeCategory.value === 'image') {
    result = result.filter(m => m.model_type === '图像')
  } else if (activeCategory.value === 'video') {
    result = result.filter(m => m.model_type === '视频' || m.tags?.includes('视频'))
  } else if (activeCategory.value === 'hot') {
    // Hot models: popular providers or tagged as hot
    result = result.filter(m =>
      m.tags?.includes('热门') ||
      m.tags?.includes('推荐') ||
      ['midjourney', 'dall-e-3', 'stable-diffusion', 'gpt-4', 'claude'].some(name =>
        m.model_name?.toLowerCase().includes(name)
      )
    )
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
  const imageModels = filteredModels.value.filter(m => m.model_type === '图像')
  const chatModels = filteredModels.value.filter(m => m.model_type === '文本')
  const otherModels = filteredModels.value.filter(m => m.model_type !== '图像' && m.model_type !== '文本')

  return [
    { type: 'image', label: '图像模型', models: imageModels },
    { type: 'chat', label: '对话模型', models: chatModels },
    { type: 'other', label: '其他', models: otherModels }
  ].filter(g => g.models.length > 0)
})

// Get count for each category
const getCategoryCount = (categoryValue) => {
  if (categoryValue === 'all') {
    return models.value.length
  }

  let result = [...models.value]

  if (categoryValue === 'chat') {
    result = result.filter(m => m.model_type === '文本')
  } else if (categoryValue === 'image') {
    result = result.filter(m => m.model_type === '图像')
  } else if (categoryValue === 'video') {
    result = result.filter(m => m.model_type === '视频' || m.tags?.includes('视频'))
  } else if (categoryValue === 'hot') {
    result = result.filter(m =>
      m.tags?.includes('热门') ||
      m.tags?.includes('推荐') ||
      ['midjourney', 'dall-e-3', 'stable-diffusion', 'gpt-4', 'claude'].some(name =>
        m.model_name?.toLowerCase().includes(name)
      )
    )
  }

  if (hasImageAttachment.value) {
    result = result.filter(m => m.tags?.includes('识图'))
  }

  return result.length
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
      models.value = response.models
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

// Reset search when popup closes
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    searchQuery.value = ''
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
