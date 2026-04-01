<template>
  <main class="flex h-full min-h-0 flex-1 flex-col overflow-y-auto bg-background-dark">
    <!-- Hero -->
    <div class="px-4 pt-8 pb-6 text-center xs:px-6 md:px-8 md:pt-12">
      <h1 class="text-2xl font-bold text-primary md:text-4xl">多图创作</h1>
      <p class="mt-2 text-sm text-ink-500">一句话变成一组图片</p>
    </div>

    <!-- Input card -->
    <div class="mx-auto w-full max-w-[760px] px-4 xs:px-6">
      <div class="rounded-3xl border border-border-dark bg-white/92 p-4 shadow-xl">
        <el-input
          v-model="promptInput"
          type="textarea"
          :rows="4"
          placeholder="输入主题或内容即可出图，例如：三只小猪、十二星座、四季变换..."
          resize="none"
          @keydown.ctrl.enter="startBatchGeneration"
          @keydown.meta.enter="startBatchGeneration"
        />
        <div class="mt-3 flex flex-wrap items-center gap-2">
          <ModelDropdown class="shrink-0" />
          <RatioDropdown class="shrink-0" />
          <ResolutionDropdown class="shrink-0" />
          <!-- Card count -->
          <el-popover placement="bottom" :width="200" trigger="click">
            <template #reference>
              <el-button>
                <span class="material-symbols-outlined !text-lg">grid_on</span>
                <span class="text-sm">{{ batchCount }}张</span>
              </el-button>
            </template>
            <div class="space-y-3">
              <div class="text-xs font-semibold text-ink-700">选择生成张数</div>
              <div class="grid grid-cols-3 gap-2">
                <el-button v-for="c in presetCounts" :key="c"
                  :type="batchCount === c ? 'primary' : 'default'" :plain="batchCount !== c"
                  size="small" @click="batchCount = c">{{ c }}</el-button>
              </div>
              <el-input-number v-model="batchCount" :min="1" :max="36" size="small"
                controls-position="right" class="w-full" />
            </div>
          </el-popover>
          <div class="flex-1"></div>
          <el-button type="primary" round :disabled="!promptInput.trim()" :loading="isGenerating"
            @click="startBatchGeneration">
            <span class="material-symbols-outlined !text-lg">auto_awesome</span>
            <span class="hidden xs:inline">生成</span>
          </el-button>
        </div>
      </div>
    </div>

    <!-- Type/Style selector -->
    <div class="mx-auto mt-6 w-full max-w-[760px] px-4 xs:px-6">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="类型" name="type">
          <div class="grid grid-cols-3 gap-3 xs:grid-cols-4 md:grid-cols-5">
            <button v-for="t in imageTypes" :key="t.value" @click="selectedType = t.value"
              :class="['flex flex-col items-center gap-2 rounded-2xl border p-3 transition-all',
                selectedType === t.value ? 'border-primary bg-primary/8 shadow-sm' : 'border-border-dark bg-white/60 hover:border-primary/30']">
              <span class="text-2xl">{{ t.emoji }}</span>
              <span class="text-xs font-medium text-ink-700">{{ t.label }}</span>
            </button>
          </div>
        </el-tab-pane>
        <el-tab-pane label="风格" name="style">
          <div class="grid grid-cols-3 gap-3 xs:grid-cols-4 md:grid-cols-5">
            <button v-for="s in imageStyles" :key="s.value" @click="selectedStyle = s.value"
              :class="['flex flex-col items-center gap-2 rounded-2xl border p-3 transition-all',
                selectedStyle === s.value ? 'border-primary bg-primary/8 shadow-sm' : 'border-border-dark bg-white/60 hover:border-primary/30']">
              <span class="text-2xl">{{ s.emoji }}</span>
              <span class="text-xs font-medium text-ink-700">{{ s.label }}</span>
            </button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Multi-image gallery records -->
    <div class="mx-auto mt-8 w-full max-w-[760px] px-4 pb-8 xs:px-6">
      <div v-if="galleryRecords.length > 0" class="mb-4 flex items-center justify-between">
        <h3 class="text-sm font-semibold text-ink-700">创作记录</h3>
        <router-link to="/gallery" class="text-xs text-primary hover:underline">查看更多</router-link>
      </div>

      <div v-if="galleryRecords.length > 0" class="space-y-4">
        <div v-for="record in galleryRecords" :key="record.id"
          class="overflow-hidden rounded-2xl border border-border-dark bg-white/80 transition hover:shadow-md">
          <!-- Multi-image grid -->
          <div class="grid gap-1"
            :class="record.image_urls?.length >= 4 ? 'grid-cols-4' :
                    record.image_urls?.length === 3 ? 'grid-cols-3' :
                    record.image_urls?.length === 2 ? 'grid-cols-2' : 'grid-cols-1'">
            <div v-for="(url, i) in (record.image_urls || []).slice(0, 4)" :key="i"
              class="aspect-square overflow-hidden cursor-pointer" @click="previewMulti(record, i)">
              <img :src="url" class="h-full w-full object-cover hover:scale-105 transition-transform" loading="lazy" />
            </div>
            <!-- More indicator -->
            <div v-if="record.image_urls?.length > 4"
              class="absolute bottom-1 right-1 rounded-full bg-black/60 px-2 py-0.5 text-xs text-white">
              +{{ record.image_urls.length - 4 }}
            </div>
          </div>

          <!-- Info -->
          <div class="p-3">
            <div class="mb-1.5 flex flex-wrap gap-1">
              <span v-if="record.model" class="rounded-md bg-primary-soft px-1.5 py-0.5 text-[10px] font-medium text-primary">{{ record.model }}</span>
              <span class="rounded-md bg-ink-300/20 px-1.5 py-0.5 text-[10px] text-ink-500">{{ record.image_urls?.length || 0 }}张</span>
            </div>
            <div class="flex items-start gap-2">
              <p class="flex-1 text-xs text-ink-700 line-clamp-2">{{ record.prompt || '无提示词' }}</p>
              <button v-if="record.prompt" @click="copyPrompt(record.prompt)"
                class="shrink-0 text-ink-300 hover:text-primary transition" title="复制提示词">
                <span class="material-symbols-outlined !text-sm">content_copy</span>
              </button>
            </div>
            <div class="mt-1.5 text-[10px] text-ink-500">{{ formatTime(record.created_at) }}</div>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else class="mt-8 text-center text-ink-500">
        <span class="material-symbols-outlined !text-5xl text-ink-300">collections</span>
        <p class="mt-3 text-sm">开始创作你的第一组图片吧</p>
      </div>
    </div>

    <!-- Preview dialog -->
    <el-dialog v-model="showPreview" width="min(90vw, 800px)" align-center>
      <div v-if="previewRecord">
        <div class="grid gap-2" :class="previewRecord.image_urls?.length > 1 ? 'grid-cols-2' : 'grid-cols-1'">
          <img v-for="(url, i) in previewRecord.image_urls" :key="i" :src="url"
            class="w-full rounded-xl" :class="{ 'ring-2 ring-primary': i === previewIndex }" />
        </div>
        <div class="mt-4">
          <p class="text-sm text-ink-700">{{ previewRecord.prompt }}</p>
        </div>
      </div>
    </el-dialog>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import ModelDropdown from '@/components/landing/ModelDropdown.vue'
