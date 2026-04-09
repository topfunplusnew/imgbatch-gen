<template>
  <main class="flex h-full min-h-0 flex-1 flex-col overflow-y-auto bg-background-dark">
    <!-- Hero -->
    <div class="px-4 pt-6 pb-4 text-center xs:px-6 md:px-8 md:pt-10">
      <h1 class="text-2xl font-bold text-primary md:text-3xl">多图创作</h1>
      <p class="mt-1.5 text-sm text-ink-500">一句话变成一组图片</p>
    </div>

    <!-- Input card -->
    <div class="mx-auto w-full max-w-[720px] px-4 xs:px-6">
      <div class="rounded-2xl border border-border-dark bg-white/95 p-4 shadow-[0_16px_48px_rgba(140,42,46,0.06)]">
        <el-input
          v-model="promptInput"
          type="textarea"
          :rows="3"
          placeholder="输入主题或内容描述，例如：三十六计、十二星座、四季变化..."
          resize="none"
          @keydown.ctrl.enter="startBatchGeneration"
          @keydown.meta.enter="startBatchGeneration"
        />
        <!-- Toolbar: tags + params + send -->
        <div class="mt-2.5 flex flex-wrap items-center gap-1.5">
          <!-- Selected type tag -->
          <button v-if="selectedTypeLabel"
            class="inline-flex items-center gap-1 rounded-lg border border-primary/20 bg-primary/8 px-2.5 py-1.5 text-xs font-medium text-primary cursor-pointer hover:bg-primary/15"
            @click="selectedType = ''">
            {{ selectedTypeEmoji }} {{ selectedTypeLabel }}
            <span class="material-symbols-outlined !text-[11px] ml-0.5 opacity-50">close</span>
          </button>
          <!-- Selected style tag -->
          <button v-if="selectedStyleLabel"
            class="inline-flex items-center gap-1 rounded-lg border border-border-dark bg-white px-2.5 py-1.5 text-xs font-medium text-ink-700 cursor-pointer hover:bg-ink-300/10"
            @click="selectedStyle = ''">
            {{ selectedStyleLabel }}
            <span class="material-symbols-outlined !text-[11px] ml-0.5 opacity-50">close</span>
          </button>
          <!-- Ratio -->
          <RatioDropdown class="shrink-0" />
          <!-- Resolution -->
          <ResolutionDropdown class="shrink-0" />
          <!-- Batch count -->
          <el-popover placement="bottom" :width="200" trigger="click">
            <template #reference>
              <el-button size="small">
                <span class="material-symbols-outlined !text-sm">grid_on</span>
                <span class="text-xs">{{ batchCount }}张</span>
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
          <!-- File upload -->
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="false"
            :multiple="true"
            accept="image/*,.pdf,.docx,.doc,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            :on-change="handleUploadChange"
          >
            <el-button size="small" circle>
              <span class="material-symbols-outlined !text-sm">attach_file</span>
            </el-button>
          </el-upload>
          <div class="flex-1"></div>
          <!-- Model selector -->
          <ModelDropdown class="shrink-0" />
          <!-- Send button -->
          <el-button type="primary" round size="small" :disabled="(!promptInput.trim() && attachments.length === 0) || isGenerating"
            :loading="isGenerating" @click="startBatchGeneration"
            class="!px-4">
            <span class="material-symbols-outlined !text-base">arrow_upward</span>
            <span class="material-symbols-outlined !text-base">bolt</span>
          </el-button>
        </div>
        <!-- Attachments -->
        <div v-if="attachments.length > 0" class="mt-2 flex flex-wrap gap-1.5">
          <div v-for="(file, i) in attachments" :key="i"
            class="flex items-center gap-1.5 rounded-lg border border-primary/20 bg-primary-soft px-2.5 py-1">
            <span class="material-symbols-outlined !text-sm text-primary">{{ getFileIcon(file) }}</span>
            <span class="max-w-[100px] truncate text-xs text-ink-700">{{ file.name }}</span>
            <button @click="attachments.splice(i, 1)" class="text-ink-500 hover:text-ink-950 cursor-pointer">
              <span class="material-symbols-outlined !text-xs">close</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Type/Style selector -->
    <div class="mx-auto mt-5 w-full max-w-[720px] px-4 xs:px-6">
      <div class="flex items-center gap-2 mb-3">
        <button @click="activeTab = 'type'"
          :class="['rounded-lg px-4 py-1.5 text-sm font-medium cursor-pointer',
            activeTab === 'type' ? 'bg-ink-950 text-white' : 'bg-white/80 text-ink-700 border border-border-dark hover:bg-white']">
          类型
        </button>
        <button @click="activeTab = 'style'"
          :class="['rounded-lg px-4 py-1.5 text-sm font-medium cursor-pointer',
            activeTab === 'style' ? 'bg-ink-950 text-white' : 'bg-white/80 text-ink-700 border border-border-dark hover:bg-white']">
          风格
        </button>
        <span class="material-symbols-outlined !text-lg text-ink-400 cursor-pointer" @click="showTypePanel = !showTypePanel">
          {{ showTypePanel ? 'expand_less' : 'expand_more' }}
        </span>
      </div>

      <div v-show="showTypePanel">
        <!-- 类型：有封面图用卡片，无封面图用文字标签 -->
        <div v-if="activeTab === 'type'">
          <div v-if="typesHasCover" class="grid grid-cols-3 gap-2.5 xs:grid-cols-4 md:grid-cols-5">
            <button v-for="t in filteredTypes" :key="t.value"
              @click="selectedType = selectedType === t.value ? '' : t.value"
              class="relative flex flex-col items-center cursor-pointer group">
              <div :class="['w-full overflow-hidden rounded-xl border-2',
                selectedType === t.value ? 'border-primary' : 'border-transparent hover:border-primary/30']">
                <div class="overflow-hidden bg-primary-soft/10 rounded-xl">
                  <img v-if="t.cover" :src="t.cover" :alt="t.label"
                    class="w-full h-auto object-contain group-hover:scale-105 transition-transform duration-300" loading="lazy" />
                  <div v-else class="w-full aspect-square flex items-center justify-center text-sm font-bold text-ink-400">{{ t.label }}</div>
                </div>
              </div>
              <div v-if="selectedType === t.value"
                class="absolute top-1.5 right-1.5 grid h-5 w-5 place-items-center rounded-full bg-primary text-white">
                <span class="material-symbols-outlined !text-xs">check</span>
              </div>
              <span class="mt-1 text-xs text-ink-700 font-medium">{{ t.label }}</span>
            </button>
          </div>
          <div v-else class="flex flex-wrap gap-2">
            <button v-for="t in filteredTypes" :key="t.value"
              @click="selectedType = selectedType === t.value ? '' : t.value"
              :class="['rounded-lg border px-3 py-1.5 text-xs font-medium cursor-pointer',
                selectedType === t.value ? 'border-primary bg-primary/8 text-primary' : 'border-border-dark bg-white text-ink-700 hover:border-primary/30']">
              {{ t.label }}
            </button>
          </div>
        </div>

        <!-- 风格：带封面图卡片（完整显示） -->
        <div v-if="activeTab === 'style'">
          <div class="grid grid-cols-3 gap-2.5 xs:grid-cols-4 md:grid-cols-5">
            <button v-for="s in imageStyles" :key="s.value"
              @click="selectedStyle = selectedStyle === s.value ? '' : s.value"
              class="relative flex flex-col items-center cursor-pointer group">
              <div :class="['w-full overflow-hidden rounded-xl border-2',
                selectedStyle === s.value ? 'border-primary' : 'border-transparent hover:border-primary/30']">
                <div class="overflow-hidden bg-primary-soft/10 rounded-xl">
                  <img :src="s.cover" :alt="s.label"
                    class="w-full h-auto object-contain group-hover:scale-105 transition-transform duration-300" loading="lazy" />
                </div>
              </div>
              <div v-if="selectedStyle === s.value"
                class="absolute top-1.5 right-1.5 grid h-5 w-5 place-items-center rounded-full bg-primary text-white">
                <span class="material-symbols-outlined !text-xs">check</span>
              </div>
              <span :class="['mt-1.5 text-xs font-medium',
                selectedStyle === s.value ? 'text-primary' : 'text-ink-700']">{{ s.label }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Generation progress -->
    <div v-if="currentTask" class="mx-auto mt-6 w-full max-w-[760px] px-4 xs:px-6">
      <div class="rounded-2xl border border-primary/30 bg-white/90 p-4 shadow-sm">
        <div class="mb-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span v-if="currentTask.status === 'generating'" class="relative flex h-3 w-3">
              <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
              <span class="relative inline-flex h-3 w-3 rounded-full bg-primary"></span>
            </span>
            <span v-else-if="currentTask.status === 'completed'" class="material-symbols-outlined !text-lg text-green-600">check_circle</span>
            <span v-else-if="currentTask.status === 'error'" class="material-symbols-outlined !text-lg text-red-500">error</span>
            <span class="text-sm font-semibold text-ink-950">{{ currentTask.statusText }}</span>
          </div>
          <button v-if="currentTask.status !== 'generating'" @click="currentTask = null" class="text-ink-400 hover:text-ink-700">
            <span class="material-symbols-outlined !text-lg">close</span>
          </button>
        </div>

        <!-- Progress bar -->
        <div v-if="currentTask.status === 'generating'" class="mb-3">
          <div class="h-2 w-full overflow-hidden rounded-full bg-primary-soft">
            <div class="h-full rounded-full bg-primary transition-all duration-500"
              :style="{ width: currentTask.progress + '%' }"></div>
          </div>
          <p class="mt-1 text-xs text-ink-500">{{ currentTask.progressText }}</p>
        </div>

        <!-- Results grid -->
        <div v-if="currentTask.images.length > 0" class="grid gap-2"
          :class="currentTask.images.length >= 4 ? 'grid-cols-4' :
                  currentTask.images.length === 3 ? 'grid-cols-3' :
                  currentTask.images.length === 2 ? 'grid-cols-2' : 'grid-cols-1'">
          <div v-for="(img, i) in currentTask.images" :key="i"
            class="group relative aspect-square overflow-hidden rounded-xl cursor-pointer"
            @click="previewMulti({ image_urls: currentTask.images.map(x => x.url), prompt: currentTask.prompt }, i)">
            <img :src="img.url" class="h-full w-full object-cover transition-transform group-hover:scale-105" />
            <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition"></div>
          </div>
        </div>

        <!-- Placeholder slots while generating -->
        <div v-else-if="currentTask.status === 'generating'" class="grid gap-2"
          :class="currentTask.total >= 4 ? 'grid-cols-4' :
                  currentTask.total === 3 ? 'grid-cols-3' :
                  currentTask.total === 2 ? 'grid-cols-2' : 'grid-cols-1'">
          <div v-for="i in currentTask.total" :key="i"
            class="aspect-square rounded-xl bg-primary-soft/50 flex items-center justify-center animate-pulse">
            <span class="material-symbols-outlined !text-3xl text-primary/30">image</span>
          </div>
        </div>

        <!-- Error message -->
        <p v-if="currentTask.status === 'error'" class="mt-2 text-sm text-red-500">{{ currentTask.error }}</p>
      </div>
    </div>

    <!-- Gallery records -->
    <div class="mt-8 px-4 pb-8 xs:px-6 md:px-8">
      <div class="w-full">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-lg font-bold text-ink-950">创作记录</h3>
          <router-link v-if="galleryRecords.length > 0" to="/gallery" class="text-xs text-primary hover:underline">查看更多</router-link>
        </div>

        <div v-if="galleryRecords.length > 0" class="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
          <div
            v-for="record in galleryRecords"
            :key="record.id"
            class="group relative overflow-hidden rounded-xl border border-border-dark bg-white/90 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
          >
            <div class="aspect-square overflow-hidden cursor-pointer" @click="previewMulti(record, 0)">
              <img
                v-if="getRecordImage(record)"
                :src="getRecordImage(record)"
                class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                loading="lazy"
              />
              <div v-else class="flex h-full items-center justify-center bg-primary-soft text-primary">
                <span class="material-symbols-outlined !text-4xl">image</span>
              </div>
            </div>

            <div class="absolute top-1.5 right-1.5 flex gap-1 opacity-0 transition group-hover:opacity-100">
              <button
                v-if="record.prompt"
                @click.stop="copyPrompt(record.prompt)"
                class="grid h-7 min-w-7 place-items-center rounded-full bg-white/90 px-2 shadow backdrop-blur-sm hover:bg-white cursor-pointer"
                :title="record.image_urls?.length ? `${record.image_urls.length} 张图片` : '复制提示词'"
              >
                <span class="material-symbols-outlined !text-sm text-ink-700">content_copy</span>
              </button>
            </div>

            <div v-if="record.image_urls?.length > 1"
              class="absolute left-1.5 bottom-[54px] rounded-full bg-black/55 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur-sm">
              {{ record.image_urls.length }} 张
            </div>

            <div class="p-2.5">
              <div class="group/prompt relative">
                <p class="line-clamp-2 pr-5 text-xs text-ink-700">{{ record.prompt || '无提示词' }}</p>
                <button
                  v-if="record.prompt"
                  @click.stop="copyPrompt(record.prompt)"
                  class="absolute top-0 right-0 text-ink-300 hover:text-primary cursor-pointer"
                >
                  <span class="material-symbols-outlined !text-sm">content_copy</span>
                </button>
              </div>
              <div class="mt-1 text-[10px] text-ink-500">{{ formatTime(record.created_at) }}</div>
            </div>
          </div>
        </div>

        <div v-else-if="!currentTask">
          <div class="rounded-xl border border-dashed border-border-dark bg-white/60 p-6">
            <div class="mt-1 text-center">
              <span class="material-symbols-outlined !text-3xl text-ink-300">collections</span>
              <p class="mt-1.5 text-sm font-medium text-ink-700">暂无作品</p>
              <p class="mt-0.5 text-xs text-ink-500">在上方输入内容，创建你的第一组图片</p>
            </div>
          </div>
        </div>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import ModelDropdown from '@/components/landing/ModelDropdown.vue'
