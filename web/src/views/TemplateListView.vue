<template>
  <main class="flex min-h-screen flex-1 flex-col overflow-hidden bg-white/55">
    <TopHeader
      @toggleSettings="$emit('toggleSettings')"
      @toggleSidebar="$emit('toggleSidebar')"
    />

    <el-scrollbar class="template-list-view__scroll">
      <section class="mx-auto w-full max-w-7xl px-4 py-6 xs:px-6 md:px-8 md:py-8">
        <el-card shadow="never" class="template-hero-card">
          <div class="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div class="max-w-3xl">
              <el-tag round effect="plain" class="!border-primary/20 !bg-primary-soft !text-primary">
                模版列表
              </el-tag>
              <h1 class="mt-4 text-2xl font-bold tracking-tight text-ink-950 md:text-3xl">
                快速挑选适合当前创作场景的模版
              </h1>
              <p class="mt-3 text-sm leading-7 text-ink-500 md:text-base">
                所有模版都以卡片方式集中展示，你可以直接预览、筛选并一键带入当前对话，保持原有提示词和参数应用逻辑不变。
              </p>
            </div>

            <div class="grid gap-3 sm:grid-cols-3 xl:min-w-[360px]">
              <el-statistic title="当前已加载" :value="cases.length" />
              <el-statistic title="筛选结果" :value="filteredCases.length" />
              <el-statistic title="分类数量" :value="categories.length" />
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="mt-5">
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center">
            <el-input
              v-model="searchKeyword"
              clearable
              placeholder="搜索标题、描述或标签"
              class="lg:max-w-md"
            >
              <template #prefix>
                <span class="material-symbols-outlined !text-sm text-ink-500">search</span>
              </template>
            </el-input>

            <el-select
              v-model="selectedCategory"
              class="lg:max-w-[220px]"
              placeholder="选择分类"
            >
              <el-option label="全部分类" value="" />
              <el-option
                v-for="category in categories"
                :key="category"
                :label="category"
                :value="category"
              />
            </el-select>

            <div class="flex-1"></div>

            <el-button plain @click="resetFilters">
              <span class="material-symbols-outlined !text-lg">filter_alt_off</span>
              <span>重置筛选</span>
            </el-button>
          </div>
        </el-card>

        <div v-if="loading && cases.length === 0" class="mt-6 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          <el-skeleton
            v-for="index in 6"
            :key="index"
            animated
            class="template-skeleton"
          >
            <template #template>
              <el-card shadow="never">
                <div class="flex flex-col gap-4 lg:flex-row">
                  <el-skeleton-item variant="image" class="h-44 w-full rounded-[20px] lg:w-56" />
                  <div class="flex flex-1 flex-col gap-3">
                    <el-skeleton-item variant="h3" style="width: 56%;" />
                    <el-skeleton-item variant="text" />
                    <el-skeleton-item variant="text" style="width: 84%;" />
                    <el-skeleton-item variant="text" style="width: 38%;" />
                  </div>
                </div>
              </el-card>
            </template>
          </el-skeleton>
        </div>

        <div v-else-if="filteredCases.length === 0" class="mt-6">
          <el-card shadow="never">
            <el-empty description="没有匹配的模版" :image-size="72" />
          </el-card>
        </div>

        <div v-else class="mt-6 flex flex-col gap-4">
          <el-card
            v-for="caseItem in filteredCases"
            :key="caseItem.id"
            shadow="hover"
            class="template-list-card"
          >
            <div class="flex flex-col gap-5 lg:flex-row">
              <div class="template-list-card__media">
                <img
                  :src="getCaseImageSources(caseItem)[0]"
                  :data-fallback-src="getCaseImageSources(caseItem)[1] || ''"
                  :alt="caseItem.title"
                  class="h-full w-full object-cover"
                  @error="handleImageFallback"
                >
              </div>

              <div class="flex min-w-0 flex-1 flex-col">
                <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div class="min-w-0">
                    <div class="flex flex-wrap items-center gap-2">
                      <h3 class="truncate text-lg font-semibold text-ink-950">
                        {{ caseItem.title }}
                      </h3>
                      <el-tag effect="plain" round>{{ caseItem.category }}</el-tag>
                    </div>
                    <p class="mt-3 line-clamp-3 text-sm leading-7 text-ink-500">
                      {{ caseItem.description || caseItem.prompt }}
                    </p>
                  </div>

                  <div class="flex items-center gap-2 text-xs text-ink-500">
                    <span class="material-symbols-outlined !text-base">visibility</span>
                    <span>{{ caseItem.view_count }}</span>
                    <span class="material-symbols-outlined !text-base">bolt</span>
                    <span>{{ caseItem.use_count }}</span>
                  </div>
                </div>

                <div class="mt-4 flex flex-wrap gap-2">
                  <el-tag
                    v-for="tag in (caseItem.tags || []).slice(0, 6)"
                    :key="tag"
                    round
                    effect="plain"
                    class="!bg-white"
                  >
                    {{ tag }}
                  </el-tag>
                  <el-tag
                    v-if="caseItem.model"
                    type="info"
                    round
                    effect="plain"
                  >
                    {{ caseItem.model }}
                  </el-tag>
                </div>

                <div class="mt-auto flex flex-wrap items-center gap-3 pt-5">
                  <el-button plain @click="previewTemplate(caseItem)">
                    <span class="material-symbols-outlined !text-lg">preview</span>
                    <span>查看详情</span>
                  </el-button>
                  <el-button type="primary" @click="useTemplate(caseItem)">
                    <span class="material-symbols-outlined !text-lg">auto_awesome</span>
                    <span>使用模版</span>
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
        </div>

        <div v-if="hasMore" class="pb-2 pt-6 text-center">
          <el-button :loading="loading" plain @click="loadMoreTemplates">
            <span class="material-symbols-outlined !text-lg">expand_more</span>
            <span>{{ loading ? '加载中...' : '加载更多模版' }}</span>
          </el-button>
        </div>
      </section>
    </el-scrollbar>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import TopHeader from '@/components/layout/TopHeader.vue'
