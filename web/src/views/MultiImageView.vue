<template>
  <main class="multi-view flex h-full min-h-0 flex-1 flex-col overflow-y-auto">
    <div class="mx-auto flex w-full max-w-[1380px] flex-1 flex-col gap-6 px-4 pb-10 pt-6 xs:px-6 md:px-8 md:gap-8 md:pt-8">
      <section class="space-y-6">
          <section class="glass-panel rounded-[30px] p-5 md:p-7">
            <div class="max-w-3xl">
              <div class="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/6 px-3 py-1 text-xs font-semibold tracking-[0.18em] text-primary">
                <span class="material-symbols-outlined !text-sm">auto_awesome</span>
                多图创作
              </div>
              <h1 class="mt-4 text-3xl font-bold tracking-tight text-ink-950 md:text-[2.7rem] md:leading-[1.1]">
                一次输入，生成一整组更清晰的图片
              </h1>
              <p class="mt-3 max-w-2xl text-sm leading-6 text-ink-500 md:text-base">
                适合把教程、知识点、招生内容、流程说明拆成多张图。输入内容后会在下方保留横向历史，生成结果也支持放大查看细节。
              </p>
            </div>

            <div class="mt-6 rounded-[28px] border border-border-dark/80 bg-white/95 p-4 shadow-[0_24px_60px_rgba(140,42,46,0.06)] md:p-5">
              <el-input
                ref="promptRef"
                v-model="promptInput"
                type="textarea"
                :rows="5"
                placeholder="输入主题或内容描述，例如：三十六计、十二星座、四季变化、初高中化学衔接指南..."
                resize="none"
                @keydown.ctrl.enter="startBatchGeneration"
                @keydown.meta.enter="startBatchGeneration"
              />

              <div class="mt-3 flex flex-wrap items-center gap-1.5">
                <button
                  v-if="selectedTypeLabel"
                  class="inline-flex cursor-pointer items-center gap-1 rounded-lg border border-primary/20 bg-primary/8 px-2.5 py-1.5 text-xs font-medium text-primary hover:bg-primary/15"
                  @click="selectedType = ''"
                >
                  {{ selectedTypeEmoji }} {{ selectedTypeLabel }}
                  <span class="material-symbols-outlined !text-[11px] opacity-50">close</span>
                </button>

                <button
                  v-if="selectedStyleLabel"
                  class="inline-flex cursor-pointer items-center gap-1 rounded-lg border border-border-dark bg-white px-2.5 py-1.5 text-xs font-medium text-ink-700 hover:bg-ink-300/10"
                  @click="selectedStyle = ''"
                >
                  {{ selectedStyleLabel }}
                  <span class="material-symbols-outlined !text-[11px] opacity-50">close</span>
                </button>

                <RatioDropdown class="shrink-0" />
                <ResolutionDropdown class="shrink-0" />

                <el-popover placement="bottom" :width="220" trigger="click">
                  <template #reference>
                    <el-button size="small">
                      <span class="material-symbols-outlined !text-sm">grid_on</span>
                      <span class="text-xs">{{ batchCount }}张</span>
                    </el-button>
                  </template>
                  <div class="space-y-3">
                    <div class="text-xs font-semibold text-ink-700">选择生成张数</div>
                    <div class="grid grid-cols-3 gap-2">
                      <el-button
                        v-for="count in presetCounts"
                        :key="count"
                        :type="batchCount === count ? 'primary' : 'default'"
                        :plain="batchCount !== count"
                        size="small"
                        @click="batchCount = count"
                      >
                        {{ count }}
                      </el-button>
                    </div>
                    <el-input-number
                      v-model="batchCount"
                      :min="1"
                      :max="36"
                      size="small"
                      controls-position="right"
                      class="w-full"
                    />
                  </div>
                </el-popover>

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

                <el-button
                  type="primary"
                  round
                  size="small"
                  class="!px-4"
                  :disabled="(!promptInput.trim() && attachments.length === 0) || isGenerating"
                  :loading="isGenerating"
                  @click="startBatchGeneration"
                >
                  <span class="material-symbols-outlined !text-base">arrow_upward</span>
                  <span class="material-symbols-outlined !text-base">bolt</span>
                </el-button>
              </div>

              <div v-if="attachments.length > 0" class="mt-3 flex flex-wrap gap-1.5">
                <div
                  v-for="(file, index) in attachments"
                  :key="`${file.name}-${index}`"
                  class="flex items-center gap-1.5 rounded-lg border border-primary/20 bg-primary-soft px-2.5 py-1"
                >
                  <span class="material-symbols-outlined !text-sm text-primary">{{ getFileIcon(file) }}</span>
                  <span class="max-w-[120px] truncate text-xs text-ink-700">{{ file.name }}</span>
                  <button
                    class="cursor-pointer text-ink-500 hover:text-ink-950"
                    @click="attachments.splice(index, 1)"
                  >
                    <span class="material-symbols-outlined !text-xs">close</span>
                  </button>
                </div>
              </div>

              <div class="mt-4 flex flex-wrap items-center gap-2 rounded-2xl bg-ink-950/[0.03] px-3 py-2 text-xs text-ink-500">
                <span class="inline-flex items-center gap-1 rounded-full bg-white px-2 py-1 text-ink-700 shadow-sm">
                  <span class="material-symbols-outlined !text-sm text-primary">zoom_in</span>
                  结果支持放大预览
                </span>
                <span class="inline-flex items-center gap-1 rounded-full bg-white px-2 py-1 text-ink-700 shadow-sm">
                  <span class="material-symbols-outlined !text-sm text-primary">history</span>
                  历史自动保存在下方横向列表
                </span>
                <span class="inline-flex items-center gap-1 rounded-full bg-white px-2 py-1 text-ink-700 shadow-sm">
                  <span class="material-symbols-outlined !text-sm text-primary">sync</span>
                  积分会跟随生成实时刷新
                </span>
              </div>
            </div>
          </section>

          <section class="glass-panel rounded-[28px] p-5 md:p-6">
            <div class="mb-4 flex items-center gap-2">
              <button
                :class="[
                  'rounded-lg px-4 py-1.5 text-sm font-medium transition-colors',
                  activeTab === 'type'
                    ? 'bg-ink-950 text-white'
                    : 'border border-border-dark bg-white/80 text-ink-700 hover:bg-white'
                ]"
                @click="activeTab = 'type'"
              >
                类型
              </button>
              <button
                :class="[
                  'rounded-lg px-4 py-1.5 text-sm font-medium transition-colors',
                  activeTab === 'style'
                    ? 'bg-ink-950 text-white'
                    : 'border border-border-dark bg-white/80 text-ink-700 hover:bg-white'
                ]"
                @click="activeTab = 'style'"
              >
                风格
              </button>
              <button
                class="inline-flex cursor-pointer items-center rounded-full p-1 text-ink-400 transition-colors hover:bg-white hover:text-ink-700"
                @click="showTypePanel = !showTypePanel"
              >
                <span class="material-symbols-outlined !text-lg">
                  {{ showTypePanel ? 'expand_less' : 'expand_more' }}
                </span>
              </button>
            </div>

            <div v-show="showTypePanel">
              <div v-if="activeTab === 'type'">
                <div
                  v-if="typesHasCover"
                  class="grid grid-cols-3 gap-3 xs:grid-cols-4 md:grid-cols-5"
                >
                  <button
                    v-for="typeItem in filteredTypes"
                    :key="typeItem.value"
                    class="relative flex cursor-pointer flex-col items-center group"
                    @click="selectedType = selectedType === typeItem.value ? '' : typeItem.value"
                  >
                    <div
                      :class="[
                        'w-full overflow-hidden rounded-xl border-2',
                        selectedType === typeItem.value
                          ? 'border-primary'
                          : 'border-transparent hover:border-primary/30'
                      ]"
                    >
                      <div class="overflow-hidden rounded-xl bg-primary-soft/10">
                        <img
                          v-if="typeItem.cover"
                          :src="typeItem.cover"
                          :alt="typeItem.label"
                          class="h-auto w-full object-contain transition-transform duration-300 group-hover:scale-105"
                          loading="lazy"
                        />
                        <div
                          v-else
                          class="flex aspect-square w-full items-center justify-center text-sm font-bold text-ink-400"
                        >
                          {{ typeItem.label }}
                        </div>
                      </div>
                    </div>
                    <div
                      v-if="selectedType === typeItem.value"
                      class="absolute right-1.5 top-1.5 grid h-5 w-5 place-items-center rounded-full bg-primary text-white"
                    >
                      <span class="material-symbols-outlined !text-xs">check</span>
                    </div>
                    <span class="mt-1.5 text-xs font-medium text-ink-700">{{ typeItem.label }}</span>
                  </button>
                </div>

                <div v-else class="flex flex-wrap gap-2">
                  <button
                    v-for="typeItem in filteredTypes"
                    :key="typeItem.value"
                    :class="[
                      'cursor-pointer rounded-lg border px-3 py-1.5 text-xs font-medium',
                      selectedType === typeItem.value
                        ? 'border-primary bg-primary/8 text-primary'
                        : 'border-border-dark bg-white text-ink-700 hover:border-primary/30'
                    ]"
                    @click="selectedType = selectedType === typeItem.value ? '' : typeItem.value"
                  >
                    {{ typeItem.label }}
                  </button>
                </div>
              </div>

              <div v-else class="grid grid-cols-3 gap-3 xs:grid-cols-4 md:grid-cols-5">
                <button
                  v-for="styleItem in imageStyles"
                  :key="styleItem.value"
                  class="relative flex cursor-pointer flex-col items-center group"
                  @click="selectedStyle = selectedStyle === styleItem.value ? '' : styleItem.value"
                >
                  <div
                    :class="[
                      'w-full overflow-hidden rounded-xl border-2',
                      selectedStyle === styleItem.value
                        ? 'border-primary'
                        : 'border-transparent hover:border-primary/30'
                    ]"
                  >
                    <div class="overflow-hidden rounded-xl bg-primary-soft/10">
                      <img
                        :src="styleItem.cover"
                        :alt="styleItem.label"
                        class="h-auto w-full object-contain transition-transform duration-300 group-hover:scale-105"
                        loading="lazy"
                      />
                    </div>
                  </div>
                  <div
                    v-if="selectedStyle === styleItem.value"
                    class="absolute right-1.5 top-1.5 grid h-5 w-5 place-items-center rounded-full bg-primary text-white"
                  >
                    <span class="material-symbols-outlined !text-xs">check</span>
                  </div>
                  <span
                    :class="[
                      'mt-1.5 text-xs font-medium',
                      selectedStyle === styleItem.value ? 'text-primary' : 'text-ink-700'
                    ]"
                  >
                    {{ styleItem.label }}
                  </span>
                </button>
              </div>
            </div>
          </section>

          <section v-if="currentTask" class="glass-panel rounded-[28px] p-5 md:p-6">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold" :class="currentTaskBadgeClass">
                  <span class="material-symbols-outlined !text-sm">{{ currentTaskIcon }}</span>
                  {{ currentTask.statusText }}
                </div>
                <p class="mt-3 max-w-3xl text-sm leading-6 text-ink-600">
                  {{ currentTask.prompt || '正在处理本次多图任务' }}
                </p>
              </div>

              <button
                v-if="currentTask.status !== 'generating'"
                class="inline-flex items-center rounded-full border border-border-dark bg-white px-3 py-1.5 text-xs font-medium text-ink-500 transition-colors hover:text-ink-950"
                @click="currentTask = null"
              >
                <span class="material-symbols-outlined !text-sm">close</span>
                关闭结果
              </button>
            </div>

            <div class="mt-5">
              <div class="flex items-center justify-between text-xs text-ink-500">
                <span>{{ currentTask.progressText }}</span>
                <span>{{ currentTask.progress }}%</span>
              </div>
              <div class="mt-2 h-2.5 overflow-hidden rounded-full bg-primary-soft/80">
                <div
                  class="h-full rounded-full bg-gradient-to-r from-primary to-primary-deep transition-all duration-500"
                  :style="{ width: `${currentTask.progress}%` }"
                ></div>
              </div>
            </div>

            <div v-if="currentTask.images.length > 0" class="mt-5 grid gap-4" :class="resultGridClass(currentTask.images.length)">
              <button
                v-for="(image, index) in currentTask.images"
                :key="`${image.url}-${index}`"
                class="result-card cursor-zoom-in text-left"
                @click="openCurrentTaskPreview(index)"
              >
                <div class="result-card__canvas">
                  <img
                    :src="image.url"
                    :alt="image.alt || `生成图片 ${index + 1}`"
                    class="h-full w-full object-contain"
                    @error="handlePreviewImageFallback"
                  />
                </div>
                <div class="flex items-center justify-between gap-3 px-4 py-3 text-xs text-ink-500">
                  <span class="truncate">{{ image.alt || `生成图片 ${index + 1}` }}</span>
                  <span class="inline-flex items-center gap-1 text-primary">
                    <span class="material-symbols-outlined !text-sm">zoom_in</span>
                    放大查看
                  </span>
                </div>
              </button>
            </div>

            <div
              v-else-if="currentTask.status === 'generating'"
              class="mt-5 grid gap-4"
              :class="resultGridClass(currentTask.total)"
            >
              <div
                v-for="placeholderIndex in currentTask.total"
                :key="placeholderIndex"
                class="result-card result-card--placeholder"
              >
                <div class="result-card__skeleton">
                  <div class="result-card__skeleton-orb result-card__skeleton-orb--one"></div>
                  <div class="result-card__skeleton-orb result-card__skeleton-orb--two"></div>
                  <div class="result-card__skeleton-panel"></div>
                </div>
                <div class="px-4 py-3 text-xs text-ink-400">
                  第 {{ placeholderIndex }} 张生成中...
                </div>
              </div>
            </div>

            <p v-if="currentTask.error" class="mt-4 rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-500">
              {{ currentTask.error }}
            </p>
          </section>

          <section class="glass-panel rounded-[28px] p-5 md:p-6">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="text-xl font-bold text-ink-950">生图历史</h2>
                <p class="mt-1 text-sm text-ink-500">
                  最近完成的作品会保留在这里，方便像首页画廊一样快速回看和放大。
                </p>
              </div>
              <router-link
                v-if="galleryRecords.length > 0"
                to="/gallery"
                class="inline-flex items-center gap-1 rounded-full border border-border-dark bg-white px-3 py-1.5 text-xs font-medium text-ink-600 transition-colors hover:border-primary/30 hover:text-primary"
              >
                查看全部
                <span class="material-symbols-outlined !text-sm">arrow_forward</span>
              </router-link>
            </div>

            <div v-if="galleryLoading && galleryRecords.length === 0" class="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
              <div v-for="i in 4" :key="i" class="animate-pulse overflow-hidden rounded-xl bg-white/60">
                <div class="aspect-square rounded-t-xl bg-primary-soft/30"></div>
                <div class="space-y-1.5 p-2.5">
                  <div class="h-3 w-3/4 rounded bg-primary-soft/30"></div>
                  <div class="h-2 w-1/2 rounded bg-primary-soft/30"></div>
                </div>
              </div>
            </div>

            <div v-else-if="galleryRecords.length > 0" class="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
              <article
                v-for="record in galleryRecords"
                :key="record.id"
                class="group relative overflow-hidden rounded-xl border border-border-dark bg-white/90 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lg"
              >
                <button class="block w-full cursor-zoom-in text-left" @click="openRecordPreview(record, 0)">
                  <div class="relative aspect-square overflow-hidden bg-primary-soft/20">
                    <img
                      v-if="getRecordImage(record)"
                      :src="getRecordImage(record)"
                      :alt="displayPromptOrFallback(record.prompt)"
                      class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      loading="lazy"
                      @error="handlePreviewImageFallback"
                    />
                    <div v-else class="flex h-full items-center justify-center bg-primary-soft text-primary">
                      <span class="material-symbols-outlined !text-4xl">image</span>
                    </div>

                    <div
                      v-if="record.image_urls?.length"
                      class="absolute bottom-1.5 left-1.5 inline-flex items-center gap-1 rounded-full bg-white/92 px-2 py-1 text-[11px] font-medium text-primary shadow-sm backdrop-blur-sm"
                    >
                      <span class="material-symbols-outlined !text-sm">photo_library</span>
                      {{ record.image_urls.length }} 张
                    </div>
                  </div>
                </button>

                <div class="absolute right-1.5 top-1.5 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    class="grid h-7 w-7 place-items-center rounded-full bg-white/90 shadow backdrop-blur-sm transition-colors hover:bg-white"
                    @click.stop="openRecordPreview(record, 0)"
                  >
                    <span class="material-symbols-outlined !text-sm text-ink-700">zoom_in</span>
                  </button>
                  <button
                    v-if="extractDisplayPrompt(record.prompt)"
                    class="grid h-7 w-7 place-items-center rounded-full bg-white/90 shadow backdrop-blur-sm transition-colors hover:bg-white"
                    @click.stop="copyPrompt(record.prompt)"
                  >
                    <span class="material-symbols-outlined !text-sm text-ink-700">content_copy</span>
                  </button>
                </div>

                <div class="p-2.5">
                  <p class="line-clamp-2 pr-5 text-xs text-ink-700">
                    {{ displayPromptOrFallback(record.prompt) }}
                  </p>

                  <div class="mt-2 flex items-center justify-between gap-2 text-[11px] text-ink-400">
                    <span class="truncate">{{ formatTime(record.created_at || record.timestamp) }}</span>
                    <span class="truncate">{{ record.model || record.provider || '未标记模型' }}</span>
                  </div>
                </div>
              </article>
            </div>

            <div v-else class="mt-5 rounded-[24px] border border-dashed border-border-dark bg-white/70 p-6 text-center">
              <span class="material-symbols-outlined !text-4xl text-ink-300">history</span>
              <p class="mt-2 text-sm font-medium text-ink-700">还没有生图历史</p>
              <p class="mt-1 text-xs text-ink-500">生成完成后，作品会以更大的横向卡片展示在这里</p>
            </div>
          </section>
      </section>
    </div>

    <ImagePreviewModal ref="imagePreviewModalRef" />
  </main>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/useAuthStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import ModelDropdown from '@/components/landing/ModelDropdown.vue'