import RatioDropdown from '@/components/landing/RatioDropdown.vue'
import ResolutionDropdown from '@/components/landing/ResolutionDropdown.vue'
import { api } from '@/services/api'
import { notification } from '@/utils/notification'
import { copyText } from '@/utils/clipboard'

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
const currentTask = ref(null)
const attachments = ref([])
const uploadRef = ref(null)
let pollTimer = null

const presetCounts = [4, 8, 12, 16, 20, 36]
const showTypePanel = ref(true)
const selectedTypeCategory = ref('all')

// 类型：纯文字标签（从API加载）
const imageTypes = ref([
  { value: 'poster', label: '海报设计' },
  { value: 'reading_notes', label: '读书笔记' },
  { value: 'mind_map', label: '思维导图' },
  { value: 'infographic', label: '信息图表' },
  { value: 'flow_guide', label: '流程指南' },
  { value: 'comic', label: '漫画故事' },
  { value: 'timeline', label: '时间线' },
  { value: 'comparison', label: '对比分析' },
  { value: 'tutorial', label: '教程指南' },
  { value: 'concept_map', label: '概念地图' },
  { value: 'visual_summary', label: '视觉总结' },
  { value: 'poetry', label: '诗词解读' },
  { value: 'formula', label: '公式原理' },
])

