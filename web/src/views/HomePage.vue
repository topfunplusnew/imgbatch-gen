<template>
  <main class="flex h-full min-h-0 flex-1 flex-col overflow-hidden">
    <!-- Landing mode -->
    <div v-if="!hasConversation" class="flex-1 overflow-y-auto">
      <!-- Hero + Input -->
      <div class="flex flex-col items-center px-4 pt-8 pb-4 xs:px-6 md:px-8 md:pt-14">
        <div class="mb-5 text-center md:mb-7">
          <h1 class="mx-auto max-w-3xl text-3xl font-bold tracking-tight text-ink-950 md:text-5xl">
            一<span class="text-primary">图</span>胜千言
          </h1>
          <p class="mt-2 text-sm text-ink-500 md:text-base">
            一悟学舍，一键创图，AI 驱动，全场景省心之选
          </p>
        </div>

        <!-- Input card -->
        <div class="w-full max-w-[720px]">
          <div class="rounded-2xl border border-border-dark bg-white/95 p-4 shadow-[0_16px_48px_rgba(140,42,46,0.06)]">
            <el-input
              ref="promptRef"
              v-model="promptInput"
              type="textarea"
              :rows="3"
              placeholder="输入你想要可视化的内容..."
              resize="none"
              @keydown.ctrl.enter="startGeneration"
              @keydown.meta.enter="startGeneration"
            />
            <!-- Toolbar -->
            <div class="mt-2.5 flex flex-wrap items-center gap-1.5">
              <!-- Selected type/style tags -->
              <button v-if="homeSelectedType"
                class="inline-flex items-center gap-1 rounded-lg border border-primary/20 bg-primary/8 px-2.5 py-1.5 text-xs font-medium text-primary cursor-pointer hover:bg-primary/15"
                @click="homeSelectedType = ''">
                {{ homeTypeObj?.emoji }} {{ homeTypeObj?.label }}
                <span class="material-symbols-outlined !text-[11px] ml-0.5 opacity-50">close</span>
              </button>
              <button v-if="homeSelectedStyle"
                class="inline-flex items-center gap-1 rounded-lg border border-border-dark bg-white px-2.5 py-1.5 text-xs font-medium text-ink-700 cursor-pointer hover:bg-ink-300/10"
                @click="homeSelectedStyle = ''">
                {{ homeStyleObj?.label || homeSelectedStyle }}
                <span class="material-symbols-outlined !text-[11px] ml-0.5 opacity-50">close</span>
              </button>
              <RatioDropdown class="shrink-0" />
              <ResolutionDropdown class="shrink-0" />
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
              <ModelDropdown class="shrink-0" />
              <el-button type="primary" round size="small" :disabled="!canSend" @click="startGeneration" class="!px-4">
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

        <!-- Type/Style selector (like reference site) -->
        <div class="w-full max-w-[720px] mt-3">
          <div class="flex items-center gap-2 mb-2.5">
            <button @click="homeTab = 'type'"
              :class="['rounded-lg px-4 py-1.5 text-sm font-medium cursor-pointer',
                homeTab === 'type' ? 'bg-ink-950 text-white' : 'bg-white/80 text-ink-700 border border-border-dark hover:bg-white']">
              类型
            </button>
            <button @click="homeTab = 'style'"
              :class="['rounded-lg px-4 py-1.5 text-sm font-medium cursor-pointer',
                homeTab === 'style' ? 'bg-ink-950 text-white' : 'bg-white/80 text-ink-700 border border-border-dark hover:bg-white']">
              风格
            </button>
            <span class="material-symbols-outlined !text-lg text-ink-400 cursor-pointer" @click="showHomeTypePanel = !showHomeTypePanel">
              {{ showHomeTypePanel ? 'expand_less' : 'expand_more' }}
            </span>
          </div>
          <div v-show="showHomeTypePanel">
            <!-- 类型：有封面图用卡片，无封面图用文字标签 -->
            <div v-if="homeTab === 'type'">
              <div v-if="homeTypesHasCover" class="grid grid-cols-3 gap-2.5 xs:grid-cols-4 md:grid-cols-5">
                <button v-for="t in homeTypes" :key="t.value"
                  @click="homeSelectedType = homeSelectedType === t.value ? '' : t.value"
                  class="relative flex flex-col items-center cursor-pointer group">
                  <div :class="['w-full overflow-hidden rounded-xl border-2',
                    homeSelectedType === t.value ? 'border-primary' : 'border-transparent hover:border-primary/30']">
                    <div class="overflow-hidden bg-primary-soft/10 rounded-xl">
                      <img v-if="t.cover" :src="t.cover" :alt="t.label"
                        class="w-full h-auto object-contain group-hover:scale-105 transition-transform duration-300" loading="lazy" />
                      <div v-else class="w-full aspect-square flex items-center justify-center text-sm font-bold text-ink-400">{{ t.label }}</div>
                    </div>
                  </div>
                  <div v-if="homeSelectedType === t.value"
                    class="absolute top-1.5 right-1.5 grid h-5 w-5 place-items-center rounded-full bg-primary text-white">
                    <span class="material-symbols-outlined !text-xs">check</span>
                  </div>
                  <span class="mt-1 text-xs text-ink-700 font-medium">{{ t.label }}</span>
                </button>
              </div>
              <div v-else class="flex flex-wrap gap-2">
                <button v-for="t in homeTypes" :key="t.value"
                  @click="homeSelectedType = homeSelectedType === t.value ? '' : t.value"
                  :class="['rounded-lg border px-3 py-1.5 text-xs font-medium cursor-pointer',
                    homeSelectedType === t.value ? 'border-primary bg-primary/8 text-primary' : 'border-border-dark bg-white text-ink-700 hover:border-primary/30']">
                  {{ t.label }}
                </button>
              </div>
            </div>
            <!-- 风格：带封面图卡片 -->
            <div v-if="homeTab === 'style'" class="grid grid-cols-3 gap-2.5 xs:grid-cols-4 md:grid-cols-5">
              <button v-for="s in homeStyles" :key="s.value"
                @click="homeSelectedStyle = homeSelectedStyle === s.value ? '' : s.value"
                class="relative flex flex-col items-center cursor-pointer group">
                <div :class="['w-full overflow-hidden rounded-xl border-2',
                  homeSelectedStyle === s.value ? 'border-primary' : 'border-transparent hover:border-primary/30']">
                  <div class="overflow-hidden bg-primary-soft/10 rounded-xl">
                    <img :src="s.cover" :alt="s.label"
                      class="w-full h-auto object-contain group-hover:scale-105 transition-transform duration-300" loading="lazy" />
                  </div>
                </div>
                <div v-if="homeSelectedStyle === s.value"
                  class="absolute top-1.5 right-1.5 grid h-5 w-5 place-items-center rounded-full bg-primary text-white">
                  <span class="material-symbols-outlined !text-xs">check</span>
                </div>
                <span :class="['mt-1.5 text-xs font-medium',
                  homeSelectedStyle === s.value ? 'text-primary' : 'text-ink-700']">{{ s.label }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Gallery -->
      <div class="px-4 pb-10 xs:px-6 md:px-8">
        <div class="w-full">
          <div class="mb-3 flex items-center justify-between">
            <h3 class="text-lg font-bold text-ink-950">画廊</h3>
            <router-link v-if="galleryRecords.length > 0" to="/gallery" class="text-xs text-primary hover:underline">查看全部</router-link>
          </div>

          <!-- Loading -->
          <div v-if="galleryLoading && galleryRecords.length === 0" class="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
            <div v-for="i in 4" :key="i" class="animate-pulse rounded-xl bg-white/60">
              <div class="aspect-square rounded-t-xl bg-primary-soft/30"></div>
              <div class="p-2.5 space-y-1.5">
                <div class="h-3 w-3/4 rounded bg-primary-soft/30"></div>
                <div class="h-2 w-1/2 rounded bg-primary-soft/30"></div>
              </div>
            </div>
          </div>

          <!-- Gallery cards -->
          <div v-else-if="galleryRecords.length > 0" class="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
            <div
              v-for="record in galleryRecords"
              :key="record.id"
              class="group relative cursor-pointer overflow-hidden rounded-xl border border-border-dark bg-white/90 shadow-sm hover:shadow-lg hover:-translate-y-0.5"
            >
              <div class="aspect-square overflow-hidden" @click="previewRecord(record)">
                <img v-if="getRecordImage(record)" :src="getRecordImage(record)"
                  class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" />
                <div v-else class="flex h-full items-center justify-center bg-primary-soft text-primary">
                  <span class="material-symbols-outlined !text-4xl">image</span>
                </div>
              </div>
              <!-- Hover actions -->
              <div class="absolute top-1.5 right-1.5 flex gap-1 opacity-0 group-hover:opacity-100">
                <button @click.stop="downloadRecord(record)"
                  class="grid h-7 w-7 place-items-center rounded-full bg-white/90 shadow backdrop-blur-sm hover:bg-white cursor-pointer">
                  <span class="material-symbols-outlined !text-sm text-ink-700">download</span>
                </button>
                <button @click.stop="deleteRecord(record)"
                  class="grid h-7 w-7 place-items-center rounded-full bg-white/90 shadow backdrop-blur-sm hover:bg-red-50 cursor-pointer">
                  <span class="material-symbols-outlined !text-sm text-red-500">delete</span>
                </button>
              </div>
              <div class="p-2.5">
                <div class="group/prompt relative">
                  <p class="line-clamp-2 text-xs text-ink-700 pr-5">{{ displayPromptOrFallback(record.prompt) }}</p>
                  <button v-if="extractDisplayPrompt(record.prompt)" @click.stop="copyPrompt(record.prompt)"
                    class="absolute top-0 right-0 text-ink-300 hover:text-primary cursor-pointer">
                    <span class="material-symbols-outlined !text-sm">content_copy</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-else>
            <div class="rounded-xl border border-dashed border-border-dark bg-white/60 p-6">
              <div class="mt-4 text-center">
                <span class="material-symbols-outlined !text-3xl text-ink-300">auto_awesome</span>
                <p class="mt-1.5 text-sm font-medium text-ink-700">暂无作品</p>
                <p class="mt-0.5 text-xs text-ink-500">在上方输入内容，创建你的第一个知识可视化作品</p>
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
            <p class="flex-1 text-sm text-ink-700">{{ displayPromptOrFallback(previewItem.prompt) }}</p>
            <button v-if="extractDisplayPrompt(previewItem.prompt)" @click="copyPrompt(previewItem.prompt)" class="shrink-0 text-ink-500 hover:text-primary">
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
import ModelDropdown from '@/components/landing/ModelDropdown.vue'
import RatioDropdown from '@/components/landing/RatioDropdown.vue'
import ResolutionDropdown from '@/components/landing/ResolutionDropdown.vue'
import MessageItem from '@/components/chat/MessageItem.vue'
import ChatInputBar from '@/components/chat/ChatInputBar.vue'
import CaseDetailPanel from '@/components/cases/CaseDetailPanel.vue'
import CreationDetailPanel from '@/components/creation/CreationDetailPanel.vue'
import ModelSelector from '@/components/ModelSelector.vue'
import { api } from '@/services/api'
import { notification } from '@/utils/notification'
import { copyText } from '@/utils/clipboard'
import { DEFAULT_IMAGE_MODEL, pickPreferredFrontendModel } from '@/utils/modelSelection'
import { extractDisplayPrompt, displayPromptOrFallback } from '@/utils/promptDisplay'

