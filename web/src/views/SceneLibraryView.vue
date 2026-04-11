<template>
  <main class="flex h-full min-h-0 flex-1 flex-col overflow-y-auto bg-background-dark">
    <!-- Hero -->
    <div class="px-4 pt-8 pb-6 text-center xs:px-6 md:px-8 md:pt-12">
      <h1 class="text-2xl font-bold text-ink-950 md:text-3xl">
        找到你的场景，<span class="text-primary">即刻出图</span>
      </h1>
      <p class="mt-2 text-sm text-ink-500">
        每个场景都预设好了图片类型、风格和提示词，选中即用
      </p>
    </div>

    <!-- Search bar -->
    <div class="mx-auto w-full max-w-[600px] px-4 xs:px-6">
      <el-input
        v-model="searchQuery"
        size="large"
        clearable
        placeholder="搜索场景或提示词..."
        class="scene-search"
      >
        <template #prefix>
          <span class="material-symbols-outlined !text-xl text-ink-500">search</span>
        </template>
      </el-input>
    </div>

    <!-- Hot scenes -->
    <div class="mx-auto mt-6 w-full max-w-[800px] px-4 xs:px-6 md:px-8">
      <div class="mb-3 flex items-center gap-2">
        <span class="text-lg">🔥</span>
        <h3 class="text-sm font-semibold text-ink-700">热门场景</h3>
      </div>
      <div class="grid grid-cols-2 gap-2 xs:grid-cols-3 md:grid-cols-3">
        <button
          v-for="scene in hotScenes"
          :key="scene.id"
          @click="selectScene(scene)"
          class="flex items-center gap-2.5 rounded-2xl border border-border-dark bg-white/80 px-3 py-2.5 text-left transition hover:border-primary/30 hover:shadow-sm"
        >
          <span class="text-xl">{{ scene.icon }}</span>
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-medium text-ink-950">{{ scene.name }}</div>
            <div class="text-xs text-ink-500">{{ scene.templateCount }} 个模版</div>
          </div>
        </button>
      </div>
    </div>

    <!-- Category filter -->
    <div class="mx-auto mt-6 w-full max-w-[800px] px-4 xs:px-6 md:px-8">
      <div class="flex flex-wrap items-center gap-2 pb-2">
        <el-button
          :type="selectedCategory === null ? 'primary' : 'default'"
          :plain="selectedCategory !== null"
          round
          size="small"
          @click="selectedCategory = null"
        >
          <span class="material-symbols-outlined !text-sm">home</span>
          <span>全部</span>
        </el-button>
        <el-button
          v-for="cat in categories"
          :key="cat.id"
          :type="selectedCategory === cat.id ? 'primary' : 'default'"
          :plain="selectedCategory !== cat.id"
          round
          size="small"
          @click="selectedCategory = cat.id"
        >
          <span>{{ cat.icon }}</span>
          <span>{{ cat.name }}</span>
        </el-button>
      </div>
    </div>

    <!-- Scene cards grid -->
    <div class="mx-auto mt-4 w-full max-w-[800px] px-4 pb-8 xs:px-6 md:px-8">
      <!-- Loading -->
      <div v-if="loading" class="grid grid-cols-2 gap-4 xs:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        <div v-for="i in 8" :key="i" class="animate-pulse rounded-2xl bg-white/60">
          <div class="aspect-square rounded-t-2xl bg-primary-soft"></div>
          <div class="p-3 space-y-2">
            <div class="h-4 w-3/4 rounded bg-primary-soft"></div>
            <div class="h-3 w-1/2 rounded bg-primary-soft"></div>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="filteredScenes.length === 0" class="py-16 text-center text-ink-500">
        <span class="material-symbols-outlined !text-5xl text-ink-300">search_off</span>
        <p class="mt-3 text-sm">未找到匹配的场景</p>
      </div>

      <!-- Scene cards -->
      <div v-else class="grid grid-cols-2 gap-4 xs:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        <div
          v-for="scene in filteredScenes"
          :key="scene.id"
          @click="selectScene(scene)"
          class="group cursor-pointer overflow-hidden rounded-2xl border border-border-dark bg-white/90 shadow-sm hover:shadow-xl hover:-translate-y-0.5 hover:border-primary/30"
        >
          <!-- Cover image / icon -->
          <div class="aspect-[4/3] overflow-hidden bg-primary-soft/20">
            <img
              v-if="scene.coverImage"
              :src="scene.coverImage"
              :alt="scene.name"
              class="w-full h-full object-cover transition-transform group-hover:scale-105"
              loading="lazy"
            />
            <div v-else class="flex h-full items-center justify-center">
              <span class="text-5xl">{{ scene.icon }}</span>
            </div>
          </div>
          <!-- Info -->
          <div class="p-3">
            <h4 class="truncate text-sm font-semibold text-ink-950">{{ scene.name }}</h4>
            <p class="mt-1 text-xs text-ink-500 line-clamp-2">
              {{ scene.templateCount }} 个模版 · {{ scene.description }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Scene detail drawer -->
    <el-drawer
      v-model="showSceneDetail"
      direction="rtl"
      size="min(480px, 90vw)"
      :title="selectedScene?.name"
      append-to-body
    >
      <template v-if="selectedScene">
        <!-- Scene header -->
        <div class="mb-4 flex items-center gap-3">
          <div class="grid h-12 w-12 place-items-center rounded-2xl bg-primary-soft text-2xl">
            {{ selectedScene.icon }}
          </div>
          <div>
            <h3 class="text-lg font-bold text-ink-950">{{ selectedScene.name }}</h3>
            <p class="text-xs text-ink-500">{{ selectedScene.templateCount }} 个模版</p>
          </div>
        </div>
        <p class="mb-6 text-sm text-ink-700">{{ selectedScene.description }}</p>

        <!-- Templates -->
        <div class="space-y-3">
          <div
            v-for="tpl in selectedScene.templates"
            :key="tpl.id"
            class="group overflow-hidden rounded-2xl border border-border-dark bg-white/80 transition hover:shadow-md"
          >
            <div v-if="tpl.exampleImage" class="aspect-[4/3] overflow-hidden bg-primary-soft/20">
              <img :src="tpl.exampleImage" class="w-full h-full object-cover transition-transform group-hover:scale-105" />
            </div>
            <div class="p-3">
              <h5 class="text-sm font-semibold text-ink-950">{{ tpl.title }}</h5>
              <div class="mt-1.5 flex flex-wrap gap-1.5">
                <el-tag v-if="tpl.type" size="small">{{ tpl.type }}</el-tag>
                <el-tag v-if="tpl.style" size="small" type="info">{{ tpl.style }}</el-tag>
              </div>
              <el-button
                type="primary"
                size="small"
                round
                class="mt-3"
                @click="useSameStyle(tpl)"
              >
                <span class="material-symbols-outlined !text-sm">arrow_upward</span>
                做同款
              </el-button>
            </div>
          </div>
        </div>
      </template>
    </el-drawer>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { notification } from '@/utils/notification'
import { DEFAULT_IMAGE_MODEL } from '@/utils/modelSelection'

const router = useRouter()
const generatorStore = useGeneratorStore()

const searchQuery = ref('')
const selectedCategory = ref(null)
const loading = ref(true)
const showSceneDetail = ref(false)
const selectedScene = ref(null)

const categories = ref([])

const scenes = ref([])

const hotScenes = computed(() => {
  const configuredHotScenes = scenes.value.filter(scene => scene.isHot)
  if (configuredHotScenes.length > 0) {
    return configuredHotScenes.slice(0, 6)
  }

  return [...scenes.value]
    .sort((a, b) => (b.templates?.length || 0) - (a.templates?.length || 0))
    .slice(0, 6)
})

const filteredScenes = computed(() => {
  let result = scenes.value

  if (selectedCategory.value) {
    result = result.filter(s => s.category === selectedCategory.value)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(s =>
      s.name.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q) ||
      s.templates?.some(t => t.title.toLowerCase().includes(q) || t.prompt.toLowerCase().includes(q))
    )
  }

  return result
})

