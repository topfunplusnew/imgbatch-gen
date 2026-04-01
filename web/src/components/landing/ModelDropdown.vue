<template>
  <div class="relative">
    <el-button round class="landing-select-trigger" @click="togglePanel" :title="currentModelLabel">
      <span class="material-symbols-outlined !text-lg text-primary shrink-0">auto_awesome</span>
      <span class="hidden max-w-[180px] truncate text-sm font-medium xs:inline">{{ currentModelLabel }}</span>
    </el-button>

    <el-dialog
      v-model="isOpen"
      align-center
      append-to-body
      class="landing-model-dialog"
      width="min(720px, calc(100vw - 32px))"
    >
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <div>
            <h3 class="text-lg font-semibold text-ink-950">选择模型</h3>
            <p class="mt-1 text-sm text-ink-500">按分类筛选后再选择更快。</p>
          </div>
        </div>
      </template>

      <div class="space-y-4">
        <div class="flex flex-wrap items-center gap-2">
          <el-button
            :type="selectedCategory === null ? 'primary' : 'default'"
            :plain="selectedCategory !== null"
            @click="selectedCategory = null"
          >
            全部 ({{ generatorStore.availableModels.length }})
          </el-button>
          <el-button
            v-for="(config, key) in typeConfig"
            :key="key"
            :type="selectedCategory === key ? 'primary' : 'default'"
            :plain="selectedCategory !== key"
            @click="selectedCategory = selectedCategory === key ? null : key"
          >
            <span class="material-symbols-outlined !text-sm">{{ config.icon }}</span>
            <span>{{ config.label }} ({{ categoryCounts[key] || 0 }})</span>
          </el-button>
        </div>

        <el-input v-model="searchQuery" placeholder="搜索模型名称...">
          <template #prefix>
            <span class="material-symbols-outlined !text-base text-ink-400">search</span>
          </template>
        </el-input>

        <el-scrollbar max-height="500px" class="pr-2">
          <div v-if="Object.keys(groupedModels).length === 0" class="px-4 py-12 text-center">
            <el-empty description="未找到匹配的模型" :image-size="64" />
          </div>

          <div
            v-for="(models, type) in groupedModels"
            :key="type"
            class="mb-4 overflow-hidden rounded-3xl border border-border-dark bg-white"
          >
            <div class="flex items-center gap-2 border-b border-border-dark bg-[rgba(140,42,46,0.04)] px-4 py-3">
              <span class="material-symbols-outlined !text-lg" :class="getTypeIconColor(type)">{{ getTypeIcon(type) }}</span>
              <span class="text-sm font-semibold text-ink-950">{{ getTypeLabel(type) }}</span>
              <el-tag round effect="plain">{{ models.length }}</el-tag>
            </div>

            <div class="space-y-2 p-3">
              <el-card
                v-for="model in models"
                :key="model.model_name"
                shadow="hover"
                class="landing-model-option cursor-pointer"
                :class="{ 'landing-model-option--active': model.model_name === generatorStore.model }"
                @click="selectModel(model)"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="flex min-w-0 items-center gap-3">
                    <div class="grid h-11 w-11 place-items-center rounded-2xl bg-primary-soft text-primary">
                      <span class="material-symbols-outlined !text-xl">smart_toy</span>
                    </div>
                    <div class="min-w-0">
                      <div class="truncate text-sm font-semibold text-ink-950">
                        {{ model.display_name || model.model_name }}
                      </div>
                      <div class="mt-1 truncate text-xs text-ink-500">{{ model.model_name }}</div>
                    </div>
                  </div>
                  <div class="flex shrink-0 items-center gap-2">
                    <el-tag effect="plain" round>{{ getProviderLabel(model.provider) }}</el-tag>
                    <span
                      v-if="model.model_name === generatorStore.model"
                      class="material-symbols-outlined !text-xl text-primary"
                    >
                      check_circle
                    </span>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-scrollbar>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const generatorStore = useGeneratorStore()
const isOpen = ref(false)
const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)

const providerLabels: Record<string, string> = {
  openai: 'OpenAI',
  midjourney: 'Midjourney',
  ideogram: 'Ideogram',
  replicate: 'Replicate',
  'fal-ai': 'Fal.ai',
  gemini: 'Gemini',
  stability: 'Stability',
  unknown: '其他'
}

const getProviderLabel = (provider?: string): string => {
  if (!provider) return '其他'
  return providerLabels[provider] || provider.charAt(0).toUpperCase() + provider.slice(1)
}

