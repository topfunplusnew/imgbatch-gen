<template>
  <div class="max-w-full md:max-w-4xl mx-auto flex gap-2 md:gap-4" :class="{ 'flex-row-reverse': msg.role === 'user' }">
    <!-- 头像/图标 -->
    <div class="size-8 rounded flex items-center justify-center shrink-0"
         :class="msg.role === 'user' ? 'bg-white border border-border-dark' : 'bg-primary/10 border border-primary/20'">
      <span class="material-symbols-outlined !text-sm"
            :class="msg.role === 'user' ? 'text-ink-700' : 'text-primary'">
        {{ msg.role === 'user' ? 'person' : 'auto_awesome' }}
      </span>
    </div>

    <div class="flex-1">
      <div class="text-sm font-bold mb-1" :class="{ 'text-right': msg.role === 'user' }">
        {{ msg.role === 'user' ? '您' : 'AI 助手' }}
        <span v-if="msg.role === 'assistant'" class="text-[10px] font-normal text-ink-500 ml-2">v2.4.0</span>
      </div>

      <!-- Thinking/Loading Animation - 当 AI 正在思考时显示 -->
      <div
        v-if="msg.role === 'assistant' && msg.status === 'processing' && !msg.content"
        :class="[
          'leading-relaxed mb-2 px-3 xs:px-4 py-2.5 xs:py-3 rounded-2xl block text-left',
          'bg-primary/10 text-ink-950 border border-primary/20 max-w-[90%] xs:max-w-[85%] sm:max-w-[80%]'
        ]">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-1.5">
            <span class="thinking-dot w-2 h-2 bg-primary rounded-full"></span>
            <span class="thinking-dot w-2 h-2 bg-primary rounded-full"></span>
            <span class="thinking-dot w-2 h-2 bg-primary rounded-full"></span>
          </div>
          <span class="text-ink-700 text-sm">AI 正在思考...</span>
        </div>
      </div>

      <!-- 文本内容 -->
      <div v-if="msg.content"
           :class="[
             'leading-relaxed mb-2 px-3 xs:px-4 py-2.5 xs:py-3 rounded-2xl block text-left',
             'text-sm xs:text-base md:text-base',
             msg.role === 'user'
               ? 'bg-white text-ink-950 border border-primary/20 shadow-sm ml-auto max-w-[90%] xs:max-w-[85%] sm:max-w-[80%]'
               : getStatusClasses(msg.status) + ' max-w-[90%] xs:max-w-[85%] sm:max-w-[80%]'
           ]">
        <span v-if="msg.role === 'assistant'" class="markdown-body" v-html="renderMarkdown(msg.content)"></span>
        <!-- 流式输出时的闪烁光标 -->
        <span
          v-if="msg.role === 'assistant' && msg.status === 'processing' && msg.content"
          class="inline-block w-0.5 h-4 bg-primary ml-0.5 animate-pulse rounded-sm align-middle">
        </span>
        <template v-else-if="msg.role === 'user'">{{ msg.content }}</template>
      </div>

      <!-- Message Action Bar - Only for assistant messages (outside the bubble) -->
      <div v-if="msg.role === 'assistant'" class="mt-2">
        <!-- Action buttons container -->
        <div class="flex items-center gap-1.5 flex-wrap">

            <!-- Copy button -->
            <button
              v-if="msg.content"
              @click="copyContent"
              class="inline-flex items-center gap-1.5 px-2 py-1.5 bg-white/90 hover:bg-primary/5 text-ink-500 hover:text-ink-950 border border-border-dark rounded-lg text-xs transition-colors"
              title="复制内容">
              <span class="material-symbols-outlined !text-base">
                {{ copied ? 'check' : 'content_copy' }}
              </span>
            </button>

            <!-- Like button -->
            <button
              @click="toggleLike"
              class="inline-flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs transition-colors"
              :class="isLiked
                ? 'bg-primary/10 text-primary border-2 border-primary/30'
                : 'bg-white/90 text-ink-500 hover:bg-pink-50 hover:text-pink-600 border border-border-dark'"
              title="喜欢">
              <span class="material-symbols-outlined !text-base">thumb_up</span>
            </button>

            <!-- Dislike button -->
            <button
              @click="toggleDislike"
              class="inline-flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs transition-colors"
              :class="isDisliked
                ? 'bg-red-500/10 text-red-600 border-2 border-red-500/30'
                : 'bg-white/90 text-ink-500 hover:bg-red-50 hover:text-red-600 border border-border-dark'"
              title="不喜欢">
              <span class="material-symbols-outlined !text-base">thumb_down</span>
            </button>

            <!-- Share button -->
            <button
              @click="shareMessage"
              class="inline-flex items-center gap-1.5 px-2 py-1.5 bg-white/90 hover:bg-primary/5 text-ink-500 hover:text-ink-950 border border-border-dark rounded-lg text-xs transition-colors"
              title="分享对话">
              <span class="material-symbols-outlined !text-base">share</span>
            </button>

            <!-- Quote button -->
            <button
              v-if="msg.content"
              @click="quoteMessage"
              class="inline-flex items-center gap-1.5 px-2 py-1.5 bg-white/90 hover:bg-primary/5 text-ink-500 hover:text-ink-950 border border-border-dark rounded-lg text-xs transition-colors"
              title="引用">
              <span class="material-symbols-outlined !text-base">format_quote</span>
            </button>

            <!-- Retry button (only shows on error/timeout) -->
            <button
              v-if="msg.status === 'error' || msg.status === 'timeout'"
              @click="retryMessage"
              class="inline-flex items-center gap-1.5 px-2 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 border border-amber-500/30 rounded-lg text-xs transition-colors"
              title="重试">
              <span class="material-symbols-outlined !text-base">refresh</span>
            </button>

            <!-- Model Toggle Dropdown -->
            <div class="relative" data-model-dropdown>
              <button
                @click="toggleModelDropdown"
                class="inline-flex items-center gap-1.5 px-2 py-1.5 bg-white/90 hover:bg-primary/5 text-ink-500 hover:text-ink-950 border border-border-dark rounded-lg text-xs transition-colors"
                title="切换模型">
                <span class="material-symbols-outlined !text-base">auto_awesome</span>
                <span class="material-symbols-outlined !text-sm" :class="showModelDropdown ? 'rotate-180' : ''">expand_more</span>
              </button>

              <transition
                enter-active-class="transition ease-out duration-200"
                enter-from-class="opacity-0 scale-95 translate-y-2"
                enter-to-class="opacity-100 scale-100 translate-y-0"
                leave-active-class="transition ease-in duration-150"
                leave-from-class="opacity-100 scale-100 translate-y-0"
                leave-to-class="opacity-0 scale-95 translate-y-2">
                <div
                  v-if="showModelDropdown"
                  class="absolute top-full left-0 mt-2 bg-white rounded-xl shadow-xl border border-border-dark overflow-hidden z-20 min-w-[200px]">
                  <div class="py-1">
                    <button
                      v-for="model in availableModels"
                      :key="model.model_name"
                      @click="selectModel(model)"
                      class="w-full px-4 py-2.5 text-left text-sm flex items-center gap-2 transition-colors"
                      :class="generatorStore.model === model.model_name
                        ? 'bg-primary/10 text-primary font-medium'
                        : 'text-ink-700 hover:bg-primary/5'">
                      <span class="material-symbols-outlined !text-lg">
                        {{ generatorStore.model === model.model_name ? 'check_circle' : 'radio_button_unchecked' }}
                      </span>
                      <div class="flex-1">
                        <p class="font-medium">{{ model.display_name || model.model_name }}</p>
                        <p class="text-xs text-ink-500">{{ model.provider }}</p>
                      </div>
                    </button>
                  </div>
                </div>
              </transition>
            </div>
          </div>

        <transition name="status-card">
          <div v-if="progressCard" class="mt-3">
            <div
              class="status-card relative overflow-hidden rounded-[1.25rem] border px-3 py-3 sm:px-4"
              :class="statusCardThemeClass"
            >
              <div v-if="isProgressActive" class="status-card__ambient"></div>

              <div class="relative flex items-start gap-3">
                <div class="status-card__badge" :class="statusBadgeThemeClass">
                  <span
                    class="material-symbols-outlined !text-lg"
                    :class="{ 'status-card__icon-spin': isProgressActive }"
                  >
                    {{ progressCard.icon }}
                  </span>
                </div>

                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="text-sm font-semibold text-ink-950">{{ progressCard.title }}</span>
                    <span class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="statusTagThemeClass">
                      {{ progressCard.tag }}
                    </span>
                    <div v-if="isProgressActive" class="loading-dots" aria-hidden="true">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>

                  <p class="mt-1 text-xs leading-relaxed text-ink-500 sm:text-sm">
                    {{ progressCard.message }}
                  </p>

                  <div class="mt-3">
                    <div class="status-card__progress-track">
                      <div
                        class="status-card__progress-fill"
                        :class="progressFillThemeClass"
                        :style="{ width: `${progressCard.percent}%` }"
                      >
                        <span v-if="isProgressActive" class="status-card__progress-shine"></span>
                      </div>
                    </div>
                    <div class="mt-2 flex items-center justify-between text-[11px] font-medium text-ink-500">
                      <span>{{ progressCard.caption }}</span>
                      <span class="text-ink-700">{{ progressCard.percent }}%</span>
                    </div>
                  </div>

                  <div v-if="progressStatChips.length > 0" class="mt-3 flex flex-wrap gap-2">
                    <div
                      v-for="chip in progressStatChips"
                      :key="chip.label"
                      class="status-chip"
                    >
                      <span class="text-[10px] uppercase tracking-[0.12em] text-ink-400">{{ chip.label }}</span>
                      <span class="text-xs font-semibold text-ink-700">{{ chip.value }}</span>
                    </div>
                  </div>

                  <div v-if="progressStagePills.length > 0" class="mt-3 flex flex-wrap gap-2">
                    <div
                      v-for="item in progressStagePills"
                      :key="`${item.stage}-${item.countText}`"
                      class="stage-pill"
                      :class="{
                        'stage-pill--active': item.isActive,
                        'stage-pill--done': item.isDone,
                        'stage-pill--error': item.isError
                      }"
                    >
                      <span class="material-symbols-outlined !text-sm">{{ item.icon }}</span>
                      <span class="font-medium">{{ item.label }}</span>
                      <span v-if="item.countText">{{ item.countText }}</span>
                    </div>
                  </div>

                  <div v-if="progressTimeline.length > 0" class="mt-3 space-y-2">
                    <div
                      v-for="event in progressTimeline"
                      :key="`${event.stage}-${event.timestamp || event.label}`"
                      class="timeline-item"
                      :class="{ 'timeline-item--active': event.isActive }"
                    >
                      <span class="timeline-item__dot"></span>
                      <div class="min-w-0 flex-1">
                        <div class="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                          <span class="text-xs font-semibold text-ink-700">{{ event.label }}</span>
                          <span class="text-[10px] text-ink-400">{{ event.progressPercent }}%</span>
                          <span v-if="event.timestamp" class="text-[10px] text-ink-400">{{ event.timestamp }}</span>
                        </div>
                        <p class="mt-0.5 text-[11px] leading-relaxed text-ink-500">{{ event.message }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- 单张图片 -->
      <div
        v-if="imageAttachments.length > 0 || fileAttachments.length > 0"
        :class="[
          'mt-3 space-y-3',
          msg.role === 'user' ? 'ml-auto max-w-[90%] xs:max-w-[85%] sm:max-w-[80%]' : 'max-w-[90%] xs:max-w-[85%] sm:max-w-[80%]'
        ]"
      >
        <div v-if="imageAttachments.length > 0" class="grid grid-cols-2 md:grid-cols-3 gap-2">
          <div
            v-for="(file, index) in imageAttachments"
            :key="`att-image-${index}`"
            class="relative group aspect-square rounded-xl overflow-hidden border border-border-dark bg-white cursor-zoom-in"
            @click="openAttachmentPreview(index)"
          >
            <img
              :src="getFileUrl(file)"
              :alt="getAttachmentName(file)"
              class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
            >
            <div class="absolute inset-0 bg-gradient-to-t from-black/55 via-black/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100">
              <div class="absolute left-2 top-2 rounded-full bg-black/45 px-2 py-1 text-[11px] text-white backdrop-blur-sm">
                点击预览
              </div>
            </div>
            <button
              @click.stop="downloadAttachment(file)"
              :disabled="!getFileUrl(file)"
              class="absolute right-2 bottom-2 p-1.5 rounded-lg bg-black/45 hover:bg-black/60 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title="下载图片附件"
            >
              <span class="material-symbols-outlined !text-sm">download</span>
            </button>
          </div>
        </div>

        <div v-if="fileAttachments.length > 0" class="space-y-2">
          <button
            v-for="(file, index) in fileAttachments"
            :key="`att-file-${index}`"
            @click="downloadAttachment(file)"
            :disabled="!getFileUrl(file)"
            class="w-full flex items-center gap-3 px-3 py-2 rounded-xl border border-border-dark bg-white text-left hover:bg-primary/5 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            <span class="material-symbols-outlined !text-lg text-primary">
              {{ getAttachmentIcon(file) }}
            </span>
            <div class="min-w-0 flex-1">
              <p class="text-sm text-ink-950 truncate">{{ getAttachmentName(file) }}</p>
              <p class="text-xs text-ink-500">{{ formatAttachmentSize(file) }}</p>
            </div>
            <span class="material-symbols-outlined !text-base text-ink-500">download</span>
          </button>
        </div>
      </div>

      <div v-if="msg.images && msg.images.length === 1" class="mt-3">
        <div
          class="relative group max-w-xs md:max-w-md w-full cursor-zoom-in"
          @click="openGeneratedImagePreview(0)"
        >
          <img
            :src="getImageUrl(msg.images[0], true)"
            :alt="typeof msg.images[0] === 'object' ? msg.images[0].alt : '生成的图像'"
            class="w-full rounded-xl shadow-lg transition-transform duration-300 group-hover:scale-[1.01]">
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-xl">
            <div class="absolute bottom-3 left-3 right-3 flex items-center justify-between">
              <p class="text-sm text-white truncate">{{ typeof msg.images[0] === 'object' ? (msg.images[0].alt || '生成的图像') : '生成的图像' }}</p>
              <div class="flex items-center gap-2">
                <button
                  @click.stop="openGeneratedImagePreview(0)"
                  class="p-2 bg-white/20 hover:bg-white/30 rounded-lg backdrop-blur-sm transition-colors"
                  title="预览图片">
                  <span class="material-symbols-outlined !text-lg text-white">zoom_in</span>
                </button>
                <button
                  @click.stop="downloadSingleImage(msg.images[0])"
                  class="p-2 bg-white/20 hover:bg-white/30 rounded-lg backdrop-blur-sm transition-colors"
                  title="下载图片">
                  <span class="material-symbols-outlined !text-lg text-white">download</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 多张图片（批量结果） -->
      <div v-if="msg.images && msg.images.length > 1">
        <!-- 批量下载按钮 -->
        <div class="mb-3 flex items-center justify-between">
          <span class="text-sm text-slate-500">共 {{ msg.images.length }} 张图片</span>
          <button
            @click="downloadAllImages"
            :disabled="isDownloading"
            class="flex items-center gap-2 px-4 py-2 bg-primary-strong text-white rounded-lg text-sm hover:bg-primary-deep disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            <span class="material-symbols-outlined !text-lg">{{ isDownloading ? 'downloading' : 'download' }}</span>
            {{ isDownloading ? '下载中...' : '下载全部' }}
          </button>
        </div>

        <!-- 图片网格 -->
        <div class="grid grid-cols-1 xs:grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 xs:gap-3 md:gap-4">
          <div
            v-for="(image, index) in msg.images"
            :key="index"
            class="relative group aspect-square bg-white rounded-xl overflow-hidden border border-border-dark shadow-lg hover:shadow-xl transition-shadow cursor-zoom-in"
            @click="openGeneratedImagePreview(index)"
          >
            <img
              :src="getImageUrl(image, true)"
              :alt="typeof image === 'object' ? (image.alt || `图片 ${index + 1}`) : `图片 ${index + 1}`"
              class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105">
            <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
              <div class="absolute bottom-2 left-2 right-2 flex items-center justify-between">
                <p class="text-xs text-white truncate">{{ typeof image === 'object' ? (image.alt || `图片 ${index + 1}`) : `图片 ${index + 1}` }}</p>
                <div class="flex items-center gap-1.5">
                  <button
                    @click.stop="openGeneratedImagePreview(index)"
                    class="p-1.5 bg-white/20 hover:bg-white/30 rounded-lg backdrop-blur-sm transition-colors"
                    title="预览此图片"
                  >
                    <span class="material-symbols-outlined !text-base text-white">zoom_in</span>
                  </button>
                  <button
                    @click.stop="downloadSingleImage(image)"
                    class="p-1.5 bg-white/20 hover:bg-white/30 rounded-lg backdrop-blur-sm transition-colors"
                    title="下载此图片">
                    <span class="material-symbols-outlined !text-base text-white">download</span>
                  </button>
                </div>
              </div>
            </div>
            <!-- 下载进度 -->
            <div v-if="downloadProgress[index] !== undefined" class="absolute inset-0 bg-black/70 flex items-center justify-center">
              <div class="text-center">
                <span class="material-symbols-outlined !text-3xl text-white animate-spin">downloading</span>
                <p class="text-xs text-white mt-2">{{ downloadProgress[index] }}%</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ImagePreviewModal ref="imagePreviewModalRef" @download="handlePreviewDownload" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import { notification } from '@/utils/notification'