const filteredTypes = computed(() => imageTypes.value)
const typesHasCover = computed(() => imageTypes.value.some(t => t.cover))

const selectedTypeObj = computed(() => imageTypes.value.find(t => t.value === selectedType.value))
const selectedTypeLabel = computed(() => selectedTypeObj.value?.label || '')
const selectedTypeEmoji = computed(() => selectedTypeObj.value?.emoji || '')
const selectedStyleLabel = computed(() => {
  if (!selectedStyle.value) return ''
  return imageStyles.value.find(s => s.value === selectedStyle.value)?.label || ''
})

// 风格：带封面图（从API加载）
const imageStyles = ref([
  { value: 'hand_drawn', label: '手绘', cover: '/covers/styles/hand_drawn.webp' },
  { value: 'watercolor', label: '水彩', cover: '/covers/styles/watercolor.webp' },
  { value: 'flat', label: '扁平', cover: '/covers/styles/flat.webp' },
  { value: 'cartoon', label: '卡通', cover: '/covers/styles/cartoon.webp' },
  { value: 'realistic', label: '写实', cover: '/covers/styles/illustration.webp' },
  { value: 'retro', label: '复古', cover: '/covers/styles/retro.webp' },
  { value: 'anime', label: '动漫', cover: '/covers/styles/cartoon.webp' },
  { value: '3d', label: '3D', cover: '/covers/styles/clay.webp' },
  { value: 'minimalist', label: '极简', cover: '/covers/styles/minimalist.webp' },
  { value: 'ink', label: '水墨', cover: '/covers/styles/ink.webp' },
  { value: 'sketch', label: '素描', cover: '/covers/styles/sketch.webp' },
  { value: 'pixel', label: '像素', cover: '/covers/styles/pixel.webp' },
])