const generatorStore = useGeneratorStore()
const historyStore = useHistoryStore()

const promptInput = ref('')
const promptRef = ref(null)
const uploadRef = ref(null)
const attachments = ref([])
const showModelSelector = ref(false)
const showSettings = ref(false)
const chatAreaRef = ref(null)
const chatBottomRef = ref(null)
const selectedRatio = ref('auto')

// Type/Style selector state
const homeTab = ref('type')
const showHomeTypePanel = ref(false)
const homeSelectedType = ref('')
const homeSelectedStyle = ref('')

// 类型：纯文字标签（不带图片）
const homeTypes = ref([])

// 风格：带封面图
const homeStyles = ref([])

const homeTypeObj = computed(() => homeTypes.value.find(t => t.value === homeSelectedType.value))
const homeStyleObj = computed(() => homeStyles.value.find(s => s.value === homeSelectedStyle.value))
const homeTypesHasCover = computed(() => homeTypes.value.some(t => t.cover))

// 从后台加载类型和风格
async function loadTypesStyles() {
  try {
    const res = await fetch('/api/v1/admin/system-config/types-styles')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const data = await res.json()
    homeTypes.value = Array.isArray(data.types) ? data.types : []
    homeStyles.value = Array.isArray(data.styles) ? data.styles : []
  } catch {
    homeTypes.value = []
    homeStyles.value = []
  }
}

