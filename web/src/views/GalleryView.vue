<template>
  <main class="flex h-full min-h-0 flex-1 flex-col overflow-y-auto bg-background-dark">
    <!-- Header -->
    <div class="px-4 pt-8 pb-6 xs:px-6 md:px-8 md:pt-12">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="text-2xl font-bold text-ink-950 md:text-3xl">我的作品</h1>
          <p class="mt-1 text-sm text-ink-500">共 {{ totalCount }} 件作品</p>
        </div>
        <div class="flex items-center gap-2">
          <el-button @click="viewMode = viewMode === 'grid' ? 'list' : 'grid'" circle>
            <span class="material-symbols-outlined !text-lg">{{ viewMode === 'grid' ? 'view_list' : 'grid_view' }}</span>
          </el-button>
          <el-button @click="fetchCreations" circle :loading="loading">
            <span class="material-symbols-outlined !text-lg">refresh</span>
          </el-button>
        </div>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="flex flex-wrap items-center gap-2 px-4 pb-4 xs:px-6 md:px-8">
      <el-input
        v-model="searchQuery"
        clearable
        placeholder="搜索作品..."
        class="!w-48"
      >
        <template #prefix>
          <span class="material-symbols-outlined !text-sm">search</span>
        </template>
      </el-input>
      <el-select v-model="statusFilter" placeholder="状态" clearable class="!w-28">
        <el-option label="全部" value="" />
        <el-option label="已完成" value="completed" />
        <el-option label="处理中" value="processing" />
        <el-option label="失败" value="failed" />
      </el-select>
    </div>

    <!-- Loading -->
    <div v-if="loading && creations.length === 0" class="flex flex-1 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-3 border-primary border-t-transparent"></div>
    </div>

    <!-- Empty state -->
    <div v-else-if="filteredCreations.length === 0" class="flex flex-1 flex-col items-center justify-center gap-4 text-ink-500">
      <span class="material-symbols-outlined !text-6xl text-ink-300">photo_library</span>
      <p class="text-sm">还没有作品，去创作一张吧</p>
      <router-link to="/">
        <el-button type="primary" round>开始创作</el-button>
      </router-link>
    </div>

    <!-- Grid / List view -->
    <div v-else class="px-4 pb-8 xs:px-6 md:px-8">
      <div :class="viewMode === 'grid'
        ? 'grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
        : 'space-y-3'"
      >
        <div
          v-for="item in filteredCreations"
          :key="item.id"
          :class="[
            'group relative cursor-pointer overflow-hidden rounded-2xl border border-border-dark bg-white/90 shadow-sm hover:shadow-xl hover:-translate-y-0.5',
            viewMode === 'list' ? 'flex items-center' : ''
          ]"
          @click="previewImage(item)"
        >
          <!-- Image -->
          <div :class="viewMode === 'grid' ? 'aspect-square' : 'h-20 w-20 shrink-0'">
            <img
              v-if="getImageUrl(item)"
              :src="getImageUrl(item)"
              :alt="item.prompt"
              class="h-full w-full object-cover transition-transform group-hover:scale-105"
              loading="lazy"
            />
            <div v-else class="flex h-full items-center justify-center bg-primary-soft text-primary">
              <span class="material-symbols-outlined !text-3xl">image</span>
            </div>
          </div>

          <!-- Status badge -->
          <div v-if="item.status !== 'completed'" class="absolute top-2 left-2">
            <el-tag
              :type="item.status === 'failed' ? 'danger' : 'warning'"
              size="small"
              round
            >
              {{ item.status === 'processing' || item.status === 'pending' ? '处理中' : '失败' }}
            </el-tag>
          </div>

          <!-- Hover overlay with actions (grid mode) -->
          <div v-if="viewMode === 'grid'" class="absolute inset-0 flex items-end bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100">
            <div class="flex w-full items-center justify-center gap-2 p-3">
              <el-button size="small" circle @click.stop="downloadImage(item)" title="下载">
                <span class="material-symbols-outlined !text-sm">download</span>
              </el-button>
              <el-button size="small" circle @click.stop="reusePrompt(item)" title="复用">
                <span class="material-symbols-outlined !text-sm">replay</span>
              </el-button>
            </div>
          </div>

          <!-- Info (grid) -->
          <div v-if="viewMode === 'grid'" class="p-2.5">
            <p class="truncate text-xs font-medium text-ink-950">{{ item.prompt || '未命名' }}</p>
            <div class="mt-0.5 flex items-center gap-1.5">
              <span class="text-[10px] text-ink-500">{{ item.model || '' }}</span>
              <span class="text-[10px] text-ink-300">&middot;</span>
              <span class="text-[10px] text-ink-500">{{ formatTime(item.created_at) }}</span>
            </div>
          </div>

          <!-- Info (list) -->
          <div v-if="viewMode === 'list'" class="flex min-w-0 flex-1 items-center justify-between gap-3 p-3">
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-ink-950">{{ item.prompt || '未命名' }}</p>
              <p class="mt-0.5 text-xs text-ink-500">
                {{ item.model || '未知模型' }} &middot; {{ formatTime(item.created_at) }}
                <span v-if="item.image_urls?.length > 1"> &middot; {{ item.image_urls.length }}张</span>
              </p>
            </div>
            <div class="flex shrink-0 items-center gap-1">
              <el-button size="small" text @click.stop="downloadImage(item)">
                <span class="material-symbols-outlined !text-lg">download</span>
              </el-button>
              <el-button size="small" text @click.stop="reusePrompt(item)">
                <span class="material-symbols-outlined !text-lg">replay</span>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Load more -->
      <div v-if="hasMore" class="mt-6 text-center">
        <el-button @click="loadMore" :loading="loading" round>加载更多</el-button>
      </div>
    </div>

    <!-- Image preview modal -->
    <el-dialog v-model="showPreview" width="min(90vw, 800px)" align-center :show-close="true">
      <div v-if="previewItem">
        <!-- Multiple images -->
        <div v-if="previewItem.image_urls?.length > 1" class="grid grid-cols-2 gap-2">
          <img
            v-for="(url, i) in previewItem.image_urls"
            :key="i"
            :src="url"
            class="w-full rounded-xl"
          />
        </div>
        <!-- Single image -->
        <img v-else :src="getImageUrl(previewItem)" class="w-full rounded-xl" />

        <div class="mt-4 space-y-2">
          <p class="text-sm text-ink-950">{{ previewItem.prompt }}</p>
          <div class="flex flex-wrap gap-2">
            <el-tag v-if="previewItem.model" size="small">{{ previewItem.model }}</el-tag>
            <el-tag v-if="previewItem.style" size="small" type="info">{{ previewItem.style }}</el-tag>
            <el-tag v-if="previewItem.quality" size="small" type="warning">{{ previewItem.quality }}</el-tag>
            <el-tag v-if="previewItem.width && previewItem.height" size="small" type="success">
              {{ previewItem.width }}×{{ previewItem.height }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { api } from '@/services/api'
import { notification } from '@/utils/notification'

const router = useRouter()
const generatorStore = useGeneratorStore()

const creations = ref([])
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const viewMode = ref('grid')
const currentPage = ref(1)
const pageSize = 20
const hasMore = ref(true)
const totalCount = ref(0)
const showPreview = ref(false)
const previewItem = ref(null)

const filteredCreations = computed(() => {
  let result = creations.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(c =>
      (c.prompt || '').toLowerCase().includes(q) ||
      (c.model || '').toLowerCase().includes(q)
    )
  }
  return result
})