const handleUploadChange = (uploadFile) => {
  const file = uploadFile?.raw || uploadFile
  if (!file) return
  attachments.value.push(file)
  uploadRef.value?.clearFiles?.()

  // PDF: auto-detect page count and set batchCount
  if (file.name.toLowerCase().endsWith('.pdf')) {
    import('pdfjs-dist').then(async ({ getDocument }) => {
      try {
        const buf = await file.arrayBuffer()
        const pdf = await getDocument({ data: buf }).promise
        const pages = Math.min(pdf.numPages, 20)
        batchCount.value = pages
        notification.info('PDF 已识别', `共 ${pdf.numPages} 页，将生成 ${pages} 张图片`)
      } catch {}
    }).catch(() => {})
  }
}

const getFileIcon = (file) => {
  const ext = file.name.split('.').pop().toLowerCase()
  if (ext === 'pdf') return 'picture_as_pdf'
  if (['doc', 'docx'].includes(ext)) return 'description'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) return 'image'
  return 'insert_drive_file'
}

const copyPrompt = async (text) => {
  const ok = await copyText(text)
  if (ok) {
    notification.success('已复制', '提示词已复制到剪贴板')
  } else { notification.error('复制失败', '') }
}

const previewMulti = (record, index) => {
  previewRecord.value = record
  previewIndex.value = index
  showPreview.value = true
}