import RatioDropdown from '@/components/landing/RatioDropdown.vue'
import ResolutionDropdown from '@/components/landing/ResolutionDropdown.vue'
import ImagePreviewModal from '@/components/ImagePreviewModal.vue'
import { api } from '@/services/api'
import { notification } from '@/utils/notification'
import { copyText } from '@/utils/clipboard'
import { extractDisplayPrompt, displayPromptOrFallback } from '@/utils/promptDisplay'
import { handleImageFallback, resolveImageSrc } from '@/utils/imageFallback'
import { getTutorialExampleById } from '@/constants/multiGuide'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const generatorStore = useGeneratorStore()

const promptRef = ref(null)
const promptInput = ref('')
const batchCount = ref(4)
const activeTab = ref('type')
const selectedType = ref('')
const selectedStyle = ref('')
const isGenerating = ref(false)
const galleryRecords = ref([])
const galleryLoading = ref(false)
const currentTask = ref(null)
const attachments = ref([])
const uploadRef = ref(null)
const imagePreviewModalRef = ref(null)
const showTypePanel = ref(true)

const presetCounts = [4, 8, 12, 16, 20, 36]
let pollTimer = null
let accountRefreshTimer = null

const imageTypes = ref([])

const imageStyles = ref([])

const filteredTypes = computed(() => imageTypes.value)
const typesHasCover = computed(() => imageTypes.value.some((item) => item.cover))
const selectedTypeObj = computed(() => imageTypes.value.find((item) => item.value === selectedType.value))
const selectedTypeLabel = computed(() => selectedTypeObj.value?.label || '')
const selectedTypeEmoji = computed(() => selectedTypeObj.value?.emoji || '')
const selectedStyleLabel = computed(() => {
  if (!selectedStyle.value) return ''
  return imageStyles.value.find((item) => item.value === selectedStyle.value)?.label || ''
})
const currentTaskIcon = computed(() => {
  const status = String(currentTask.value?.status || '').toLowerCase()
  if (status === 'completed') return 'check_circle'
  if (status === 'error') return 'error'
  return 'progress_activity'
})
const currentTaskBadgeClass = computed(() => {
  const status = String(currentTask.value?.status || '').toLowerCase()
  if (status === 'completed') return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  if (status === 'error') return 'bg-red-50 text-red-500 border border-red-200'
  return 'bg-primary/10 text-primary border border-primary/15'
})