import RatioDropdown from '@/components/landing/RatioDropdown.vue'
import ResolutionDropdown from '@/components/landing/ResolutionDropdown.vue'
import api from '@/services/api'
import { notification } from '@/utils/notification'

const generatorStore = useGeneratorStore()

const promptInput = ref('')
const batchCount = ref(4)
const activeTab = ref('type')
const selectedType = ref('poster')
const selectedStyle = ref('hand_drawn')
const isGenerating = ref(false)
const galleryRecords = ref([])
const showPreview = ref(false)
const previewRecord = ref(null)
const previewIndex = ref(0)

const presetCounts = [4, 8, 12, 16, 20, 36]

const imageTypes = [
  { value: 'poster', label: '海报设计', emoji: '🎨' },
  { value: 'knowledge', label: '知识科普', emoji: '📚' },
  { value: 'flow_guide', label: '流程指南', emoji: '📋' },
  { value: 'comic', label: '漫画故事', emoji: '💬' },
  { value: 'checklist', label: '清单合集', emoji: '✅' },
  { value: 'event', label: '活动策划', emoji: '🎉' },
  { value: 'card', label: '知识卡片', emoji: '🃏' },
  { value: 'infographic', label: '信息图表', emoji: '📊' },
  { value: 'timeline', label: '时间轴', emoji: '⏳' },
  { value: 'comparison', label: '对比图', emoji: '⚖️' },
]

const imageStyles = [
  { value: 'hand_drawn', label: '手绘', emoji: '✏️' },
  { value: 'flat', label: '扁平', emoji: '🟦' },
  { value: 'watercolor', label: '水彩', emoji: '🎨' },
  { value: 'cartoon', label: '卡通', emoji: '🧸' },
  { value: 'realistic', label: '写实', emoji: '📷' },
  { value: 'anime', label: '动漫', emoji: '🌸' },
  { value: '3d', label: '3D', emoji: '🧊' },
  { value: 'pixel', label: '像素', emoji: '👾' },
  { value: 'minimalist', label: '极简', emoji: '⬜' },
  { value: 'vintage', label: '复古', emoji: '📜' },
]

const copyPrompt = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    notification.success('已复制', '提示词已复制到剪贴板')
  } catch { notification.error('复制失败', '') }
}

const previewMulti = (record, index) => {
  previewRecord.value = record
  previewIndex.value = index
  showPreview.value = true
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const startBatchGeneration = async () => {
  if (!promptInput.value.trim()) return
  isGenerating.value = true
  try {
    const typeLabel = imageTypes.find(t => t.value === selectedType.value)?.label || ''
    const styleLabel = imageStyles.find(s => s.value === selectedStyle.value)?.label || ''
    const fullPrompt = `${promptInput.value}\n风格：${styleLabel}\n类型：${typeLabel}\n生成${batchCount.value}张`
    generatorStore.prompt = fullPrompt
    generatorStore.batchCount = batchCount.value
    generatorStore.setPendingAutoSend(true)
    notification.success('已提交', `正在生成 ${batchCount.value} 张图片...`)
  } catch (err) {
    notification.error('生成失败', err.message || '请稍后重试')
  } finally {
    isGenerating.value = false
  }
}

const loadGallery = async () => {
  try {
    // Load records that have multiple images
    const records = await api.getUnifiedGenerationHistory(6, 0, 'completed')
    galleryRecords.value = (records || []).filter(r => r.image_urls?.length > 0)
  } catch {
    try {
      const records = await api.getGenerationHistory(6, 0, 'completed')
      galleryRecords.value = (records || []).filter(r => r.image_urls?.length > 0)
    } catch { galleryRecords.value = [] }
  }
}

onMounted(() => { loadGallery() })
</script>

<style scoped>
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