const selectScene = (scene) => {
  selectedScene.value = scene
  showSceneDetail.value = true
}

const buildSceneTemplatePrompt = (scene, template) => {
  const sceneName = scene?.name || '场景创作'
  const templateType = template?.type || sceneName
  const templateStyle = template?.style || ''
  const basePrompt = String(template?.prompt || '').trim()
  const promptSections = [
    `请围绕“${sceneName}”直接生成一张高完成度图片。`,
    `目标类型：${templateType}。`,
    templateStyle ? `推荐风格：${templateStyle}。` : '',
    '请确保主体明确、版式完整、关键信息有层次、不要偏题，也不要输出与主题无关的装饰内容。',
    '如果包含中文文案，请尽量让标题短、层级清晰、重点醒目。',
    basePrompt ? `核心创作要求：${basePrompt}` : '',
  ].filter(Boolean)

  return promptSections.join('\n')
}

const useSameStyle = (template) => {
  const scenePrompt = buildSceneTemplatePrompt(selectedScene.value, template)
  generatorStore.startNewConversation()
  generatorStore.prompt = scenePrompt
  if (template.style) {
    generatorStore.style = template.style
  }
  generatorStore.setBatchSize(1)
  generatorStore.setNextPreferredModel(DEFAULT_IMAGE_MODEL)
  showSceneDetail.value = false
  router.push('/')
  notification.success('已加载模版', '已补强提示词并固定推荐生图模型，可直接发送或修改后发送')
}

onMounted(async () => {
  try {
    const res = await fetch('/api/v1/admin/system-config/scenes')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const data = await res.json()
    categories.value = Array.isArray(data.categories) ? data.categories : []
    scenes.value = (Array.isArray(data.scenes) ? data.scenes : []).map(s => ({
      ...s,
      templateCount: s.templates?.length || 0,
    }))

    if (!categories.value.length && scenes.value.length > 0) {
      const categoryMap = new Map()
      scenes.value.forEach((scene) => {
        if (!scene.category || categoryMap.has(scene.category)) return
        categoryMap.set(scene.category, {
          id: scene.category,
          name: scene.category,
          icon: '',
        })
      })
      categories.value = Array.from(categoryMap.values())
    }
  } catch (e) {
    console.error('Failed to load scenes from API:', e)
    categories.value = []
    scenes.value = []
    notification.error('加载失败', '场景库暂时无法获取后端数据')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.scene-search :deep(.el-input__wrapper) {
  border-radius: 24px;
  padding: 4px 16px;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
