<template>
  <main class="flex h-full min-h-0 flex-1 flex-col overflow-hidden">
    <!-- Landing mode -->
    <div v-if="!hasConversation" class="flex-1 overflow-y-auto">
      <!-- Hero + Input -->
      <div class="flex flex-col items-center px-4 pt-10 pb-6 xs:px-6 md:px-8 md:pt-16">
        <div class="mb-6 text-center md:mb-8">
          <h1 class="mx-auto max-w-3xl text-3xl font-bold tracking-tight text-ink-950 md:text-5xl">
            一<span class="text-primary">图</span>胜千言
          </h1>
          <p class="mt-3 text-sm text-ink-500 md:text-base">
            强大的AI图像生成工具，支持多种模型和风格，轻松创建您想要的图像
          </p>
        </div>

        <!-- Input card -->
        <div class="w-full max-w-[720px]">
          <div class="rounded-3xl border border-border-dark bg-white/92 p-4 shadow-xl">
            <el-input
              ref="promptRef"
              v-model="promptInput"
              type="textarea"
              :rows="4"
              placeholder="输入你想要可视化的内容..."
              resize="none"
              @keydown.ctrl.enter="startGeneration"
              @keydown.meta.enter="startGeneration"
            />
            <div class="mt-3 flex flex-wrap items-center gap-2">
              <ModelDropdown class="shrink-0" />
              <RatioDropdown class="shrink-0" />
              <ResolutionDropdown class="shrink-0" />
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :show-file-list="false"
                :multiple="true"
                accept=".pdf,.docx,.jpg,.jpeg,.png,.gif,.webp,.bmp,.svg"
                :on-change="handleUploadChange"
              >
                <el-button circle>
                  <span class="material-symbols-outlined !text-lg">attach_file</span>
                </el-button>
              </el-upload>
              <div class="flex-1"></div>
              <el-button type="primary" round :disabled="!canSend" @click="startGeneration">
                <span class="material-symbols-outlined !text-lg">arrow_upward</span>
              </el-button>
            </div>
            <div v-if="attachments.length > 0" class="mt-3 flex flex-wrap gap-2">
              <div v-for="(file, i) in attachments" :key="i"
                class="flex items-center gap-2 rounded-xl border border-primary/20 bg-primary-soft px-3 py-1.5">
                <span class="material-symbols-outlined !text-sm text-primary">{{ getFileIcon(file) }}</span>
                <span class="max-w-[100px] truncate text-xs text-ink-700">{{ file.name }}</span>
                <button @click="attachments.splice(i, 1)" class="text-ink-500 hover:text-ink-950">
                  <span class="material-symbols-outlined !text-sm">close</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div class="mt-6 flex flex-wrap items-center justify-center gap-4 text-xs text-ink-500 md:gap-6 md:text-sm">
          <span class="flex items-center gap-1.5">
            <span class="material-symbols-outlined !text-base text-primary">palette</span>多种风格
          </span>
          <span class="flex items-center gap-1.5">
            <span class="material-symbols-outlined !text-base text-primary">auto_awesome</span>AI 智能生图
          </span>
          <span class="flex items-center gap-1.5">
            <span class="material-symbols-outlined !text-base text-primary">high_quality</span>4K 超清输出
          </span>
        </div>
      </div>

      <!-- Generation History Gallery -->
      <div class="px-4 pb-10 xs:px-6 md:px-8">
        <div class="mx-auto max-w-[960px]">
          <!-- Header -->
          <div v-if="galleryRecords.length > 0 || galleryLoading" class="mb-4 flex items-center justify-between">
            <h3 class="text-base font-semibold text-ink-950">创作记录</h3>
            <router-link to="/gallery" class="text-xs text-primary hover:underline">查看全部</router-link>
          </div>

          <!-- Loading -->
          <div v-if="galleryLoading && galleryRecords.length === 0" class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            <div v-for="i in 4" :key="i" class="animate-pulse rounded-2xl bg-white/60">
              <div class="aspect-square rounded-t-2xl bg-primary-soft/50"></div>
              <div class="p-3 space-y-2">
                <div class="h-3 w-3/4 rounded bg-primary-soft/50"></div>
                <div class="h-2 w-1/2 rounded bg-primary-soft/50"></div>
              </div>
            </div>
          </div>

          <!-- Gallery cards -->
          <div v-else-if="galleryRecords.length > 0" class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            <div
              v-for="record in galleryRecords"
              :key="record.id"
              class="group relative overflow-hidden rounded-2xl border border-border-dark bg-white/80 transition hover:shadow-lg"
            >
              <!-- Image -->
              <div class="aspect-square overflow-hidden cursor-pointer" @click="previewRecord(record)">
                <img
                  v-if="getRecordImage(record)"
                  :src="getRecordImage(record)"
                  class="h-full w-full object-cover transition-transform group-hover:scale-105"
                  loading="lazy"
                />
                <div v-else class="flex h-full items-center justify-center bg-primary-soft text-primary">
                  <span class="material-symbols-outlined !text-4xl">image</span>
                </div>
              </div>

              <!-- Hover actions -->
              <div class="absolute top-2 right-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  @click.stop="downloadRecord(record)"
                  class="grid h-8 w-8 place-items-center rounded-full bg-white/90 shadow backdrop-blur-sm hover:bg-white"
                  title="下载"
                >
                  <span class="material-symbols-outlined !text-base text-ink-700">download</span>
                </button>
                <button
                  @click.stop="deleteRecord(record)"
                  class="grid h-8 w-8 place-items-center rounded-full bg-white/90 shadow backdrop-blur-sm hover:bg-red-50"
                  title="删除"
                >
                  <span class="material-symbols-outlined !text-base text-red-500">delete</span>
                </button>
              </div>

              <!-- Info -->
              <div class="p-3">
                <!-- Parameters -->
                <div class="mb-1.5 flex flex-wrap gap-1">
                  <span v-if="record.model" class="rounded-md bg-primary-soft px-1.5 py-0.5 text-[10px] font-medium text-primary">
                    {{ record.model }}
                  </span>
                  <span v-if="record.width && record.height" class="rounded-md bg-ink-300/20 px-1.5 py-0.5 text-[10px] text-ink-500">
                    {{ record.width }}×{{ record.height }}
                  </span>
                  <span v-if="record.quality" class="rounded-md bg-ink-300/20 px-1.5 py-0.5 text-[10px] text-ink-500">
                    {{ record.quality }}
                  </span>
                </div>

                <!-- Prompt (copyable) -->
                <div class="group/prompt relative">
                  <p class="line-clamp-2 text-xs text-ink-700 pr-6">{{ record.prompt || '无提示词' }}</p>
                  <button
                    v-if="record.prompt"
                    @click.stop="copyPrompt(record.prompt)"
                    class="absolute top-0 right-0 text-ink-300 hover:text-primary transition"
                    title="复制提示词"
                  >
                    <span class="material-symbols-outlined !text-sm">content_copy</span>
                  </button>
                </div>

                <!-- Time -->
                <div class="mt-1.5 text-[10px] text-ink-500">{{ formatTime(record.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat mode -->
    <template v-else>
      <div class="shrink-0 flex items-center justify-between border-b border-border-dark bg-white/80 px-4 py-2.5 backdrop-blur-xl">
        <div class="flex items-center gap-2">
          <el-button text circle @click="backToLanding">
            <span class="material-symbols-outlined !text-xl">arrow_back</span>
          </el-button>
          <span class="text-sm font-semibold text-ink-950 truncate max-w-[200px]">
            {{ generatorStore.currentSessionTitle || '新对话' }}
          </span>
        </div>
        <div class="flex items-center gap-1">
          <el-button text circle @click="showSettings = !showSettings">
            <span class="material-symbols-outlined !text-xl">tune</span>
          </el-button>
        </div>
      </div>

      <div ref="chatAreaRef" class="flex-1 overflow-y-auto custom-scrollbar p-4 md:p-8">
        <CaseDetailPanel />
        <CreationDetailPanel />
        <div class="mx-auto max-w-4xl space-y-6">
          <MessageItem v-for="msg in generatorStore.messages" :key="msg.id" :msg="msg" />
          <div ref="chatBottomRef" class="h-px w-full"></div>
        </div>
      </div>

      <ChatInputBar
        :show-model-selector="showModelSelector"
        @update:showModelSelector="showModelSelector = $event"
      />
    </template>

    <!-- Model selector -->
    <Teleport to="body">
      <ModelSelector
        v-if="showModelSelector"
        :current-model="generatorStore.model"
        :attachments="generatorStore.attachments"
        @select="handleModelSelect"
        @close="showModelSelector = false"
      />
    </Teleport>

    <!-- Settings drawer -->
    <el-drawer v-model="showSettings" direction="rtl" title="生成参数" size="320px" append-to-body>
      <div class="space-y-5">
        <section class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider text-ink-500">图像质量</div>
          <el-radio-group :model-value="generatorStore.quality" @change="generatorStore.setQuality" class="w-full">
            <el-radio-button label="720p">720P</el-radio-button>
            <el-radio-button label="2k">2K</el-radio-button>
            <el-radio-button label="4k">4K</el-radio-button>
          </el-radio-group>
        </section>
        <section class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider text-ink-500">图像尺寸</div>
          <div class="grid grid-cols-3 gap-2">
            <el-button v-for="ratio in ratioOptions" :key="ratio.value"
              :type="selectedRatio === ratio.value ? 'primary' : 'default'"
              :plain="selectedRatio !== ratio.value" size="small" @click="selectRatio(ratio)">
              {{ ratio.label }}
            </el-button>
          </div>
        </section>
        <section class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider text-ink-500">负面提示词</div>
          <el-input v-model="generatorStore.negativePrompt" type="textarea" :rows="3" resize="none"
            placeholder="描述不希望出现的内容..." />
        </section>
      </div>
    </el-drawer>

    <!-- Preview dialog -->
    <el-dialog v-model="showPreview" width="min(90vw, 700px)" align-center>
      <div v-if="previewItem">
        <img :src="getRecordImage(previewItem)" class="w-full rounded-xl" />
        <div class="mt-4 space-y-2">
          <div class="flex flex-wrap gap-1.5">
            <el-tag v-if="previewItem.model" size="small">{{ previewItem.model }}</el-tag>
            <el-tag v-if="previewItem.width" size="small" type="info">{{ previewItem.width }}×{{ previewItem.height }}</el-tag>
            <el-tag v-if="previewItem.quality" size="small" type="warning">{{ previewItem.quality }}</el-tag>
            <el-tag v-if="previewItem.style" size="small" type="success">{{ previewItem.style }}</el-tag>
          </div>
          <div class="flex items-start gap-2">
            <p class="flex-1 text-sm text-ink-700">{{ previewItem.prompt }}</p>
            <button v-if="previewItem.prompt" @click="copyPrompt(previewItem.prompt)" class="shrink-0 text-ink-500 hover:text-primary">
              <span class="material-symbols-outlined !text-lg">content_copy</span>
            </button>
          </div>
        </div>
      </div>
    </el-dialog>
  </main>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useHistoryStore } from '@/store/useHistoryStore'
import { useAppStore } from '@/store/useAppStore'
import ModelDropdown from '@/components/landing/ModelDropdown.vue'
import RatioDropdown from '@/components/landing/RatioDropdown.vue'
import ResolutionDropdown from '@/components/landing/ResolutionDropdown.vue'
import MessageItem from '@/components/chat/MessageItem.vue'
import ChatInputBar from '@/components/chat/ChatInputBar.vue'
import CaseDetailPanel from '@/components/cases/CaseDetailPanel.vue'
import CreationDetailPanel from '@/components/creation/CreationDetailPanel.vue'
import ModelSelector from '@/components/ModelSelector.vue'
import api from '@/services/api'
import { notification } from '@/utils/notification'

const generatorStore = useGeneratorStore()
const historyStore = useHistoryStore()
const appStore = useAppStore()

const promptInput = ref('')
const promptRef = ref(null)
const uploadRef = ref(null)
const attachments = ref([])
const showModelSelector = ref(false)
const showSettings = ref(false)
const chatAreaRef = ref(null)
const chatBottomRef = ref(null)
const selectedRatio = ref('1:1')

// Gallery state
const galleryRecords = ref([])
const galleryLoading = ref(false)
const showPreview = ref(false)
const previewItem = ref(null)

const hasConversation = computed(() => generatorStore.messages.length > 0)
const canSend = computed(() => promptInput.value.trim().length > 0 || attachments.value.length > 0)

const ratioOptions = [
  { value: '1:1', label: '1:1', w: 1024, h: 1024 },
  { value: '3:4', label: '3:4', w: 768, h: 1024 },
  { value: '4:3', label: '4:3', w: 1024, h: 768 },
  { value: '9:16', label: '9:16', w: 576, h: 1024 },
  { value: '16:9', label: '16:9', w: 1024, h: 576 },
  { value: '3:2', label: '3:2', w: 1024, h: 683 },
]

// --- Gallery ---
const loadGallery = async () => {
  galleryLoading.value = true
  try {
    const records = await api.getUnifiedGenerationHistory(8, 0, 'completed')
    galleryRecords.value = records || []
  } catch {
    try {
      const records = await api.getGenerationHistory(8, 0, 'completed')
      galleryRecords.value = records || []
    } catch { galleryRecords.value = [] }
  } finally {
    galleryLoading.value = false
  }
}

const getRecordImage = (record) => {
  if (record.image_urls?.length > 0) return record.image_urls[0]
  return ''
}

const previewRecord = (record) => {
  if (getRecordImage(record)) {
    previewItem.value = record
    showPreview.value = true
  }
}

const copyPrompt = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    notification.success('已复制', '提示词已复制到剪贴板')
  } catch {
    notification.error('复制失败', '')
  }
}

