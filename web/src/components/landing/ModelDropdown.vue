<template>
  <div class="relative" ref="dropdownRef">
    <button
      @click="togglePanel"
      class="flex items-center gap-1.5 px-2 py-2 xs:px-2.5 bg-white border border-border-dark rounded-lg hover:border-primary/50 transition-colors shrink-0 max-w-[120px] xs:max-w-[180px]"
      :title="currentModelLabel">
      <span class="material-symbols-outlined !text-lg text-accent-purple shrink-0">auto_awesome</span>
      <span class="text-xs xs:text-sm font-medium text-gray-800 truncate hidden xs:inline">{{ currentModelLabel }}</span>
    </button>

    <!-- Floating Panel -->
    <Teleport to="body">
      <Transition name="panel">
        <div
          v-if="isOpen"
          class="fixed inset-0 z-50 flex items-center justify-center">
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black/20 backdrop-blur-sm" @click="isOpen = false"></div>

          <!-- Panel -->
          <div
            ref="panelRef"
            class="relative w-[560px] max-w-[calc(100vw-32px)] bg-white border border-border-dark rounded-xl shadow-2xl overflow-hidden"
            @click.stop>
          <!-- Header with Search and Filter -->
          <div class="p-4 border-b border-border-dark bg-gradient-to-r from-primary/5 to-primary/10">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-bold text-ink-950">选择模型</h3>
              <button @click="isOpen = false" class="text-ink-400 hover:text-ink-700 transition-colors">
                <span class="material-symbols-outlined !text-xl">close</span>
              </button>
            </div>

            <!-- Category Filter Tabs -->
            <div class="flex items-center gap-2 mb-3 flex-wrap">
              <button
                @click="selectedCategory = null"
                :class="[
                  'px-3 py-1.5 text-xs font-medium rounded-full transition-all',
                  selectedCategory === null
                    ? 'bg-primary text-white shadow-sm'
                    : 'bg-white text-ink-700 border border-border-dark hover:bg-gray-50'
                ]">
                全部 ({{ generatorStore.availableModels.length }})
              </button>
              <button
                v-for="(config, key) in typeConfig"
                :key="key"
                @click="selectedCategory = selectedCategory === key ? null : key"
                :class="[
                  'px-3 py-1.5 text-xs font-medium rounded-full transition-all flex items-center gap-1',
                  selectedCategory === key
                    ? 'bg-primary text-white shadow-sm'
                    : 'bg-white text-ink-700 border border-border-dark hover:bg-gray-50'
                ]">
                <span class="material-symbols-outlined !text-sm">{{ config.icon }}</span>
                {{ config.label }} ({{ categoryCounts[key] || 0 }})
              </button>
            </div>

            <div class="relative">
              <span class="material-symbols-outlined !text-lg absolute left-3 top-1/2 -translate-y-1/2 text-ink-400">search</span>
              <input
                v-model="searchQuery"
                placeholder="搜索模型名称..."
                class="w-full pl-9 pr-3 py-2 text-sm bg-white border border-border-dark rounded-lg focus:ring-1 focus:ring-primary focus:outline-none">
            </div>
          </div>

          <!-- Model List by Category -->
          <div class="max-h-[500px] overflow-y-auto custom-scrollbar">
            <!-- Group by Model Type -->
            <div
              v-for="(models, type) in groupedModels"
              :key="type"
              class="border-b border-border-dark last:border-b-0">
              <!-- Type Header -->
              <div class="px-4 py-2.5 bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined !text-lg" :class="getTypeIconColor(type)">{{ getTypeIcon(type) }}</span>
                  <span class="text-xs font-bold text-ink-700">{{ getTypeLabel(type) }}</span>
                  <span class="text-xs text-ink-500 bg-white px-2 py-0.5 rounded-full">{{ models.length }}</span>
                </div>
              </div>

              <!-- Models in this type -->
              <div class="divide-y divide-gray-100">
                <div
                  v-for="model in models"
                  :key="model.model_name"
                  @click="selectModel(model)"
                  :class="[
                    'px-4 py-3 cursor-pointer transition-colors',
                    model.model_name === generatorStore.model ? 'bg-primary/10 text-primary' : 'hover:bg-gray-50'
                  ]">
                  <div class="flex items-center justify-between gap-3">
                    <div class="flex items-center gap-3 min-w-0 flex-1">
                      <span class="material-symbols-outlined !text-xl shrink-0" :class="model.model_name === generatorStore.model ? 'text-primary' : 'text-ink-400'">smart_toy</span>
                      <div class="min-w-0 flex-1">
                        <div class="text-sm font-medium truncate">{{ model.display_name || model.model_name }}</div>
                        <div class="text-xs text-ink-500 truncate mt-0.5">{{ model.model_name }}</div>
                      </div>
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                      <span class="text-xs text-ink-500 bg-gray-100 px-2 py-0.5 rounded">{{ getProviderLabel(model.provider) }}</span>
                      <span v-if="model.model_name === generatorStore.model" class="material-symbols-outlined !text-xl text-primary">check_circle</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

              <!-- Empty State -->
            <div v-if="Object.keys(groupedModels).length === 0" class="px-4 py-12 text-center">
              <span class="material-symbols-outlined !text-5xl text-ink-300 mb-3 block">search_off</span>
              <div class="text-sm text-ink-700 font-medium">未找到匹配的模型</div>
              <div class="text-xs text-ink-500 mt-1">尝试其他关键词</div>
            </div>
          </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const generatorStore = useGeneratorStore()