import { useApiConfigStore } from '@/store/useApiConfigStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { api } from '@/services/api'
import ImagePreviewModal from '@/components/ImagePreviewModal.vue'

const apiConfigStore = useApiConfigStore()
const generatorStore = useGeneratorStore()

// 渲染 markdown
function renderMarkdown(content) {
  if (!content) return ''
  return marked.parse(content)
}

const props = defineProps({
  msg: {
    type: Object,
    required: true,
    validator: (value) => {
      return ['user', 'assistant'].includes(value.role) &&
          (typeof value.content === 'string' || Array.isArray(value.images));
    }
  },
})

const emit = defineEmits(['retry'])

const isDownloading = ref(false)
const downloadProgress = ref({})
const copied = ref(false)
const imagePreviewModalRef = ref(null)

// Message interaction state
const isLiked = ref(false)
const isDisliked = ref(false)
const showModelDropdown = ref(false)

// Get available models from generator store (empty array if not available yet)
const availableModels = computed(() => {
  return generatorStore.availableModels || []
})

const messageFiles = computed(() => (Array.isArray(props.msg.files) ? props.msg.files : []))
const imageAttachments = computed(() => messageFiles.value.filter((file) => isImageAttachment(file)))
const fileAttachments = computed(() => messageFiles.value.filter((file) => !isImageAttachment(file)))
const previewableGeneratedImages = computed(() =>
  (Array.isArray(props.msg.images) ? props.msg.images : [])
    .map((image, index) => normalizePreviewImage(image, index))
    .filter((image) => image.url)
)
const previewableAttachmentImages = computed(() =>
  imageAttachments.value
    .map((file, index) => ({
      url: getFileUrl(file),
      alt: getAttachmentName(file) || `图片附件 ${index + 1}`,
    }))
    .filter((image) => image.url)
)
const generationProgress = computed(() => props.msg?.generationProgress || null)
const batchProgressPercent = computed(() => {
  const explicitPercent = Number(props.msg?.batchProgress?.progressPercent)
  if (Number.isFinite(explicitPercent)) {
    return Math.max(0, Math.min(100, Math.round(explicitPercent)))
  }
  const total = Number(props.msg?.batchProgress?.total || 0)
  const completed = Number(props.msg?.batchProgress?.completed || 0)
  if (!Number.isFinite(total) || total <= 0) return 0
  return Math.max(0, Math.min(100, Math.round(completed / total * 100)))
})
const normalizedBatchStageOverview = computed(() =>
  Array.isArray(props.msg?.batchProgress?.stageOverview)
    ? props.msg.batchProgress.stageOverview.filter((item) => item && item.count > 0)
    : []
)
const progressCard = computed(() => {
  if (props.msg.role !== 'assistant') return null

  if (props.msg?.batchProgress) {
    const batchProgress = props.msg.batchProgress
    const total = Number(batchProgress.total || 0)
    const completed = Number(batchProgress.completed || 0)
    return {
      mode: 'batch',
      stage: String(batchProgress.stage || ''),
      title: batchProgress.stageLabel || '批量任务处理中',
      message: batchProgress.stageMessage || props.msg.content || '正在处理批量生图任务',
      percent: batchProgressPercent.value,
      icon: getStageIcon(batchProgress.stage),
      caption: total > 0 ? `已完成 ${completed}/${total}` : '等待进度回传',
      tag: resolveProgressTag('batch'),
    }
  }

  if (generationProgress.value) {
    const currentProgress = generationProgress.value
    const totalStages = Number(currentProgress.totalStages || 0)
    const stageIndex = Number(currentProgress.stageIndex || 0)
    const percent = Number.isFinite(Number(currentProgress.progressPercent))
      ? Math.max(0, Math.min(100, Math.round(Number(currentProgress.progressPercent))))
      : 0

    return {
      mode: 'single',
      stage: String(currentProgress.stage || ''),
      title: currentProgress.stageLabel || '图像任务处理中',
      message: currentProgress.stageMessage || props.msg.content || '正在生成图像',
      percent,
      icon: getStageIcon(currentProgress.stage),
      caption: totalStages > 0 && stageIndex > 0
        ? `当前处于第 ${stageIndex}/${totalStages} 个阶段`
        : '等待任务状态更新',
      tag: resolveProgressTag('single'),
    }
  }

  return null
})
const isProgressActive = computed(() => {
  if (!progressCard.value) return false
  const messageStatus = String(props.msg?.status || '').toLowerCase()
  if (['completed', 'error', 'timeout'].includes(messageStatus)) return false
  const stage = String(progressCard.value.stage || '').toLowerCase()
  return !['completed', 'failed', 'timeout', 'cancelled', 'canceled'].includes(stage)
})
const progressStatChips = computed(() => {
  if (!progressCard.value) return []

  if (progressCard.value.mode === 'batch') {
    const total = Number(props.msg?.batchProgress?.total || 0)
    const completed = Number(props.msg?.batchProgress?.completed || 0)
    const running = Number(props.msg?.batchProgress?.running || 0)
    const pending = Number(props.msg?.batchProgress?.pending || 0)
    const failed = Number(props.msg?.batchProgress?.failed || 0)
    const returnedImages = Array.isArray(props.msg?.images) ? props.msg.images.length : 0

    return [
      total > 0 ? { label: '完成', value: `${completed}/${total}` } : null,
      { label: '已返回', value: `${returnedImages} 张` },
      running > 0 ? { label: '进行中', value: `${running} 个` } : null,
      pending > 0 ? { label: '待处理', value: `${pending} 个` } : null,
      failed > 0 ? { label: '失败', value: `${failed} 个` } : null,
    ].filter(Boolean)
  }

  const currentProgress = generationProgress.value || {}
  const stageIndex = Number(currentProgress.stageIndex || 0)
  const totalStages = Number(currentProgress.totalStages || 0)
  const attempt = Number(currentProgress.attempt || 0)
  const outputCount = Array.isArray(props.msg?.images) ? props.msg.images.length : 0

  return [
    stageIndex > 0 && totalStages > 0 ? { label: '阶段', value: `${stageIndex}/${totalStages}` } : null,
    { label: '尝试', value: attempt > 0 ? `第 ${attempt} 次` : '首轮' },
    currentProgress.updatedAt ? { label: '更新', value: formatProgressTime(currentProgress.updatedAt) } : null,
    outputCount > 0 ? { label: '结果', value: `${outputCount} 张` } : null,
  ].filter(Boolean)
})
const progressStagePills = computed(() => {
  if (!progressCard.value || progressCard.value.mode !== 'batch') return []

  return normalizedBatchStageOverview.value.map((item) => {
    const stage = String(item.stage || '')
    return {
      stage,
      label: item.label || '处理中',
      icon: getStageIcon(stage),
      countText: `${item.count} 个`,
      isActive: stage === String(props.msg?.batchProgress?.stage || ''),
      isDone: stage === 'completed',
      isError: stage === 'failed',
    }
  })
})
const progressTimeline = computed(() => {
  if (!progressCard.value || progressCard.value.mode !== 'single') return []

  const history = Array.isArray(generationProgress.value?.history)
    ? generationProgress.value.history.slice(-3)
    : []

  return history.map((event, index) => ({
    ...event,
    timestamp: formatProgressTime(event?.timestamp),
    progressPercent: Number.isFinite(Number(event?.progressPercent))
      ? Math.max(0, Math.min(100, Math.round(Number(event.progressPercent))))
      : 0,
    isActive: isProgressActive.value && index === history.length - 1,
  }))
})
const statusCardThemeClass = computed(() => {
  const messageStatus = String(props.msg?.status || '').toLowerCase()
  if (['error', 'timeout'].includes(messageStatus)) return 'status-card--error'
  if (messageStatus === 'completed') return 'status-card--success'
  return 'status-card--active'
})
const statusBadgeThemeClass = computed(() => {
  const messageStatus = String(props.msg?.status || '').toLowerCase()
  if (['error', 'timeout'].includes(messageStatus)) return 'status-card__badge--error'
  if (messageStatus === 'completed') return 'status-card__badge--success'
  return 'status-card__badge--active'
})
const statusTagThemeClass = computed(() => {
  const messageStatus = String(props.msg?.status || '').toLowerCase()
  if (['error', 'timeout'].includes(messageStatus)) return 'bg-red-500/10 text-red-600'
  if (messageStatus === 'completed') return 'bg-emerald-500/10 text-emerald-700'
  return 'bg-primary/10 text-primary'
})
const progressFillThemeClass = computed(() => {
  const messageStatus = String(props.msg?.status || '').toLowerCase()
  if (['error', 'timeout'].includes(messageStatus)) return 'status-card__progress-fill--error'
  if (messageStatus === 'completed') return 'status-card__progress-fill--success'
  return 'status-card__progress-fill--active'
})

