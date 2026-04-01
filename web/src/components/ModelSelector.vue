<template>
  <el-dialog
    v-model="visible"
    title="选择模型"
    width="640px"
    :close-on-click-modal="true"
    :fullscreen="isMobile"
    class="model-selector-dialog"
    @close="$emit('close')"
  >
    <!-- 头部信息 -->
    <template #header>
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
        <el-button
          @click="loadModels"
          :loading="loading"
          circle
          class="!border-border-dark !bg-white hover:!border-primary/30"
        >
          <span class="material-symbols-outlined !text-lg">refresh</span>
        </el-button>
      </div>
    </template>

    <!-- 分类标签 -->
    <el-tabs v-model="activeTypeTab" class="mb-4">
      <el-tab-pane
        v-for="tab in typeTabs"
        :key="tab.value"
        :label="tab.label + ` (${getTabCount(tab.value)})`"
        :name="tab.value"
      />
    </el-tabs>

    <!-- 模型列表 -->
    <div class="model-list overflow-y-auto pr-1 custom-scrollbar" :class="isMobile ? 'max-h-[calc(100vh-280px)]' : 'max-h-[50vh]'">
      <!-- 加载中 -->
      <div v-if="loading" class="flex min-h-[360px] flex-col items-center justify-center text-center text-ink-500">
        <span class="material-symbols-outlined !text-4xl animate-spin text-primary">refresh</span>
        <p class="mt-3 text-sm">加载模型列表中...</p>
      </div>

      <!-- 无结果 -->
      <div
        v-else-if="filteredModels.length === 0"
        class="flex min-h-[360px] flex-col items-center justify-center text-center text-ink-500"
      >
        <span class="material-symbols-outlined !text-4xl text-ink-300">search_off</span>
        <p class="mt-3 text-sm">没有找到匹配的模型</p>
      </div>

      <!-- 模型卡片列表 -->
      <div v-else class="grid grid-cols-1 gap-3">
        <div
          v-for="model in filteredModels"
          :key="model.model_name"
          tabindex="0"
          role="button"
          @click="selectModel(model)"
          @keydown.enter.prevent="selectModel(model)"
          @keydown.space.prevent="selectModel(model)"
          :class="[
            'group rounded-[1rem] border p-4 transition-all focus:outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer',
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
                  <el-button
                    @click.stop="showModelDetail(model)"
                    circle
                    size="small"
                    class="!border-transparent hover:!border-primary/20 hover:!bg-primary/5"
                  >
                    <span class="material-symbols-outlined !text-lg text-ink-500 hover:!text-primary">info</span>
                  </el-button>
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

    <!-- 底部按钮 -->
    <template #footer>
      <el-button @click="$emit('close')">取消</el-button>
    </template>

    <!-- 模型详情弹窗 -->
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
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, ref, watch, onUnmounted } from 'vue'
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

const visible = ref(true)
const isMobile = ref(false)
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

// 获取分类数量
const getTabCount = (tabValue) => {
  if (tabValue === 'all') {
    return models.value.length
  } else if (tabValue === 'image') {
    return models.value.filter(m => m.model_type === '图像').length
  } else if (tabValue === 'chat') {
    return models.value.filter(m => m.model_type === '文本').length
  } else if (tabValue === 'async') {
    return models.value.filter(m => m.is_async || m.tags?.includes('异步')).length
  }
  return 0
}

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

  // 第一步：根据分类标签筛选
  if (activeTypeTab.value === 'image') {
    result = result.filter((model) => model.model_type === '图像')
  } else if (activeTypeTab.value === 'chat') {
    result = result.filter((model) => model.model_type === '文本')
  } else if (activeTypeTab.value === 'async') {
    result = result.filter((model) => model.is_async || model.tags?.includes('异步'))
  }

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
  visible.value = false
  emit('select', model)
}

const showModelDetail = (model) => {
  selectedModelDetail.value = model
}

const handleDetailSelect = (model) => {
  selectedModel.value = model.model_name
  selectedModelDetail.value = null
  visible.value = false
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

// 监听 visible 变化，关闭时触发 close 事件
watch(visible, (newVal) => {
  if (!newVal) {
    emit('close')
  }
})

// 检测移动端
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  loadModels()
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
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