const isOpen = ref(false)
const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const dropdownRef = ref(null)
const panelRef = ref(null)

// Provider label mapping
const providerLabels: Record<string, string> = {
  'openai': 'OpenAI',
  'midjourney': 'Midjourney',
  'ideogram': 'Ideogram',
  'replicate': 'Replicate',
  'fal-ai': 'Fal.ai',
  'gemini': 'Gemini',
  'stability': 'Stability',
  'unknown': '其他'
}

const getProviderLabel = (provider?: string): string => {
  if (!provider) return '其他'
  return providerLabels[provider] || provider.charAt(0).toUpperCase() + provider.slice(1)
}

// Model type label and icon mapping
const typeConfig: Record<string, { label: string, icon: string, color: string }> = {
  'reasoning': { label: '思考', icon: 'psychology', color: 'text-purple-600' },
  'chat': { label: '对话', icon: 'chat', color: 'text-blue-600' },
  'image': { label: '生图', icon: 'image', color: 'text-green-600' },
  'async': { label: '异步', icon: 'sync', color: 'text-orange-600' }
}

const getTypeLabel = (type: string): string => {
  return typeConfig[type]?.label || type.charAt(0).toUpperCase() + type.slice(1)
}

const getTypeIcon = (type: string): string => {
  return typeConfig[type]?.icon || 'smart_toy'
}

const getTypeIconColor = (type: string): string => {
  return typeConfig[type]?.color || 'text-gray-600'
}

const currentModelLabel = computed(() => {
  const currentModel = generatorStore.availableModels.find(m => m.model_name === generatorStore.model)
  return currentModel?.display_name || currentModel?.model_name || generatorStore.model || '选择模型'
})

// Group models by type (considering both model_type and tags)
const groupedModels = computed(() => {
  let filtered = generatorStore.availableModels.filter(model => {
    if (!searchQuery.value.trim()) return true
    const query = searchQuery.value.toLowerCase()
    const name = (model.display_name || model.model_name).toLowerCase()
    const provider = model.provider?.toLowerCase() || ''
    return name.includes(query) || provider.includes(query)
  })

  // If a category is selected, filter models by that category
  if (selectedCategory.value) {
    filtered = filtered.filter(model => {
      const categories = getModelCategories(model)
      return categories.includes(selectedCategory.value)
    })
  }

  const groups: Record<string, typeof filtered> = {
    reasoning: [],
    chat: [],
    image: [],
    async: []
  }

  // Use a Set to track models already added to prevent duplicates in same category
  const addedModels = new Set<string>()

  filtered.forEach(model => {
    const categories = getModelCategories(model)

    // 如果选中了某个分类，只把模型添加到该分类的分组中
    if (selectedCategory.value) {
      const cat = selectedCategory.value
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

  // Remove empty groups
  const result: Record<string, typeof filtered> = {}
  const typeOrder = ['reasoning', 'chat', 'image', 'async']

  typeOrder.forEach(key => {
    if (groups[key].length > 0) {
      result[key] = groups[key]
    }
  })

  return result
})

// Get category count for filter tabs
const categoryCounts = computed(() => {
  const counts: Record<string, number> = {
    reasoning: 0,
    chat: 0,
    image: 0,
    async: 0
  }

  // Use a Set to avoid counting the same model multiple times for the same category
  const countedModels = new Set<string>()

  generatorStore.availableModels.forEach(model => {
    const categories = getModelCategories(model)
    categories.forEach(cat => {
      const modelKey = `${cat}-${model.model_name}`
      if (counts[cat] !== undefined && !countedModels.has(modelKey)) {
        counts[cat]++
        countedModels.add(modelKey)
      }
    })
  })

  return counts
})

// Determine model categories based on model_type and tags
const getModelCategories = (model: any): string[] => {
  const categories: string[] = []
  const modelType = model.model_type || ''
  const tags = model.tags || []

  // Handle both array and string tags
  let tagList: string[] = []
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
  if (tagSet.has('异步')) {
    categories.push('async')
  }

  // Also check for async models with is_async field
  if (model.is_async === true) {
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

const togglePanel = () => {
  isOpen.value = !isOpen.value
  // 当打开面板时，默认选中"生图"分类（如果之前没有选择过分类）
  if (isOpen.value && selectedCategory.value === null) {
    selectedCategory.value = 'image'
  }
}

const selectModel = (model: any) => {
  generatorStore.model = model.model_name
  generatorStore.setSelectedModelInfo(model)
  isOpen.value = false
}

const handleClickOutside = (event: Event) => {
  // Close when clicking outside (backup, backdrop handles most cases)
  if (isOpen.value && dropdownRef.value && panelRef.value) {
    if (!dropdownRef.value.contains(event.target as Node) &&
        !panelRef.value.contains(event.target as Node)) {
      isOpen.value = false
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // Fetch models if not already loaded
  if (generatorStore.availableModels.length === 0) {
    generatorStore.fetchAvailableModels()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Panel transition */
.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.2s ease;
}
.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}
.panel-enter-to,
.panel-leave-from {
  opacity: 1;
}

/* Scale animation for the panel content */
.panel-enter-active > div > div:last-child,
.panel-leave-active > div > div:last-child {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.panel-enter-from > div > div:last-child,
.panel-leave-to > div > div:last-child {
  transform: scale(0.95);
  opacity: 0;
}
.panel-enter-to > div > div:last-child,
.panel-leave-from > div > div:last-child {
  transform: scale(1);
  opacity: 1;
}
</style>