function getAttachmentName(file) {
  return file?.name || file?.filename || file?.original_filename || '附件'
}

function getAttachmentType(file) {
  return (file?.type || file?.file_type || '').toLowerCase()
}

function getAttachmentSize(file) {
  return Number(file?.size || file?.file_size || 0)
}

function formatBytes(bytes) {
  const size = Number(bytes)
  if (!Number.isFinite(size) || size <= 0) return '未知大小'
  const units = ['B', 'KB', 'MB', 'GB']
  let value = size
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  const fixed = unitIndex === 0 ? value.toFixed(0) : value.toFixed(2)
  return `${fixed} ${units[unitIndex]}`
}

function formatAttachmentSize(file) {
  return formatBytes(getAttachmentSize(file))
}

function getStageIcon(stage) {
  const icons = {
    request_received: 'schedule',
    queued: 'hourglass_top',
    extracting_prompt: 'notes',
    semantic_understanding: 'psychology',
    generating_images: 'imagesmode',
    validating_images: 'fact_check',
    saving_images: 'save',
    recording_result: 'database',
    retrying: 'refresh',
    completed: 'check_circle',
    failed: 'error',
  }
  return icons[String(stage || '').toLowerCase()] || 'sync'
}

function formatProgressTime(value) {
  if (!value) return ''
  try {
    return new Date(value).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return ''
  }
}