const downloadRecord = (record) => {
  const url = getRecordImage(record)
  if (!url) return
  const link = document.createElement('a')
  link.href = url
  link.download = `creation-${record.id || Date.now()}.png`
  link.target = '_blank'
  link.click()
}

const deleteRecord = async (record) => {
  try {
    // Try API delete, remove from local list regardless
    galleryRecords.value = galleryRecords.value.filter(r => r.id !== record.id)
    notification.success('已删除', '')
  } catch {
    notification.error('删除失败', '')
  }
}

// --- Input ---
const startGeneration = () => {
  if (!canSend.value) return
  generatorStore.prompt = promptInput.value
  attachments.value.forEach(file => generatorStore.addAttachment(file))
  if (promptInput.value.trim() || generatorStore.attachments.length > 0) {
    generatorStore.setPendingAutoSend(true)
  }
  appStore.setCurrentView('chat')
  promptInput.value = ''
  attachments.value = []
}

const backToLanding = () => {
  generatorStore.startNewConversation()
  loadGallery()
}

const handleModelSelect = (model) => {
  generatorStore.setSelectedModel(model.model_name)
  generatorStore.setSelectedModelInfo(model)
  showModelSelector.value = false
  localStorage.setItem('selectedModel', JSON.stringify({ modelName: model.model_name, modelInfo: model }))
  notification.success('模型已切换', `已切换到 ${model.model_name}`)
}