// Gallery state
const galleryRecords = ref([])
const galleryLoading = ref(false)
const showPreview = ref(false)
const previewItem = ref(null)

const hasConversation = computed(() => generatorStore.messages.length > 0 || generatorStore.pendingAutoSend)
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
  const ok = await copyText(extractDisplayPrompt(text))
  if (ok) {
    notification.success('已复制', '提示词已复制到剪贴板')
  } else {
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
  // Build prompt with selected type/style
  let fullPrompt = promptInput.value
  if (homeTypeObj.value) fullPrompt += `\n类型：${homeTypeObj.value.label}`
  if (homeStyleObj.value) fullPrompt += `\n风格：${homeStyleObj.value.label}`
  generatorStore.prompt = fullPrompt
  attachments.value.forEach(file => generatorStore.addAttachment(file))
  if (fullPrompt.trim() || generatorStore.attachments.length > 0) {
    generatorStore.setPendingAutoSend(true)
  }
  promptInput.value = ''
  attachments.value = []
}

const backToLanding = () => {
  generatorStore.startNewConversation()
  applyHomeDefaultModel()
  loadGallery()
}

const handleModelSelect = (model) => {
  generatorStore.setSelectedModel(model.model_name)
  generatorStore.setSelectedModelInfo(model)
  showModelSelector.value = false
  localStorage.setItem('selectedModel', JSON.stringify({ modelName: model.model_name, modelInfo: model }))
  notification.success('模型已切换', `已切换到 ${model.model_name}`)
}