function resolveProgressTag(mode) {
  const messageStatus = String(props.msg?.status || '').toLowerCase()
  if (messageStatus === 'completed') {
    return mode === 'batch' ? '批量完成' : '生成完成'
  }
  if (messageStatus === 'timeout') return '轮询超时'
  if (messageStatus === 'error') return '任务异常'
  return mode === 'batch' ? '批量任务' : '单张任务'
}

function isImageAttachment(file) {
  const type = getAttachmentType(file)
  if (type.startsWith('image/')) return true
  const fileName = getAttachmentName(file).toLowerCase()
  return /\.(png|jpe?g|gif|webp|bmp|svg)$/.test(fileName)
}

function getAttachmentIcon(file) {
  if (isImageAttachment(file)) return 'image'
  const fileName = getAttachmentName(file).toLowerCase()
  if (fileName.endsWith('.pdf')) return 'picture_as_pdf'
  if (fileName.endsWith('.doc') || fileName.endsWith('.docx')) return 'description'
  if (fileName.endsWith('.xls') || fileName.endsWith('.xlsx')) return 'table_chart'
  if (fileName.endsWith('.ppt') || fileName.endsWith('.pptx')) return 'slideshow'
  if (fileName.endsWith('.zip') || fileName.endsWith('.rar') || fileName.endsWith('.7z')) return 'folder_zip'
  return 'attach_file'
}