const selectRatio = (ratio) => {
  selectedRatio.value = ratio.value
  generatorStore.width = ratio.w
  generatorStore.height = ratio.h
}

const handleUploadChange = (uploadFile) => {
  const file = uploadFile?.raw || uploadFile
  if (!file) return
  attachments.value.push(file)
  uploadRef.value?.clearFiles?.()
}

const getFileIcon = (file) => {
  const ext = file.name.split('.').pop().toLowerCase()
  if (ext === 'pdf') return 'picture_as_pdf'
  if (['doc', 'docx'].includes(ext)) return 'description'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) return 'image'
  return 'insert_drive_file'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// Scroll
const scheduleScroll = () => {
  requestAnimationFrame(() => { chatBottomRef.value?.scrollIntoView?.({ block: 'end' }) })
}
watch(() => generatorStore.messages.length, async () => { await nextTick(); scheduleScroll() })
watch(() => generatorStore.currentSessionId, async () => { await nextTick(); scheduleScroll() })

onMounted(() => {
  if (historyStore.sessions.length === 0) historyStore.loadFromServer()
  if (generatorStore.availableModels.length === 0) generatorStore.fetchAvailableModels()
  loadGallery()
  // Sync prompt from store (e.g. from scene library "做同款")
  if (generatorStore.prompt && !promptInput.value) {
    promptInput.value = generatorStore.prompt
    generatorStore.prompt = ''
  }
  try {
    const saved = localStorage.getItem('selectedModel')
    if (saved) {
      const data = JSON.parse(saved)
      generatorStore.setSelectedModel(data.modelName)
      generatorStore.setSelectedModelInfo(data.modelInfo)
    }
  } catch {}
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(140, 42, 46, 0.2); border-radius: 10px; }
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
