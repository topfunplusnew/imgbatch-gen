<template>
  <div class="h-full flex flex-col bg-white">
    <!-- 标题栏 -->
<!--    <div class="flex items-center justify-between p-4 border-b border-border-dark shrink-0">-->
<!--      <span class="font-bold text-sm uppercase tracking-wider">我的创作</span>-->
<!--    </div>-->

    <!-- 记录列表 -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-6">
      <!-- 加载状态 -->
      <div v-if="loading && records.length === 0" class="flex items-center justify-center py-20">
        <div class="flex flex-col items-center gap-4">
          <div class="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p class="text-sm text-ink-500">加载中...</p>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="records.length === 0" class="flex items-center justify-center py-20">
        <div class="text-center">
          <span class="material-symbols-outlined !text-6xl text-ink-300 mb-4 block">photo_library</span>
          <p class="text-base text-ink-500 mb-2">暂无创作记录</p>
          <p class="text-sm text-ink-400">开始生成图片后，记录将显示在这里</p>
        </div>
      </div>

      <!-- 图片网格 -->
      <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <div
          v-for="record in records"
          :key="record.id"
          class="group relative rounded-lg overflow-hidden bg-gray-100 cursor-pointer hover:shadow-lg transition-all"
        >
          <!-- 图片 -->
          <div class="aspect-square">
            <img
              v-if="record.image_urls && record.image_urls.length > 0"
              :src="record.image_urls[0]"
              :alt="record.prompt"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              @error="handleImageError"
            >
            <div v-else class="w-full h-full flex items-center justify-center text-ink-300">
              <span class="material-symbols-outlined !text-4xl">image</span>
            </div>
          </div>

          <!-- 多图标记 -->
          <div
            v-if="record.image_urls && record.image_urls.length > 1"
            class="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded"
          >
            {{ record.image_urls.length }}张
          </div>

          <!-- 状态标记 -->
          <div
            v-if="record.status === 'processing' || record.status === 'pending'"
            class="absolute inset-0 bg-black/50 flex items-center justify-center"
          >
            <div class="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          <div
            v-else-if="record.status === 'failed'"
            class="absolute inset-0 bg-black/50 flex items-center justify-center"
          >
            <span class="material-symbols-outlined !text-3xl text-white">error</span>
          </div>

          <!-- 悬浮信息 -->
          <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-3">
            <p class="text-white text-xs line-clamp-2 mb-2">{{ record.prompt }}</p>
            <div class="flex items-center gap-2 text-white/80 text-xs">
              <span>{{ formatDate(record.timestamp || record.created_at) }}</span>
              <span>·</span>
              <span>{{ record.model || '未知模型' }}</span>
            </div>
          </div>

          <!-- 点击查看详情 -->
          <button
            @click.stop="viewDetail(record)"
            class="absolute bottom-2 right-2 p-2 bg-white/90 hover:bg-white rounded-lg shadow opacity-0 group-hover:opacity-100 transition-all"
            title="查看详情"
          >
            <span class="material-symbols-outlined !text-base text-gray-700">visibility</span>
          </button>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore && records.length > 0" class="text-center mt-6">
        <button
          v-if="!loading"
          @click="loadMore"
          class="px-6 py-2 bg-white border border-border-dark hover:bg-gray-50 rounded-lg text-sm text-ink-700 transition-colors"
        >
          加载更多
        </button>
        <div v-else class="flex items-center justify-center gap-2">
          <div class="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
          <span class="text-sm text-ink-500">加载中...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { api } from '@/services/api'
import { useAppStore } from '@/store/useAppStore'

const appStore = useAppStore()

const loading = ref(false)
const records = ref([])
const hasMore = ref(true)
const totalRecords = ref(0)
const offset = ref(0)
const limit = 20

const handleImageError = (event) => {
  event.target.src = '/placeholder-case.png'
}

const loadRecords = async (reset = false) => {
  if (loading.value) return

  loading.value = true

  try {
    const data = await api.getUnifiedGenerationHistory(
      limit,
      reset ? 0 : offset.value
    )

    if (reset) {
      records.value = data
      offset.value = data.length
    } else {
      records.value.push(...data)
      offset.value += data.length
    }

    hasMore.value = data.length === limit

    // 获取总数
    try {
      const countData = await api.getUnifiedGenerationHistoryCount()
      totalRecords.value = countData.count
    } catch (error) {
      console.error('获取总数失败:', error)
    }
  } catch (error) {
    console.error('加载创作记录失败:', error)
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  loadRecords()
}

const viewDetail = (record) => {
  appStore.setSelectedCreation(record)
}

const formatDate = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

// 监听显示状态，打开时重新加载
watch(() => appStore.showCreationRecords, (newVal) => {
  if (newVal && records.value.length === 0) {
    loadRecords(true)
  }
})

onMounted(() => {
  if (appStore.showCreationRecords) {
    loadRecords(true)
  }
})
</script>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