const normalizeMinioUrl = (url) => {
  if (!url) return url
  const m = url.match(/^https?:\/\/[^/]*minio[^/]*(?::\d+)?\/([^/]+)\/(.+)$/)
  return m ? `/storage/${m[2]}` : url
}

const getImageUrl = (item) => {
  if (item.image_urls?.length > 0) return normalizeMinioUrl(item.image_urls[0])
  if (item.thumbnail_url) return normalizeMinioUrl(item.thumbnail_url)
  return ''
}

const fetchCreations = async () => {
  loading.value = true
  currentPage.value = 1
  try {
    const [records, countRes] = await Promise.all([
      api.getUnifiedGenerationHistory(pageSize, 0, statusFilter.value || undefined),
      api.getUnifiedGenerationHistoryCount(statusFilter.value || undefined)
    ])
    creations.value = records || []
    totalCount.value = countRes?.count || creations.value.length
    hasMore.value = creations.value.length >= pageSize
  } catch (err) {
    // Fallback to basic generation history
    try {
      const records = await api.getGenerationHistory(pageSize, 0, statusFilter.value || undefined)
      creations.value = records || []
      totalCount.value = creations.value.length
      hasMore.value = creations.value.length >= pageSize
    } catch {
      creations.value = []
      totalCount.value = 0
      hasMore.value = false
    }
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  loading.value = true
  currentPage.value++
  const offset = (currentPage.value - 1) * pageSize
  try {
    const records = await api.getUnifiedGenerationHistory(pageSize, offset, statusFilter.value || undefined)
    const newItems = records || []
    creations.value.push(...newItems)
    hasMore.value = newItems.length >= pageSize
  } catch {
    hasMore.value = false
  } finally {
    loading.value = false
  }
}

const previewImage = (item) => {
  if (getImageUrl(item)) {
    previewItem.value = item
    showPreview.value = true
  }
}

const downloadImage = async (item) => {
  const url = getImageUrl(item)
  if (!url) return
  try {
    const link = document.createElement('a')
    link.href = url
    link.download = `creation-${item.id || Date.now()}.png`
    link.target = '_blank'
    link.click()
    // Record download
    api.recordDownload({ image_url: url, file_name: link.download }).catch(() => {})
  } catch {
    notification.error('下载失败', '')
  }
}

const reusePrompt = (item) => {
  if (item.prompt) {
    generatorStore.prompt = item.prompt
    router.push('/')
    notification.success('已复用', '提示词已填入输入框')
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  let normalized = timestamp
  if (typeof timestamp === 'string' && !timestamp.endsWith('Z') && !timestamp.includes('+') && !/[+-]\d{2}:\d{2}$/.test(timestamp)) {
    normalized = timestamp.replace(' ', 'T') + 'Z'
  }
  const date = new Date(normalized)
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchCreations()
})
</script>