function getFileUrl(file) {
  const rawUrl = file?.url || file?.file_url || file?.local_url || file?.preview_url || ''
  if (!rawUrl) return ''
  if (
    rawUrl.startsWith('blob:') ||
    rawUrl.startsWith('data:') ||
    rawUrl.startsWith('http://') ||
    rawUrl.startsWith('https://')
  ) {
    return rawUrl
  }

  const apiEndpoint = apiConfigStore.apiEndpoint
  if (apiEndpoint) {
    const baseUrl = apiEndpoint.replace(/\/$/, '')
    return `${baseUrl}${rawUrl.startsWith('/') ? '' : '/'}${rawUrl}`
  }
  return rawUrl
}

function normalizePreviewImage(image, index = 0) {
  if (!image) return { url: '', alt: `图片 ${index + 1}` }

  if (typeof image === 'string') {
    return {
      url: getImageUrl(image),
      alt: `图片 ${index + 1}`,
    }
  }

  return {
    ...image,
    url: getImageUrl(image),
    alt: image.alt || `图片 ${index + 1}`,
  }
}

function downloadAttachment(file) {
  const url = getFileUrl(file)
  if (!url) {
    notification.error('下载失败', '附件链接不可用')
    return
  }

  const link = document.createElement('a')
  link.href = url
  link.download = getAttachmentName(file)
  link.target = '_blank'
  link.rel = 'noopener noreferrer'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function openGeneratedImagePreview(startIndex = 0) {
  if (!previewableGeneratedImages.value.length) return
  imagePreviewModalRef.value?.show(previewableGeneratedImages.value, startIndex)
}

function openAttachmentPreview(startIndex = 0) {
  if (!previewableAttachmentImages.value.length) return
  imagePreviewModalRef.value?.show(previewableAttachmentImages.value, startIndex)
}

function handlePreviewDownload(image) {
  downloadSingleImage(image)
}

// 备用复制方法
function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement('textarea')
  textArea.value = text

  // 避免在屏幕外滚动
  textArea.style.position = 'fixed'
  textArea.style.left = '-9999px'
  textArea.style.top = '0'

  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()

  try {
    const successful = document.execCommand('copy')
    return successful
  } catch (err) {
    console.error('备用复制方法失败:', err)
    return false
  } finally {
    document.body.removeChild(textArea)
  }
}

// 复制消息内容
function copyContent() {
  const content = props.msg.content
  if (!content) {
    notification.error('复制失败', '消息内容为空')
    return
  }

  try {
    // 优先使用现代 API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(content).then(() => {
        copied.value = true
        notification.success('复制成功', '内容已复制到剪贴板')
        setTimeout(() => {
          copied.value = false
        }, 2000)
      }).catch(err => {
        console.error('现代 API 复制失败，尝试备用方法:', err)
        useFallbackCopy(content)
      })
    } else {
      // 使用备用方法
      useFallbackCopy(content)
    }
  } catch (error) {
    console.error('复制过程出错:', error)
    notification.error('复制失败', '复制过程中出错: ' + error.message)
  }
}

// 使用备用复制方法
function useFallbackCopy(content) {
  const successful = fallbackCopyTextToClipboard(content)
  if (successful) {
    copied.value = true
    notification.success('复制成功', '内容已复制到剪贴板')
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } else {
    notification.error('复制失败', '无法复制内容，请手动选择文本复制')
  }
}