const applyHomeDefaultModel = () => {
  const pinnedModelName = generatorStore.consumeNextPreferredModel()
  const preferredModel = pinnedModelName
    ? generatorStore.availableModels.find((model) => model.model_name === pinnedModelName) || pickPreferredFrontendModel(generatorStore.availableModels)
    : pickPreferredFrontendModel(generatorStore.availableModels)
  const nextModelName = pinnedModelName || preferredModel?.model_name || DEFAULT_IMAGE_MODEL

  generatorStore.setSelectedModel(nextModelName)
  generatorStore.setSelectedModelInfo(preferredModel || null)
  localStorage.setItem('selectedModel', JSON.stringify({ modelName: nextModelName, modelInfo: preferredModel || null }))
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

onMounted(async () => {
  if (historyStore.sessions.length === 0) historyStore.loadFromServer()
  if (generatorStore.availableModels.length === 0) await generatorStore.fetchAvailableModels()
  loadGallery()
  loadTypesStyles()
  if (!hasConversation.value) applyHomeDefaultModel()
  // Sync prompt from store (e.g. from scene library "做同款")
  if (generatorStore.prompt && !promptInput.value) {
    promptInput.value = generatorStore.prompt
    generatorStore.prompt = ''
  }
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(140, 42, 46, 0.2); border-radius: 10px; }
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