const typeConfig: Record<string, { label: string; icon: string; color: string }> = {
  reasoning: { label: '思考', icon: 'psychology', color: 'text-purple-600' },
  chat: { label: '对话', icon: 'chat', color: 'text-blue-600' },
  image: { label: '生图', icon: 'image', color: 'text-green-600' },
  async: { label: '异步', icon: 'sync', color: 'text-orange-600' }
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
  const currentModel = generatorStore.availableModels.find((m) => m.model_name === generatorStore.model)
  return currentModel?.display_name || currentModel?.model_name || generatorStore.model || '选择模型'
})

const getModelCategories = (model: any): string[] => {
  const categories: string[] = []
  const modelType = model.model_type || ''
  const tags = model.tags || []

  let tagList: string[] = []
  if (Array.isArray(tags)) {
    tagList = tags
  } else if (typeof tags === 'string') {
    tagList = tags.split(',').map((t) => t.trim())
  }

  const tagSet = new Set(tagList)

  if (
    tagSet.has('reasoning') ||
    tagSet.has('思考') ||
    tagSet.has('推理') ||
    modelType.includes('reasoning') ||
    modelType.includes('o1') ||
    model.model_name?.toLowerCase().includes('o1')
  ) {
    categories.push('reasoning')
  }

  if (
    modelType === '图像' ||
    modelType.includes('image') ||
    tagSet.has('image') ||
    tagSet.has('生图') ||
    tagSet.has('图像') ||
    tagSet.has('绘图') ||
    tagSet.has('drawing') ||
    tagSet.has('绘画')
  ) {
    categories.push('image')
  }

  if (tagSet.has('异步') || model.is_async === true) {
    categories.push('async')
  }

  if (
    modelType === '文本' ||
    modelType.includes('text') ||
    modelType.includes('chat') ||
    tagSet.has('chat') ||
    tagSet.has('对话') ||
    model.model_name?.toLowerCase().includes('gpt') ||
    model.model_name?.toLowerCase().includes('claude')
  ) {
    categories.push('chat')
  }

  if (categories.length === 0) {
    categories.push('chat')
  }

  return categories
}

const groupedModels = computed(() => {
  let filtered = generatorStore.availableModels.filter((model) => {
    if (!searchQuery.value.trim()) return true
    const query = searchQuery.value.toLowerCase()
    const name = (model.display_name || model.model_name).toLowerCase()
    const provider = model.provider?.toLowerCase() || ''
    return name.includes(query) || provider.includes(query)
  })

  if (selectedCategory.value) {
    filtered = filtered.filter((model) => {
      const categories = getModelCategories(model)
      return categories.includes(selectedCategory.value as string)
    })
  }

  const groups: Record<string, typeof filtered> = {
    reasoning: [],
    chat: [],
    image: [],
    async: []
  }

  const addedModels = new Set<string>()

  filtered.forEach((model) => {
    const categories = getModelCategories(model)
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
      categories.forEach((cat) => {
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

  const result: Record<string, typeof filtered> = {}
  const typeOrder = ['reasoning', 'chat', 'image', 'async']
  typeOrder.forEach((key) => {
    if (groups[key].length > 0) {
      result[key] = groups[key]
    }
  })

  return result
})

const categoryCounts = computed(() => {
  const counts: Record<string, number> = {
    reasoning: 0,
    chat: 0,
    image: 0,
    async: 0
  }

  const countedModels = new Set<string>()

  generatorStore.availableModels.forEach((model) => {
    const categories = getModelCategories(model)
    categories.forEach((cat) => {
      const modelKey = `${cat}-${model.model_name}`
      if (counts[cat] !== undefined && !countedModels.has(modelKey)) {
        counts[cat]++
        countedModels.add(modelKey)
      }
    })
  })

  return counts
})

const togglePanel = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value && selectedCategory.value === null) {
    selectedCategory.value = 'image'
  }
}

const selectModel = (model: any) => {
  generatorStore.model = model.model_name
  generatorStore.setSelectedModelInfo(model)
  isOpen.value = false
}

onMounted(() => {
  if (generatorStore.availableModels.length === 0) {
    generatorStore.fetchAvailableModels()
  }
})
</script>

<style scoped>
.landing-select-trigger {
  border-radius: 999px;
}

.landing-model-option {
  border-radius: 20px;
  border-color: var(--color-border-dark);
}

.landing-model-option--active {
  border-color: rgba(140, 42, 46, 0.3);
  background: rgba(140, 42, 46, 0.06);
}

.landing-model-option :deep(.el-card__body) {
  padding: 14px 16px;
}
</style>