const getRecordImage = (record) => {
  if (record.image_urls?.length > 0) return record.image_urls[0]
  return ''
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const pollTaskProgress = (taskId) => {
  stopPolling()
  let attempts = 0
  const maxAttempts = 300

  pollTimer = setInterval(async () => {
    attempts++
    if (attempts > maxAttempts) {
      stopPolling()
      if (currentTask.value) {
        currentTask.value.status = 'error'
        currentTask.value.statusText = '生成超时'
        currentTask.value.error = '任务超时，请重试'
      }
      isGenerating.value = false
      return
    }

    try {
      const task = await api.getTaskStatus(taskId)
      const status = String(task?.status || '').toLowerCase()

      if (!currentTask.value) return

      if (status === 'completed') {
        stopPolling()
        let images = []
        if (task.images) {
          images = typeof task.images === 'string' ? JSON.parse(task.images) : task.images
        } else if (task.result && Array.isArray(task.result)) {
          images = task.result.map(img => ({ url: img.url, alt: img.alt || '生成的图像' }))
        }

        currentTask.value.status = 'completed'
        currentTask.value.statusText = `生成完成！共 ${images.length} 张图片`
        currentTask.value.progress = 100
        currentTask.value.progressText = '完成'
        currentTask.value.images = images
        isGenerating.value = false
        loadGallery()

      } else if (status === 'failed' || status === 'error') {
        stopPolling()
        currentTask.value.status = 'error'
        currentTask.value.statusText = '生成失败'
        currentTask.value.error = task.error || '图像生成失败，请重试'
        isGenerating.value = false

      } else {
        // Still processing
        const progress = Math.min(90, Math.round((attempts / maxAttempts) * 100))
        const stageMsg = task.stage || task.status || '处理中'
        currentTask.value.progress = progress
        currentTask.value.progressText = `${stageMsg}... (${attempts * 2}秒)`
        currentTask.value.statusText = '正在生成中...'
      }
    } catch (err) {
      // Ignore polling errors, keep trying
      console.warn('轮询任务状态失败:', err.message)
    }
  }, 2000)
}

const pollMultiTasks = (taskIds) => {
  stopPolling()
  let attempts = 0
  const maxAttempts = 300
  const completedTasks = new Set()
  const failedTasks = new Set()

  pollTimer = setInterval(async () => {
    attempts++
    if (attempts > maxAttempts) {
      stopPolling()
      if (currentTask.value) {
        currentTask.value.status = currentTask.value.images.length > 0 ? 'completed' : 'error'
        currentTask.value.statusText = currentTask.value.images.length > 0
          ? `生成完成！共 ${currentTask.value.images.length} 张图片（部分超时）`
          : '生成超时'
        currentTask.value.error = currentTask.value.images.length > 0 ? '' : '任务超时，请重试'
        currentTask.value.progress = 100
      }
      isGenerating.value = false
      loadGallery()
      return
    }

    for (const taskId of taskIds) {
      if (completedTasks.has(taskId) || failedTasks.has(taskId)) continue
      try {
        const task = await api.getTaskStatus(taskId)
        const status = String(task?.status || '').toLowerCase()

        if (status === 'completed') {
          completedTasks.add(taskId)
          let images = []
          if (task.images) {
            images = typeof task.images === 'string' ? JSON.parse(task.images) : task.images
          } else if (task.result && Array.isArray(task.result)) {
            images = task.result.map(img => ({ url: img.url, alt: '生成的图像' }))
          }
          if (currentTask.value) {
            currentTask.value.images.push(...images)
          }
        } else if (status === 'failed' || status === 'error') {
          failedTasks.add(taskId)
        }
      } catch {}
    }

    const done = completedTasks.size + failedTasks.size
    const total = taskIds.length
    if (currentTask.value) {
      currentTask.value.progress = 25 + Math.round((done / total) * 75)
      currentTask.value.progressText = `已完成 ${completedTasks.size}/${total} 张`
      currentTask.value.statusText = `正在生成中... (${completedTasks.size}/${total})`
    }

    if (done >= total) {
      stopPolling()
      if (currentTask.value) {
        currentTask.value.status = completedTasks.size > 0 ? 'completed' : 'error'
        currentTask.value.statusText = completedTasks.size > 0
          ? `生成完成！共 ${currentTask.value.images.length} 张图片`
          : '全部生成失败'
        currentTask.value.error = completedTasks.size === 0 ? '图像生成失败，请重试' : ''
        currentTask.value.progress = 100
      }
      isGenerating.value = false
      loadGallery()
    }
  }, 2000)
}

const startBatchGeneration = async () => {
  if ((!promptInput.value.trim() && attachments.value.length === 0) || isGenerating.value) return
  isGenerating.value = true

  const typeLabel = imageTypes.value.find(t => t.value === selectedType.value)?.label || ''
  const styleLabel = imageStyles.value.find(s => s.value === selectedStyle.value)?.label || ''
  let fullPrompt = promptInput.value
  if (typeLabel) fullPrompt += `\n类型：${typeLabel}`
  if (styleLabel) fullPrompt += `\n风格：${styleLabel}`

  // Show progress card
  currentTask.value = {
    status: 'generating',
    statusText: '正在提交生成任务...',
    progress: 5,
    progressText: '提交中...',
    total: batchCount.value,
    images: [],
    prompt: promptInput.value,
    error: '',
  }

  try {
    // Upload files if any
    let uploadedFileUrls = []
    if (attachments.value.length > 0) {
      currentTask.value.progressText = '正在上传文件...'
      try {
        const uploadResults = await api.uploadFiles([...attachments.value], (progress, current, total) => {
          currentTask.value.progressText = `上传文件 (${current}/${total}) ${progress}%`
        })
        uploadedFileUrls = uploadResults.map(f => f.url).filter(Boolean)
        notification.success('文件上传成功', `已上传 ${uploadedFileUrls.length} 个文件`)
      } catch (e) {
        currentTask.value.status = 'error'
        currentTask.value.statusText = '文件上传失败'
        currentTask.value.error = e?.response?.data?.detail || e.message || '上传失败'
        isGenerating.value = false
        return
      }
    }

    // Remember uploaded file names for display
    const uploadedFileNames = attachments.value.map(f => f.name)

    // If files were uploaded, add reference instruction to prompt
    if (uploadedFileUrls.length > 0) {
      fullPrompt = `请参考我上传的图片/文件内容来生成图片。${fullPrompt}`
    }

    // Show uploaded info in progress card
    if (uploadedFileNames.length > 0) {
      currentTask.value.progressText = `已上传 ${uploadedFileNames.join(', ')}，正在提交...`
    }

    // 多图 = 发 N 次单图请求，走和首页一样的 assistant 工作流
    const taskIds = []
    for (let i = 0; i < batchCount.value; i++) {
      const itemPrompt = `${fullPrompt}\n这是第${i + 1}/${batchCount.value}张`
      // Build messages with file context so AI understands the reference
      const messages = []
      if (uploadedFileUrls.length > 0 && i === 0) {
        // First request: include file upload context message
        messages.push({ role: 'user', content: `我上传了以下文件作为参考：${uploadedFileNames.join('、')}，请基于文件内容来生成图片。` })
        messages.push({ role: 'assistant', content: '好的，我已收到您的文件，将基于文件内容为您生成图片。' })
      }
      messages.push({ role: 'user', content: itemPrompt })
      const chatRequest = {
        messages,
        session_id: `multi_${Date.now()}_${i}`,
        files: uploadedFileUrls.length > 0 ? uploadedFileUrls : undefined,
        model: generatorStore.selectedModelInfo?.model_name || generatorStore.model,
        model_type: 'image',
        image_params: {
          width: generatorStore.width,
          height: generatorStore.height,
          quality: generatorStore.quality,
          n: 1,
          model_name: generatorStore.model || undefined,
          provider: generatorStore.selectedModelInfo?.provider || undefined,
        }
      }
      try {
        const response = await api.assistantChat(chatRequest)
        const taskId = response.task_id || response.batch_id
        if (taskId) taskIds.push(taskId)
      } catch (e) {
        console.warn(`第${i + 1}张提交失败:`, e.message)
      }
      currentTask.value.progress = Math.round(((i + 1) / batchCount.value) * 20)
      currentTask.value.progressText = `已提交 ${i + 1}/${batchCount.value} 张...`
    }

    if (taskIds.length === 0) throw new Error('所有任务提交失败')

    currentTask.value.statusText = `正在生成 ${taskIds.length} 张图片...`
    currentTask.value.progress = 25
    currentTask.value.progressText = '等待生成结果...'
    pollMultiTasks(taskIds)
  } catch (err) {
    currentTask.value.status = 'error'
    currentTask.value.statusText = '提交失败'
    currentTask.value.error = err?.response?.data?.detail || err.message || '请稍后重试'
    isGenerating.value = false
  }
}

const loadGallery = async () => {
  try {
    const records = await api.getUnifiedGenerationHistory(6, 0, 'completed')
    galleryRecords.value = (records || []).filter(r => r.image_urls?.length > 0)
  } catch {
    try {
      const records = await api.getGenerationHistory(6, 0, 'completed')
      galleryRecords.value = (records || []).filter(r => r.image_urls?.length > 0)
    } catch { galleryRecords.value = [] }
  }
}

// 从后台加载类型和风格（与首页保持一致）
async function loadTypesStyles() {
  try {
    const res = await fetch('/api/v1/admin/system-config/types-styles')
    if (res.ok) {
      const data = await res.json()
      if (data.types?.length) imageTypes.value = data.types
      if (data.styles?.length) imageStyles.value = data.styles
    }
  } catch { /* 使用默认值 */ }
}

onMounted(() => { loadGallery(); loadTypesStyles() })
onUnmounted(() => { stopPolling() })
</script>

<style scoped>
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