function normalizePreviewEntry(image, index = 0, promptText = '') {
  if (!image) return null

  const rawUrl = typeof image === 'string' ? image : image.url || image.src || ''
  const url = resolveImageSrc(rawUrl)
  if (!url) return null

  const baseAlt = extractDisplayPrompt(promptText || '') || '生成图片'
  return {
    url,
    alt: typeof image === 'string'
      ? `${baseAlt} ${index + 1}`
      : image.alt || image.name || `${baseAlt} ${index + 1}`,
  }
}

function normalizeTaskImages(task) {
  let images = []

  if (Array.isArray(task?.images) && task.images.length > 0) {
    images = task.images
  } else if (typeof task?.images === 'string') {
    try {
      images = JSON.parse(task.images)
    } catch {
      images = []
    }
  } else if (Array.isArray(task?.result) && task.result.length > 0) {
    images = task.result
  }

  return images
    .map((image, index) => normalizePreviewEntry(image, index, currentTask.value?.prompt))
    .filter(Boolean)
}

function buildRecordPreviewItems(record) {
  const images = Array.isArray(record?.image_urls) ? record.image_urls : []
  return images
    .map((image, index) => normalizePreviewEntry(image, index, record?.prompt))
    .filter(Boolean)
}

function mergeUniqueImages(existingImages, incomingImages) {
  const seen = new Set()
  return [...existingImages, ...incomingImages].filter((image) => {
    const key = image?.url
    if (!key || seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function resultGridClass(count) {
  if (count <= 1) return 'grid-cols-1'
  if (count === 2) return 'grid-cols-1 md:grid-cols-2'
  return 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3'
}

function handlePreviewImageFallback(event) {
  handleImageFallback(event)
}

function openPreviewItems(items, startIndex = 0) {
  if (!Array.isArray(items) || items.length === 0) return
  imagePreviewModalRef.value?.show(items, startIndex)
}

function openCurrentTaskPreview(index = 0) {
  openPreviewItems(currentTask.value?.images || [], index)
}

function openRecordPreview(record, index = 0) {
  openPreviewItems(buildRecordPreviewItems(record), index)
}

function getRecordImage(record) {
  return buildRecordPreviewItems(record)[0]?.url || ''
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function clearAccountRefreshTimer() {
  if (accountRefreshTimer) {
    clearTimeout(accountRefreshTimer)
    accountRefreshTimer = null
  }
}

function applyBillingSnapshot(billing) {
  if (!authStore.isAuthenticated || !authStore.accountInfo || !billing?.balance_after) return

  const nextBalance = Number(billing.balance_after.balance)
  const nextPoints = billing.balance_after.points ?? authStore.accountInfo.points ?? 0
  const nextGiftPoints = billing.balance_after.gift_points ?? authStore.accountInfo.gift_points ?? 0

  authStore.accountInfo = {
    ...authStore.accountInfo,
    points: nextPoints,
    gift_points: nextGiftPoints,
    balance: Number.isFinite(nextBalance)
      ? Math.round(nextBalance * 100)
      : authStore.accountInfo.balance,
    total_points: nextPoints + nextGiftPoints,
  }
}

function scheduleAccountRefresh(billing) {
  applyBillingSnapshot(billing)
  clearAccountRefreshTimer()
  accountRefreshTimer = setTimeout(async () => {
    accountRefreshTimer = null
    try {
      await authStore.fetchAccountInfo()
    } catch (error) {
      console.warn('刷新积分失败:', error)
    }
  }, 260)
}

async function loadTypesStyles() {
  try {
    const response = await fetch('/api/v1/admin/system-config/types-styles')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    imageTypes.value = Array.isArray(data.types) ? data.types : []
    imageStyles.value = Array.isArray(data.styles) ? data.styles : []

    if (!imageTypes.value.find((item) => item.value === selectedType.value)) {
      selectedType.value = imageTypes.value[0]?.value || ''
    }
    if (!imageStyles.value.find((item) => item.value === selectedStyle.value)) {
      selectedStyle.value = imageStyles.value[0]?.value || ''
    }
  } catch {
    imageTypes.value = []
    imageStyles.value = []
    selectedType.value = ''
    selectedStyle.value = ''
  }
}

async function loadGallery() {
  galleryLoading.value = true
  try {
    const records = await api.getUnifiedGenerationHistory(10, 0, 'completed')
    galleryRecords.value = (records || []).filter((record) => buildRecordPreviewItems(record).length > 0)
  } catch {
    try {
      const records = await api.getGenerationHistory(10, 0, 'completed')
      galleryRecords.value = (records || []).filter((record) => buildRecordPreviewItems(record).length > 0)
    } catch {
      galleryRecords.value = []
    }
  } finally {
    galleryLoading.value = false
  }
}

function applyTutorialExample(example) {
  if (!example) return

  promptInput.value = example.prompt
  selectedType.value = example.type
  selectedStyle.value = example.style
  batchCount.value = example.count
  showTypePanel.value = true
  activeTab.value = 'type'

  nextTick(() => {
    promptRef.value?.focus?.()
  })

  notification.success('已填入示例', `${example.title} 已写入输入框`)
}

async function syncRouteExample(exampleId) {
  if (typeof exampleId !== 'string' || !exampleId) return

  const example = getTutorialExampleById(exampleId)
  if (!example) return

  applyTutorialExample(example)

  const nextQuery = { ...route.query }
  delete nextQuery.example
  await router.replace({ path: route.path, query: nextQuery })
}

function getFileIcon(file) {
  const ext = file.name.split('.').pop().toLowerCase()
  if (ext === 'pdf') return 'picture_as_pdf'
  if (['doc', 'docx'].includes(ext)) return 'description'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) return 'image'
  return 'insert_drive_file'
}

function handleUploadChange(uploadFile) {
  const file = uploadFile?.raw || uploadFile
  if (!file) return

  attachments.value.push(file)
  uploadRef.value?.clearFiles?.()

  if (file.name.toLowerCase().endsWith('.pdf')) {
    import('pdfjs-dist')
      .then(async ({ getDocument }) => {
        try {
          const buffer = await file.arrayBuffer()
          const pdf = await getDocument({ data: buffer }).promise
          const pages = Math.min(pdf.numPages, 20)
          batchCount.value = pages
          notification.info('PDF 已识别', `共 ${pdf.numPages} 页，将生成 ${pages} 张图片`)
        } catch {
          // ignore
        }
      })
      .catch(() => {})
  }
}

async function copyPrompt(text) {
  const ok = await copyText(extractDisplayPrompt(text))
  if (ok) {
    notification.success('已复制', '提示词已复制到剪贴板')
  } else {
    notification.error('复制失败', '')
  }
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleDateString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function startSingleTaskPolling(taskId) {
  stopPolling()
  let attempts = 0
  const maxAttempts = 300

  pollTimer = setInterval(async () => {
    attempts += 1

    if (attempts > maxAttempts) {
      stopPolling()
      if (currentTask.value) {
        currentTask.value.status = currentTask.value.images.length > 0 ? 'completed' : 'error'
        currentTask.value.statusText = currentTask.value.images.length > 0
          ? `生成完成！共 ${currentTask.value.images.length} 张图片（部分超时）`
          : '生成超时'
        currentTask.value.error = currentTask.value.images.length > 0 ? '' : '任务超时，请重试'
        currentTask.value.progress = 100
        currentTask.value.progressText = '轮询超时'
      }
      isGenerating.value = false
      void authStore.fetchAccountInfo().catch(() => {})
      void loadGallery()
      return
    }

    try {
      const task = await api.getTaskStatus(taskId)
      const status = String(task?.status || '').toLowerCase()
      if (!currentTask.value) return

      if (status === 'completed') {
        stopPolling()
        const images = normalizeTaskImages(task)
        currentTask.value.images = mergeUniqueImages(currentTask.value.images, images)
        currentTask.value.status = 'completed'
        currentTask.value.statusText = `生成完成！共 ${currentTask.value.images.length} 张图片`
        currentTask.value.progress = 100
        currentTask.value.progressText = '处理完成'
        currentTask.value.error = ''
        isGenerating.value = false
        if (task?.billing) scheduleAccountRefresh(task.billing)
        void loadGallery()
        return
      }

      if (status === 'failed' || status === 'error') {
        stopPolling()
        currentTask.value.status = 'error'
        currentTask.value.statusText = '生成失败'
        currentTask.value.error = task?.error || '图像生成失败，请重试'
        currentTask.value.progress = 100
        currentTask.value.progressText = '任务失败'
        isGenerating.value = false
        if (task?.billing) scheduleAccountRefresh(task.billing)
        return
      }

      const progress = Math.min(90, Math.round((attempts / maxAttempts) * 100))
      currentTask.value.progress = progress
      currentTask.value.progressText = `${task?.stage || task?.status || '处理中'}...`
      currentTask.value.statusText = '正在生成中...'
    } catch (error) {
      console.warn('轮询任务状态失败:', error?.message || error)
    }
  }, 2000)
}

function startMultiTaskPolling(taskIds) {
  stopPolling()
  let attempts = 0
  const maxAttempts = 300
  const completedTaskIds = new Set()
  const failedTaskIds = new Set()

  pollTimer = setInterval(async () => {
    attempts += 1

    if (attempts > maxAttempts) {
      stopPolling()
      if (currentTask.value) {
        currentTask.value.status = currentTask.value.images.length > 0 ? 'completed' : 'error'
        currentTask.value.statusText = currentTask.value.images.length > 0
          ? `生成完成！共 ${currentTask.value.images.length} 张图片（部分超时）`
          : '生成超时'
        currentTask.value.error = currentTask.value.images.length > 0 ? '' : '任务超时，请重试'
        currentTask.value.progress = 100
        currentTask.value.progressText = '轮询超时'
      }
      isGenerating.value = false
      void authStore.fetchAccountInfo().catch(() => {})
      void loadGallery()
      return
    }

    for (const taskId of taskIds) {
      if (completedTaskIds.has(taskId) || failedTaskIds.has(taskId)) continue

      try {
        const task = await api.getTaskStatus(taskId)
        const status = String(task?.status || '').toLowerCase()

        if (status === 'completed') {
          completedTaskIds.add(taskId)
          const incomingImages = normalizeTaskImages(task)
          if (currentTask.value) {
            currentTask.value.images = mergeUniqueImages(currentTask.value.images, incomingImages)
          }
          if (task?.billing) scheduleAccountRefresh(task.billing)
        } else if (status === 'failed' || status === 'error') {
          failedTaskIds.add(taskId)
          if (task?.billing) scheduleAccountRefresh(task.billing)
        }
      } catch {
        // keep polling
      }
    }

    if (!currentTask.value) return

    const doneCount = completedTaskIds.size + failedTaskIds.size
    const totalCount = taskIds.length

    currentTask.value.progress = 25 + Math.round((doneCount / totalCount) * 75)
    currentTask.value.progressText = `已完成 ${completedTaskIds.size}/${totalCount} 张`
    currentTask.value.statusText = `正在生成中... (${completedTaskIds.size}/${totalCount})`

    if (doneCount >= totalCount) {
      stopPolling()
      currentTask.value.status = completedTaskIds.size > 0 ? 'completed' : 'error'
      currentTask.value.statusText = completedTaskIds.size > 0
        ? `生成完成！共 ${currentTask.value.images.length} 张图片`
        : '全部生成失败'
      currentTask.value.error = completedTaskIds.size === 0 ? '图像生成失败，请重试' : ''
      currentTask.value.progress = 100
      currentTask.value.progressText = completedTaskIds.size > 0 ? '处理完成' : '处理失败'
      isGenerating.value = false
      void authStore.fetchAccountInfo().catch(() => {})
      void loadGallery()
    }
  }, 2000)
}

async function startBatchGeneration() {
  if ((!promptInput.value.trim() && attachments.value.length === 0) || isGenerating.value) return

  isGenerating.value = true

  const typeLabel = imageTypes.value.find((item) => item.value === selectedType.value)?.label || ''
  const styleLabel = imageStyles.value.find((item) => item.value === selectedStyle.value)?.label || ''

  let fullPrompt = promptInput.value.trim()
  if (typeLabel) fullPrompt += `\n类型：${typeLabel}`
  if (styleLabel) fullPrompt += `\n风格：${styleLabel}`

  currentTask.value = {
    status: 'generating',
    statusText: '正在提交生成任务...',
    progress: 5,
    progressText: '提交中...',
    total: batchCount.value,
    images: [],
    prompt: fullPrompt,
    error: '',
  }

  try {
    let uploadedFileUrls = []
    if (attachments.value.length > 0) {
      currentTask.value.progressText = '正在上传文件...'
      try {
        const uploadResults = await api.uploadFiles([...attachments.value], (progress, current, total) => {
          if (!currentTask.value) return
          currentTask.value.progressText = `上传文件 (${current}/${total}) ${progress}%`
        })
        uploadedFileUrls = uploadResults.map((file) => file.url).filter(Boolean)
        notification.success('文件上传成功', `已上传 ${uploadedFileUrls.length} 个文件`)
      } catch (error) {
        currentTask.value.status = 'error'
        currentTask.value.statusText = '文件上传失败'
        currentTask.value.error = error?.response?.data?.detail || error?.message || '上传失败'
        currentTask.value.progress = 100
        currentTask.value.progressText = '上传失败'
        isGenerating.value = false
        return
      }
    }

    const uploadedFileNames = attachments.value.map((file) => file.name)
    if (uploadedFileUrls.length > 0) {
      fullPrompt = `请参考我上传的图片/文件内容来生成图片。${fullPrompt}`
      currentTask.value.prompt = fullPrompt
      currentTask.value.progressText = `已上传 ${uploadedFileNames.join('、')}，正在提交任务...`
    }

    const taskIds = []
    for (let index = 0; index < batchCount.value; index += 1) {
      const itemPrompt = `${fullPrompt}\n这是第${index + 1}/${batchCount.value}张`
      const messages = []

      if (uploadedFileUrls.length > 0 && index === 0) {
        messages.push({
          role: 'user',
          content: `我上传了以下文件作为参考：${uploadedFileNames.join('、')}，请基于文件内容来生成图片。`,
        })
        messages.push({
          role: 'assistant',
          content: '好的，我已收到您的文件，将基于文件内容为您生成图片。',
        })
      }

      messages.push({ role: 'user', content: itemPrompt })

      const chatRequest = {
        messages,
        session_id: `multi_${Date.now()}_${index}`,
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
        },
      }

      try {
        const response = await api.assistantChat(chatRequest)
        const taskId = response.task_id || response.batch_id
        if (taskId) taskIds.push(taskId)
        if (response.metadata?.billing) scheduleAccountRefresh(response.metadata.billing)
      } catch (error) {
        console.warn(`第${index + 1}张提交失败:`, error?.message || error)
      }

      if (currentTask.value) {
        currentTask.value.progress = Math.round(((index + 1) / batchCount.value) * 20)
        currentTask.value.progressText = `已提交 ${index + 1}/${batchCount.value} 张...`
      }
    }

    if (taskIds.length === 0) throw new Error('所有任务提交失败')

    currentTask.value.statusText = `正在生成 ${taskIds.length} 张图片...`
    currentTask.value.progress = 25
    currentTask.value.progressText = '等待生成结果...'

    if (taskIds.length === 1) {
      startSingleTaskPolling(taskIds[0])
    } else {
      startMultiTaskPolling(taskIds)
    }
  } catch (error) {
    currentTask.value.status = 'error'
    currentTask.value.statusText = '提交失败'
    currentTask.value.error = error?.response?.data?.detail || error?.message || '请稍后重试'
    currentTask.value.progress = 100
    currentTask.value.progressText = '提交失败'
    isGenerating.value = false
  }
}

watch(() => route.query.example, (exampleId) => {
  void syncRouteExample(exampleId)
}, { immediate: true })

onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.accountInfo) {
    void authStore.fetchAccountInfo().catch(() => {})
  }

  if (generatorStore.availableModels.length === 0) {
    await generatorStore.fetchAvailableModels()
  }

  await Promise.all([loadGallery(), loadTypesStyles()])
})

onUnmounted(() => {
  stopPolling()
  clearAccountRefreshTimer()
})
</script>

<style scoped>
.multi-view {
  background:
    radial-gradient(circle at top right, rgba(140, 42, 46, 0.16), transparent 24%),
    radial-gradient(circle at top left, rgba(179, 134, 0, 0.12), transparent 22%),
    linear-gradient(180deg, rgba(255, 252, 251, 0.94) 0%, rgba(247, 241, 239, 0.98) 100%);
}

.glass-panel {
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 24px 72px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(16px);
}

.result-card {
  overflow: hidden;
  border-radius: 1.4rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
}

.result-card__canvas {
  display: flex;
  min-height: 280px;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at top, rgba(20, 86, 240, 0.09), transparent 52%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(245, 246, 250, 0.96));
  padding: 1.1rem;
}

.result-card--placeholder {
  position: relative;
}

.result-card__skeleton {
  position: relative;
  min-height: 280px;
  overflow: hidden;
  background:
    linear-gradient(120deg, rgba(20, 86, 240, 0.07), rgba(255, 255, 255, 0.7), rgba(20, 86, 240, 0.05));
}

.result-card__skeleton-orb {
  position: absolute;
  border-radius: 999px;
  background: rgba(20, 86, 240, 0.12);
  filter: blur(6px);
}

.result-card__skeleton-orb--one {
  top: 18%;
  left: 18%;
  height: 5rem;
  width: 5rem;
}

.result-card__skeleton-orb--two {
  right: 14%;
  bottom: 18%;
  height: 6rem;
  width: 6rem;
}

.result-card__skeleton-panel {
  position: absolute;
  inset: 18% 14%;
  border-radius: 1.4rem;
  border: 1px solid rgba(255, 255, 255, 0.55);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: inset 0 0 0 1px rgba(20, 86, 240, 0.04);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
</style>
