<template>
  <div class="overflow-hidden rounded-[1.25rem] border border-black/5 bg-white shadow-xl">
    <div class="border-b border-border-dark bg-background-dark/70 px-6 py-5">
      <div class="flex items-start justify-between gap-4">
        <div class="min-w-0">
          <h3 class="text-lg font-semibold text-ink-950">选择模型</h3>
          <p class="mt-1 text-xs text-ink-500">
            <span v-if="hasImageAttachment" class="font-medium text-primary-deep">
              已上传图片，仅展示支持识图的模型（{{ filteredModels.length }} 个）
            </span>
            <span v-else-if="activeTypeTab !== 'all'">
              {{ typeTabs.find(t => t.value === activeTypeTab)?.label || '当前分类' }}：{{ filteredModels.length }} 个模型
            </span>
            <span v-else>
              共 {{ models.length }} 个模型
            </span>
          </p>
        </div>

        <div class="flex items-center gap-2">
          <button
            @click="loadModels"
            :disabled="loading"
            class="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-border-dark bg-white text-ink-500 transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-ink-950 disabled:cursor-not-allowed disabled:opacity-50"
            title="刷新模型列表"
            type="button"
          >
            <span class="material-symbols-outlined !text-lg" :class="{ 'animate-spin': loading }">refresh</span>
          </button>
          <button
            @click="$emit('close')"
            class="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-border-dark bg-white text-ink-500 transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-ink-950"
            title="关闭"
            type="button"
          >
            <span class="material-symbols-outlined !text-lg">close</span>
          </button>
        </div>
      </div>

      <div class="mt-5 space-y-4">
        <div class="inline-flex flex-wrap gap-2 rounded-xl border border-border-dark bg-white/70 p-1">
          <button
            v-for="tab in typeTabs"
            :key="tab.value"
            @click="activeTypeTab = tab.value"
            :class="[
              'rounded-lg px-4 py-2 text-xs font-semibold transition-all',
              activeTypeTab === tab.value
                ? 'border border-primary/25 bg-white text-ink-950 shadow-sm ring-2 ring-primary/10'
                : 'text-ink-500 hover:bg-white hover:text-ink-950'
            ]"
            type="button"
          >
            {{ tab.label }}
            <span v-if="activeTypeTab === tab.value && filteredModels.length > 0" class="ml-1 text-primary">
              ({{ filteredModels.length }})
            </span>
          </button>
        </div>




      </div>
    </div>

    <div class="p-4 md:p-5">
      <div class="rounded-[1rem] border border-border-dark bg-background-dark/70 p-2">
        <div v-if="loading" class="flex min-h-[360px] flex-col items-center justify-center text-center text-ink-500">
          <span class="material-symbols-outlined !text-4xl animate-spin text-primary">refresh</span>
          <p class="mt-3 text-sm">加载模型列表中...</p>
        </div>

        <div
          v-else-if="filteredModels.length === 0"
          class="flex min-h-[360px] flex-col items-center justify-center text-center text-ink-500"
        >
          <span class="material-symbols-outlined !text-4xl text-ink-300">search_off</span>
          <p class="mt-3 text-sm">没有找到匹配的模型</p>
        </div>

        <div v-else class="max-h-[58vh] overflow-y-auto pr-1 custom-scrollbar">
          <div class="grid grid-cols-1 gap-3">
            <div
              v-for="model in filteredModels"
              :key="model.model_name"
              tabindex="0"
              role="button"
              @click="selectModel(model)"
              @keydown.enter.prevent="selectModel(model)"
              @keydown.space.prevent="selectModel(model)"
              :class="[
                'group rounded-[1rem] border p-4 transition-all focus:outline-none focus:ring-2 focus:ring-primary/20',
                selectedModel === model.model_name
                  ? 'border-primary/30 bg-white shadow-lg shadow-primary/10'
                  : 'border-border-dark bg-white hover:border-primary/25 hover:shadow-lg'
              ]"
            >
              <div class="flex items-start gap-3">
                <div
                  :class="[
                    'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border',
                    selectedModel === model.model_name
                      ? 'border-primary/20 bg-primary/10'
                      : 'border-border-dark bg-background-dark'
                  ]"
                >
                  <span class="material-symbols-outlined !text-xl text-primary">
                    {{ getModelIcon(model.vendor_name) }}
                  </span>
                </div>

                <div class="min-w-0 flex-1">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div class="flex flex-wrap items-center gap-2">
                        <h4 class="truncate text-sm font-semibold text-ink-950">{{ model.model_name }}</h4>
                        <span
                          v-if="model.model_type === '图像'"
                          class="rounded-md border border-primary/20 bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary-deep"
                        >
                          图像
                        </span>
                        <span
                          v-else-if="model.model_type === '文本'"
                          class="rounded-md border border-border-dark bg-background-dark px-2 py-0.5 text-[10px] font-medium text-ink-700"
                        >
                          聊天
                        </span>
                        <span
                          v-if="model.is_async"
                          class="rounded-md border border-primary/20 bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary-deep"
                        >
                          异步
                        </span>
                      </div>

                      <p class="mt-2 line-clamp-2 text-xs leading-5 text-ink-700">
                        {{ model.description || '暂无模型说明' }}
                      </p>
                    </div>

                    <div class="flex items-center gap-2 shrink-0">
                      <span
                        v-if="selectedModel === model.model_name"
                        class="material-symbols-outlined !text-lg text-primary"
                      >
                        check_circle
                      </span>
                      <button
                        @click.stop="showModelDetail(model)"
                        class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-transparent text-ink-500 transition-colors hover:border-primary/20 hover:bg-primary/5 hover:text-primary"
                        title="查看详情"
                        type="button"
                      >
                        <span class="material-symbols-outlined !text-lg">info</span>
                      </button>
                    </div>
                  </div>

                  <div class="mt-3 flex flex-wrap items-center gap-2">
                    <span class="rounded-md border border-border-dark bg-background-dark px-2 py-1 text-[10px] text-ink-700">
                      {{ model.vendor_name || '未知提供商' }}
                    </span>
                    <span class="text-[11px] text-ink-500">
                      {{ model.provider || '未标注 Provider' }}
                    </span>
                  </div>

                  <div v-if="model.tags?.length" class="mt-3 flex flex-wrap gap-1.5">
                    <span
                      v-for="tag in model.tags.slice(0, 4)"
                      :key="tag"
                      class="rounded-md bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary-deep"
                    >
                      {{ tag }}
                    </span>
                    <span
                      v-if="model.tags.length > 4"
                      class="inline-flex items-center rounded-md bg-background-dark px-2 py-0.5 text-[10px] text-ink-500"
                    >
                      +{{ model.tags.length - 4 }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="selectedModelDetail"
      class="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/10 p-4 backdrop-blur-sm"
      @click="selectedModelDetail = null"
    >
      <div class="max-h-[90vh] w-full max-w-3xl overflow-y-auto custom-scrollbar" @click.stop>
        <ModelInfoDetail
          :model="selectedModelDetail"
          @close="selectedModelDetail = null"
          @select="handleDetailSelect"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/services/api'
import ModelInfoDetail from './ModelInfoDetail.vue'

const props = defineProps({
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

const models = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedTags = ref(new Set())
const selectedModel = ref(props.currentModel)
const selectedModelDetail = ref(null)
const activeTypeTab = ref('all')

const typeTabs = [
  { label: '全部', value: 'all' },
  { label: '图像模型', value: 'image' },
  { label: '聊天模型', value: 'chat' },
  { label: '异步模型', value: 'async' }
]

const hasImageAttachment = computed(() => {
  return props.attachments.some((file) => {
    const type = file.type || ''
    return type.startsWith('image/')
  })
})

const popularTags = computed(() => {
  const counts = new Map()

  for (const model of models.value) {
    for (const tag of model.tags || []) {
      if (!tag) continue
      counts.set(tag, (counts.get(tag) || 0) + 1)
    }
  }

  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([tag]) => tag)
})

const filteredModels = computed(() => {
  let result = [...models.value]

  // 第一步：根据分类标签筛选（严格互斥筛选，选中某个分类后只显示该分类的模型）
  if (activeTypeTab.value === 'image') {
    // 只显示图像模型，严格过滤掉所有非图像模型
    result = result.filter((model) => model.model_type === '图像')
  } else if (activeTypeTab.value === 'chat') {
    // 只显示聊天模型（文本模型），严格过滤掉所有非文本模型
    result = result.filter((model) => model.model_type === '文本')
  } else if (activeTypeTab.value === 'async') {
    // 只显示异步模型，严格过滤掉所有非异步模型
    result = result.filter((model) => model.is_async || model.tags?.includes('异步'))
  }
  // activeTypeTab.value === 'all' 时显示所有模型，不进行分类筛选

  // 第二步：如果有图片附件，进一步筛选支持识图的模型
  if (hasImageAttachment.value) {
    result = result.filter((model) => {
      return model.tags && model.tags.includes('识图')
    })
  }

  // 第三步：根据选中的标签筛选
  if (selectedTags.value.size > 0) {
    result = result.filter((model) => {
      return model.tags && model.tags.some((tag) => selectedTags.value.has(tag))
    })
  }

  // 第四步：根据搜索关键词筛选
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter((model) => {
      return (
        model.model_name?.toLowerCase().includes(query) ||
        model.description?.toLowerCase().includes(query) ||
        model.vendor_name?.toLowerCase().includes(query) ||
        model.provider?.toLowerCase().includes(query) ||
        model.tags?.some((tag) => tag.toLowerCase().includes(query))
      )
    })
  }

  // 最终验证：确保结果中不包含其他分类的模型（开发调试用）
  if (activeTypeTab.value === 'image') {
    const hasNonImage = result.some(m => m.model_type !== '图像')
    if (hasNonImage) {
      console.warn('[ModelSelector] 警告：图像分类中包含非图像模型', result.filter(m => m.model_type !== '图像'))
    }
  } else if (activeTypeTab.value === 'chat') {
    const hasNonChat = result.some(m => m.model_type !== '文本')
    if (hasNonChat) {
      console.warn('[ModelSelector] 警告：聊天分类中包含非聊天模型', result.filter(m => m.model_type !== '文本'))
    }
  }

  return result
})

const loadModels = async () => {
  loading.value = true

  try {
    const response = await api.getModels()
    if (response?.models) {
      models.value = response.models
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
  } finally {
    loading.value = false
  }
}

const selectModel = (model) => {
  selectedModel.value = model.model_name
  emit('select', model)
}

const showModelDetail = (model) => {
  selectedModelDetail.value = model
}

const handleDetailSelect = (model) => {
  selectedModel.value = model.model_name
  selectedModelDetail.value = null
  emit('select', model)
}

const toggleTag = (tag) => {
  const nextTags = new Set(selectedTags.value)

  if (nextTags.has(tag)) {
    nextTags.delete(tag)
  } else {
    nextTags.add(tag)
  }

  selectedTags.value = nextTags
}

const getModelIcon = (vendorName) => {
  const icons = {
    Google: 'smart_toy',
    OpenAI: 'auto_awesome',
    'Doubao (豆包)': 'psychology',
    Tencent: 'language',
    Ideogram: 'image',
    'Stable Diffusion': 'gradient',
    Midjourney: 'palette',
    Anthropic: 'chat',
    Claude: 'chat',
    Gemini: 'smart_toy'
  }

  return icons[vendorName] || 'deployed_code'
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #d1d8d3;
  border-radius: 999px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #b7c0ba;
}
</style>