// 重试消息
async function retryMessage() {
  try {
    console.log('重试消息:', props.msg)

    // 重置消息状态为处理中
    props.msg.status = 'processing'
    props.msg.content = '正在重试生成...'

    // 如果有任务ID，重新查询任务状态
    if (props.msg.taskId) {
      await api.getTaskStatus(props.msg.taskId).then(response => {
        const responseStatus = String(response.status || '').toLowerCase()

        if (responseStatus === 'completed') {
          // 任务已完成，更新消息
          props.msg.status = 'completed'
          props.msg.content = '图像生成完成！'

          // 解析 images（可能是字符串或数组）
          let images = []
          if (response.images) {
            if (typeof response.images === 'string') {
              try {
                images = JSON.parse(response.images)
              } catch (e) {
                console.error('解析images失败:', e)
              }
            } else if (Array.isArray(response.images)) {
              images = response.images
            }
          } else if (response.result && Array.isArray(response.result)) {
            images = response.result.map(img => ({
              url: img.url,
              alt: img.alt || '生成的图像'
            }))
          }
          props.msg.images = images
        } else if (['failed', 'error', 'cancelled', 'canceled'].includes(responseStatus)) {
          props.msg.status = 'error'
          props.msg.content = `生成失败: ${response.error || '未知错误'}`
        } else if (['processing', 'running', 'pending'].includes(responseStatus)) {
          props.msg.status = 'processing'
          props.msg.content = response.stage_message || '任务处理中...'
          generatorStore.pollTaskStatus(props.msg.taskId, props.msg.id, 900, 2000)
        }
      })
    } else if (props.msg.batchId) {
      // 批量任务重试
      await api.getBatchTaskStatus(props.msg.batchId).then(response => {
        const responseStatus = String(response.status || '').toLowerCase()

        if (responseStatus === 'completed') {
          props.msg.status = 'completed'
          props.msg.content = `批量生成完成！共 ${props.msg.images?.length || response.tasks?.filter(t => t.status === 'completed').length || 0} 张图片`
          // 更新图片列表
          if (response.tasks) {
            props.msg.images = response.tasks
              .filter(task => task.status === 'completed' && task.images)
              .map(task => task.images[0])
              .flat()
          } else if (response.images) {
            props.msg.images = response.images
          }
        } else if (['failed', 'error', 'cancelled', 'canceled'].includes(responseStatus)) {
          props.msg.status = 'error'
          props.msg.content = `批量生成失败: ${response.error || '未知错误'}`
        } else if (['processing', 'running', 'pending'].includes(responseStatus)) {
          props.msg.status = 'processing'
          props.msg.content = response.stage_message || response.status_detail?.current_stage_message || '任务处理中...'
          const totalCount = Number(props.msg?.batchProgress?.total || response.total || response.tasks?.length || 1)
          generatorStore.pollBatchStatusIncremental(props.msg.batchId, props.msg.id, totalCount, 900, 2000)
        }
      })
    } else {
      // 没有任务ID的情况，使用生成器的重试方法
      const result = await generatorStore.retryGeneration(props.msg.id)
      if (result.success) {
        notification.success('重试成功', '已重新发起生成请求')
      } else {
        props.msg.status = 'error'
        props.msg.content = `重试失败: ${result.error || '未知错误'}`
        notification.error('重试失败', result.error || '重试过程中出错')
      }
    }

    if (props.msg.taskId || props.msg.batchId) {
      notification.success('重试中', '正在重新查询任务状态...')
    }

  } catch (error) {
    console.error('重试失败:', error)
    props.msg.status = 'error'
    props.msg.content = `重试失败: ${error?.message || '未知错误'}`
    notification.error('重试失败', error?.message || '重试过程中出错')
  }
}

// 转换图片URL为完整URL
const getImageUrl = (image, useThumbnail = false) => {
  let url = image
  if (typeof image === 'object') {
    url = (useThumbnail && image.thumbnail_url) ? image.thumbnail_url : image.url
  }
  if (!url) return url

  // 如果已经是完整URL，直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }

  // 如果是相对路径，基于API endpoint构建完整URL
  const apiEndpoint = apiConfigStore.apiEndpoint
  if (apiEndpoint) {
    const baseUrl = apiEndpoint.replace(/\/$/, '')
    return `${baseUrl}${url.startsWith('/') ? '' : '/'}${url}`
  }

  return url
}

// 获取状态样式
function getStatusClasses(status) {
  const classes = {
    processing: 'bg-primary/10 text-ink-950 border border-primary/20',
    completed: 'bg-primary/10 text-ink-950 border border-primary/20',
    error: 'bg-red-500/10 text-red-500 border border-red-500/20',
    timeout: 'bg-amber-500/10 text-amber-700 border border-amber-500/20'
  }
  return classes[status] || 'text-ink-950'
}

// 通过后端代理下载图片，解决跨域问题
async function downloadImageAsBlob(url, filename) {
  const apiEndpoint = apiConfigStore.apiEndpoint?.replace(/\/$/, '') || ''
  // 外部图片走代理，相对路径直接请求
  const fetchUrl = url.startsWith('http')
    ? `${apiEndpoint}/api/v1/files/image-proxy?url=${encodeURIComponent(url)}`
    : url
  const response = await fetch(fetchUrl)
  if (!response.ok) throw new Error(`下载失败: ${response.status}`)
  const blob = await response.blob()
  const ext = blob.type.includes('jpeg') ? 'jpg' : (blob.type.split('/')[1] || 'png')
  const blobUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = filename.match(/\.\w+$/) ? filename : `${filename}.${ext}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(blobUrl)
}

// 下载单张图片
async function downloadSingleImage(image) {
  try {
    const imageUrl = typeof image === 'string' ? image : image.url
    const imageAlt = typeof image === 'object' ? (image.alt || '生成的图像') : '生成的图像'
    await downloadImageAsBlob(getImageUrl(imageUrl), `${imageAlt}-${Date.now()}`)
    notification.success('下载成功', `已下载: ${imageAlt}`)
  } catch (error) {
    console.error('下载失败:', error)
    notification.error('下载失败', error.message || '无法下载图片')
  }
}

// 下载所有图片
async function downloadAllImages() {
  if (!props.msg.images || props.msg.images.length === 0) return

  isDownloading.value = true

  try {
    for (let i = 0; i < props.msg.images.length; i++) {
      const image = props.msg.images[i]
      downloadProgress.value[i] = 0
      try {
        const imageUrl = typeof image === 'string' ? image : image.url
        const imageAlt = typeof image === 'object' ? (image.alt || `image-${i + 1}`) : `image-${i + 1}`
        await downloadImageAsBlob(getImageUrl(imageUrl), `${imageAlt}-${i + 1}`)
        downloadProgress.value[i] = 100
        await new Promise(r => setTimeout(r, 200))
        delete downloadProgress.value[i]
      } catch (error) {
        console.error(`下载图片 ${i + 1} 失败:`, error)
        downloadProgress.value[i] = -1
      }
    }
    notification.success('下载完成', `已下载 ${props.msg.images.length} 张图片`)
  } catch (error) {
    console.error('批量下载失败:', error)
    notification.error('下载失败', error.message || '批量下载过程中出错')
  } finally {
    isDownloading.value = false
    downloadProgress.value = {}
  }
}

// Toggle like
function toggleLike() {
  isLiked.value = !isLiked.value
  if (isLiked.value) {
    isDisliked.value = false
  }
  console.log('Message liked:', props.msg.id, isLiked.value)
}

// Toggle dislike
function toggleDislike() {
  isDisliked.value = !isDisliked.value
  if (isDisliked.value) {
    isLiked.value = false
  }
  console.log('Message disliked:', props.msg.id, isDisliked.value)
}

// Share message - Convert conversation to markdown and generate shareable link
async function shareMessage() {
  try {
    // Build markdown content from conversation
    let markdown = `# AI 生图对话\n\n`
    markdown += `**时间**: ${new Date().toLocaleString()}\n\n`
    markdown += `---\n\n`

    // Find current message index and include context
    const msgIndex = generatorStore.messages.findIndex(m => m.id === props.msg.id)
    const messagesToInclude = generatorStore.messages.slice(0, msgIndex + 1)

    messagesToInclude.forEach((msg, idx) => {
      if (msg.role === 'user') {
        markdown += `## 👤 用户\n\n${msg.content}\n\n`
      } else if (msg.role === 'assistant') {
        markdown += `## 🤖 AI 助手\n\n`
        if (msg.content) {
          markdown += `${msg.content}\n\n`
        }
        if (msg.images && msg.images.length > 0) {
          markdown += `**生成的图片** (${msg.images.length}张):\n\n`
          msg.images.forEach((img, imgIdx) => {
            const imgUrl = typeof img === 'string' ? img : img.url
            markdown += `${imgIdx + 1}. [图片 ${imgIdx + 1}](${imgUrl})\n`
          })
          markdown += `\n`
        }
      }
      markdown += `---\n\n`
    })

    // Encode markdown to base64 for URL
    const encodedMarkdown = btoa(unescape(encodeURIComponent(markdown)))
    const shareUrl = `${window.location.origin}${window.location.pathname}#share=${encodedMarkdown}`

    // Copy shareable link to clipboard
    await navigator.clipboard.writeText(shareUrl)
    notification.success('分享链接已复制', '对话已转换为 Markdown，分享链接已复制到剪贴板')

  } catch (error) {
    console.error('分享失败:', error)
    notification.error('分享失败', error.message || '生成分享链接时出错')
  }
}