import { useAppStore } from '@/store/useAppStore'
import { useCaseStore } from '@/store/useCaseStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { handleImageFallback, resolveImageSrcCandidates } from '@/utils/imageFallback'
import { notification } from '@/utils/notification'

defineEmits(['toggleSettings', 'toggleSidebar'])

const appStore = useAppStore()
const caseStore = useCaseStore()
const generatorStore = useGeneratorStore()

const searchKeyword = ref('')
const selectedCategory = ref('')

const cases = computed(() => caseStore.cases || [])
const categories = computed(() => caseStore.categories || [])
const loading = computed(() => caseStore.loading)
const hasMore = computed(() => caseStore.hasMore)

const filteredCases = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()

  return cases.value.filter((caseItem) => {
    const matchedCategory = !selectedCategory.value || caseItem.category === selectedCategory.value
    const matchedKeyword = !keyword || [
      caseItem.title,
      caseItem.description,
      caseItem.prompt,
      ...(caseItem.tags || [])
    ].some((field) => String(field || '').toLowerCase().includes(keyword))

    return matchedCategory && matchedKeyword
  })
})

const getCaseImageSources = (caseItem) => {
  return resolveImageSrcCandidates(caseItem?.thumbnail_url, caseItem?.image_url)
}

const resetFilters = () => {
  searchKeyword.value = ''
  selectedCategory.value = ''
}

const syncModelInfo = (modelName) => {
  if (!modelName) return

  generatorStore.setSelectedModel(modelName)
  const matchedModel = generatorStore.availableModels.find((model) => model.model_name === modelName)
  generatorStore.setSelectedModelInfo(matchedModel || null)
}

const applyTemplateToGenerator = async (caseItem) => {
  generatorStore.prompt = caseItem.prompt
  generatorStore.negativePrompt = caseItem.negative_prompt || ''

  if (caseItem.parameters) {
    const params = caseItem.parameters
    if (params.width) generatorStore.width = params.width
    if (params.height) generatorStore.height = params.height
    if (params.style) generatorStore.style = params.style
    if (params.quality) generatorStore.quality = params.quality
    if (params.seed) generatorStore.seed = params.seed
  }

  if (caseItem.model) {
    syncModelInfo(caseItem.model)
  }

  await caseStore.useCaseTemplate(caseItem.id)
}

const previewTemplate = (caseItem) => {
  appStore.setSelectedCase(caseItem)
  appStore.setCurrentView('chat')
}

const useTemplate = async (caseItem) => {
  await applyTemplateToGenerator(caseItem)
  appStore.clearSelectedCase()
  appStore.setCurrentView('chat')
  notification.success('模版已应用', '提示词和参数已带入当前对话')
}

const loadMoreTemplates = async () => {
  await caseStore.loadMore()
}

onMounted(async () => {
  if (caseStore.cases.length === 0) {
    await caseStore.refresh()
  }

  if (generatorStore.availableModels.length === 0) {
    generatorStore.fetchAvailableModels()
  }
})
</script>

<style scoped>
.template-list-view__scroll :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

.template-hero-card {
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(140, 42, 46, 0.1), transparent 36%),
    linear-gradient(135deg, rgba(255, 253, 252, 0.95), rgba(248, 240, 239, 0.9));
}

.template-hero-card :deep(.el-card__body) {
  padding: 28px;
}

.template-list-card {
  overflow: hidden;
}

.template-list-card :deep(.el-card__body) {
  padding: 20px;
}

.template-list-card__media {
  width: 100%;
  overflow: hidden;
  border-radius: 22px;
  background: rgba(140, 42, 46, 0.06);
  aspect-ratio: 16 / 10;
}

.template-skeleton :deep(.el-card__body) {
  padding: 20px;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (min-width: 1024px) {
  .template-list-card__media {
    width: 240px;
    min-width: 240px;
    aspect-ratio: 4 / 3;
  }
}
</style>