// Toggle model dropdown
function toggleModelDropdown() {
  showModelDropdown.value = !showModelDropdown.value
}

// Select model
function selectModel(model) {
  generatorStore.setSelectedModel(model.model_name)
  generatorStore.setSelectedModelInfo(model)
  showModelDropdown.value = false
  notification.success('模型已切换', `已切换到 ${model.display_name || model.model_name}`)
  if (props.msg.role === 'assistant' && props.msg.status === 'completed') {
    if (confirm(`是否使用 ${model.display_name || model.model_name} 重新生成?`)) {
      retryMessage()
    }
  }
}

// Copy prompt
function copyPrompt() {
  const userMessages = generatorStore.messages.filter(m => m.role === 'user')
  if (userMessages.length > 0) {
    const lastUserMessage = userMessages[userMessages.length - 1]
    fallbackCopyTextToClipboard(lastUserMessage.content)
    notification.success('提示词已复制', '提示词已复制到剪贴板')
  }
}

// Quote message
function quoteMessage() {
  if (!props.msg.content) return

  // 将引用的消息存储到 store 中
  generatorStore.quotedMessage = {
    id: props.msg.id,
    content: props.msg.content
  }

  notification.success('已引用', '消息内容已引用，将在发送时附加到提示词')
}

// Download image (for more menu)
function downloadImage() {
  if (props.msg.images && props.msg.images.length > 0) {
    downloadSingleImage(props.msg.images[0])
  }
}

// Regenerate message
function regenerate() {
  showMoreMenu.value = false
  retryMessage()
}

// Delete message
function deleteMessage() {
  if (confirm('确定要删除这条消息吗？')) {
    const index = generatorStore.messages.findIndex(m => m.id === props.msg.id)
    if (index > -1) {
      generatorStore.messages.splice(index, 1)
      notification.success('删除成功', '消息已删除')
    }
  }
}

// Close dropdowns when clicking outside
function handleClickOutside(event) {
  const modelDropdown = document.querySelector('[data-model-dropdown]')
  if (modelDropdown && !modelDropdown.contains(event.target)) {
    showModelDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.markdown-body :deep(p) { margin: 0.4em 0; }
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) { font-weight: bold; margin: 0.6em 0 0.3em; }
.markdown-body :deep(h1) { font-size: 1.2em; }
.markdown-body :deep(h2) { font-size: 1.1em; }
.markdown-body :deep(h3) { font-size: 1em; }
.markdown-body :deep(ul),
.markdown-body :deep(ol) { padding-left: 1.4em; margin: 0.4em 0; }
.markdown-body :deep(li) { margin: 0.2em 0; }
.markdown-body :deep(code) { background: rgba(16, 19, 18, 0.06); padding: 0.1em 0.4em; border-radius: 4px; font-size: 0.85em; font-family: monospace; }
.markdown-body :deep(pre) { background: rgba(16, 19, 18, 0.05); padding: 0.8em 1em; border-radius: 8px; overflow-x: auto; margin: 0.6em 0; border: 1px solid rgba(16, 19, 18, 0.08); }
.markdown-body :deep(pre code) { background: none; padding: 0; }
.markdown-body :deep(blockquote) { border-left: 3px solid rgba(0, 220, 130, 0.35); padding-left: 0.8em; margin: 0.4em 0; opacity: 0.9; color: rgba(16, 19, 18, 0.72); }
.markdown-body :deep(a) { color: #00bb6f; text-decoration: underline; }
.markdown-body :deep(strong) { font-weight: bold; }
.markdown-body :deep(em) { font-style: italic; }
.markdown-body :deep(hr) { border: none; border-top: 1px solid rgba(16, 19, 18, 0.1); margin: 0.6em 0; }
.markdown-body :deep(table) { border-collapse: collapse; width: 100%; margin: 0.6em 0; }
.markdown-body :deep(th),
.markdown-body :deep(td) { border: 1px solid rgba(16, 19, 18, 0.08); padding: 0.4em 0.8em; }
.markdown-body :deep(th) { background: rgba(16, 19, 18, 0.04); }

.status-card {
  backdrop-filter: blur(14px);
  box-shadow: 0 18px 40px rgba(16, 19, 18, 0.08);
}

.status-card--active {
  border-color: rgba(0, 187, 111, 0.16);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(0, 187, 111, 0.06) 62%, rgba(226, 255, 242, 0.92) 100%);
}

.status-card--success {
  border-color: rgba(16, 185, 129, 0.18);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(209, 250, 229, 0.9) 100%);
}

.status-card--error {
  border-color: rgba(239, 68, 68, 0.18);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(254, 242, 242, 0.94) 100%);
}

.status-card__ambient {
  position: absolute;
  left: -3rem;
  top: -3rem;
  width: 14rem;
  height: 14rem;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(0, 187, 111, 0.18) 0%, rgba(0, 187, 111, 0) 70%);
  animation: status-orbit 5s ease-in-out infinite;
  pointer-events: none;
}

.status-card__badge {
  position: relative;
  display: flex;
  width: 2.75rem;
  height: 2.75rem;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 1rem;
  overflow: hidden;
}

.status-card__badge::after {
  content: '';
  position: absolute;
  inset: -0.3rem;
  border-radius: 1.15rem;
}

.status-card__badge--active {
  color: #00a86b;
  background: linear-gradient(145deg, rgba(0, 187, 111, 0.14), rgba(255, 255, 255, 0.9));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 10px 24px rgba(0, 187, 111, 0.16);
}

.status-card__badge--active::after {
  border: 1px solid rgba(0, 187, 111, 0.2);
  animation: status-pulse-ring 1.8s ease-out infinite;
}

.status-card__badge--success {
  color: #047857;
  background: linear-gradient(145deg, rgba(16, 185, 129, 0.14), rgba(255, 255, 255, 0.9));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 10px 24px rgba(16, 185, 129, 0.14);
}

.status-card__badge--error {
  color: #dc2626;
  background: linear-gradient(145deg, rgba(239, 68, 68, 0.14), rgba(255, 255, 255, 0.92));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85), 0 10px 24px rgba(239, 68, 68, 0.12);
}

.status-card__icon-spin {
  animation: status-spin 2.2s linear infinite;
}

.status-card__progress-track {
  position: relative;
  height: 0.75rem;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 1px 2px rgba(16, 19, 18, 0.08);
}

.status-card__progress-track::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.55) 50%, transparent 100%);
  transform: translateX(-100%);
  animation: track-shimmer 2.6s linear infinite;
}

.status-card__progress-fill {
  position: relative;
  height: 100%;
  min-width: 0.9rem;
  border-radius: inherit;
  overflow: hidden;
  transition: width 420ms cubic-bezier(0.22, 1, 0.36, 1);
}

.status-card__progress-fill::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.2) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0.2) 75%,
    transparent 75%,
    transparent
  );
  background-size: 22px 22px;
  animation: progress-stripes 1.2s linear infinite;
}

.status-card__progress-fill--active {
  background: linear-gradient(90deg, #00b26d 0%, #00cf85 52%, #8ef3c7 100%);
}

.status-card__progress-fill--success {
  background: linear-gradient(90deg, #059669 0%, #10b981 55%, #6ee7b7 100%);
}

.status-card__progress-fill--error {
  background: linear-gradient(90deg, #ef4444 0%, #fb7185 55%, #fca5a5 100%);
}

.status-card__progress-shine {
  position: absolute;
  inset: 0 auto 0 -2.5rem;
  width: 2.5rem;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0));
  animation: fill-shine 1.8s linear infinite;
}

.status-chip {
  display: flex;
  min-width: 4.5rem;
  flex-direction: column;
  gap: 0.2rem;
  border-radius: 0.95rem;
  border: 1px solid rgba(16, 19, 18, 0.08);
  background: rgba(255, 255, 255, 0.72);
  padding: 0.55rem 0.7rem;
}

.stage-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border-radius: 999px;
  border: 1px solid rgba(16, 19, 18, 0.08);
  background: rgba(255, 255, 255, 0.78);
  padding: 0.38rem 0.65rem;
  font-size: 0.7rem;
  color: rgba(16, 19, 18, 0.68);
  transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease, color 220ms ease;
}

.stage-pill--active {
  color: #007c4a;
  border-color: rgba(0, 187, 111, 0.22);
  box-shadow: 0 10px 22px rgba(0, 187, 111, 0.12);
  transform: translateY(-1px);
}

.stage-pill--done {
  color: #047857;
  border-color: rgba(16, 185, 129, 0.18);
}

.stage-pill--error {
  color: #dc2626;
  border-color: rgba(239, 68, 68, 0.18);
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
}

.timeline-item__dot {
  width: 0.65rem;
  height: 0.65rem;
  margin-top: 0.35rem;
  flex-shrink: 0;
  border-radius: 999px;
  background: rgba(0, 187, 111, 0.22);
  box-shadow: 0 0 0 0.35rem rgba(0, 187, 111, 0.08);
}

.timeline-item--active .timeline-item__dot {
  background: #00b26d;
  animation: timeline-pulse 1.45s ease-out infinite;
}

.loading-dots {
  display: inline-flex;
  align-items: center;
  gap: 0.22rem;
}

.loading-dots span {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 999px;
  background: #00b26d;
  animation: loading-dots 1.1s ease-in-out infinite;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.3s;
}

/* Thinking animation dots */
@keyframes thinking-bounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  40% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

.thinking-dot {
  animation: thinking-bounce 1.4s ease-in-out infinite;
}

.thinking-dot:nth-child(1) { animation-delay: 0s; }
.thinking-dot:nth-child(2) { animation-delay: 0.15s; }
.thinking-dot:nth-child(3) { animation-delay: 0.3s; }

@keyframes status-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes track-shimmer {
  from { transform: translateX(-100%); }
  to { transform: translateX(200%); }
}

@keyframes progress-stripes {
  from { background-position: 0 0; }
  to { background-position: 22px 0; }
}

@keyframes fill-shine {
  from { transform: translateX(0); }
  to { transform: translateX(220px); }
}

@keyframes status-orbit {
  0%, 100% {
    transform: translate3d(0, 0, 0) scale(0.95);
    opacity: 0.55;
  }
  50% {
    transform: translate3d(1.6rem, 1rem, 0) scale(1.05);
    opacity: 1;
  }
}

@keyframes status-pulse-ring {
  0% {
    transform: scale(0.92);
    opacity: 0.55;
  }
  100% {
    transform: scale(1.18);
    opacity: 0;
  }
}

@keyframes timeline-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 178, 109, 0.2);
  }
  70% {
    box-shadow: 0 0 0 0.55rem rgba(0, 178, 109, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 178, 109, 0);
  }
}

@keyframes loading-dots {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-0.2rem);
    opacity: 1;
  }
}

.status-card-enter-active,
.status-card-leave-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.status-card-enter-from,
.status-card-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (prefers-reduced-motion: reduce) {
  .status-card__ambient,
  .status-card__badge--active::after,
  .status-card__icon-spin,
  .status-card__progress-track::before,
  .status-card__progress-fill::before,
  .status-card__progress-shine,
  .timeline-item--active .timeline-item__dot,
  .loading-dots span,
  .thinking-dot {
    animation: none !important;
  }
}
</style>
