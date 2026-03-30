<template>
  <main class="flex-1 flex h-full min-h-0 flex-col bg-background-dark overflow-y-auto">
    <!-- 系统公告 - 页面顶部 -->
    <div class="flex-shrink-0">
      <NotificationCarousel ref="notificationCarouselRef" :autoplay="true" :autoplay-interval="5000" :max-items="3" />
    </div>

    <div class="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-border-dark bg-white/80 px-4 py-3 backdrop-blur-xl md:hidden xs:px-6">
      <el-button circle @click="emit('toggleSidebar')" aria-label="Open sidebar">
        <span class="material-symbols-outlined !text-xl">menu</span>
      </el-button>
      <div class="min-h-[44px] min-w-[44px] shrink-0"></div>
    </div>

    <!-- Hero Section -->
    <div class="px-4 xs:px-6 md:px-8 pt-8 md:pt-12 pb-8 md:pb-12">
      <div class="text-center mb-6 md:mb-8">
        <h1 class="mx-auto max-w-3xl text-2xl font-semibold tracking-tight text-ink-950 md:text-4xl">
          {{ heroPrompt }}
        </h1>
        <p class="text-sm md:text-base text-ink-500 max-w-2xl mx-auto">
          强大的AI图像生成工具，支持多种模型和风格，轻松创建您想要的图像
        </p>
      </div>

      <!-- Quick Input Area -->
      <div class="mx-auto w-full min-w-[320px] max-w-[960px] md:max-w-[72%] xl:max-w-[68%]">
        <el-card
          shadow="never"
          class="landing-input-card"
          @mouseenter="handleInputFocus"
          @mouseleave="handleInputBlur"
        >
          <!-- Quick input with file attachment -->
          <div class="mb-4 flex items-center justify-between gap-3">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :show-file-list="false"
              :multiple="true"
              accept=".pdf,.docx,.jpg,.jpeg,.png,.gif,.webp,.bmp,.svg"
              :on-change="handleUploadChange"
            >
              <el-button>
                <span class="material-symbols-outlined !text-lg">attach_file</span>
                <span>上传文件</span>
              </el-button>
            </el-upload>

            <el-tag round effect="plain" class="hidden sm:inline-flex">支持 PDF / Word / 图片</el-tag>
          </div>

          <!-- File attachments preview -->
          <div v-if="attachments.length > 0" class="mb-4 flex flex-wrap gap-2">
            <div
              v-for="(file, index) in attachments"
              :key="index"
              class="relative flex items-center gap-2 rounded-2xl border border-primary/20 bg-primary-soft px-3 py-2">
              <span class="material-symbols-outlined !text-lg text-primary">
                {{ getFileIcon(file) }}
              </span>
              <span class="max-w-[120px] truncate text-xs text-ink-700">{{ file.name }}</span>
              <el-button circle text @click="removeFile(index)">
                <span class="material-symbols-outlined !text-sm">close</span>
              </el-button>
            </div>
          </div>

          <!-- Text input -->
          <el-input
            ref="promptInputRef"
            v-model="promptInput"
            type="textarea"
            :rows="7"
            @focus="handleInputFocus"
            @blur="handleInputBlur"
            placeholder="您有什么想法"
            @input="handlePromptInput"
          />

          <!-- Parameter Controls & Start Button Row -->
          <div class="mt-4 flex flex-wrap items-center gap-2 xs:flex-nowrap">
            <ModelDropdown class="shrink-0" />
            <el-divider direction="vertical" class="!hidden xs:!block" />
            <RatioDropdown class="shrink-0" />
            <ResolutionDropdown class="shrink-0" />
            <div class="flex-1 min-w-0"></div>
            <el-button
              @click="startGeneration"
              :disabled="!promptInput.trim() && attachments.length === 0"
              type="primary"
              round
              class="shrink-0"
            >
              <span class="material-symbols-outlined !text-xl">auto_awesome</span>
              <span class="font-medium hidden xs:inline">发送</span>
            </el-button>
          </div>

          <!-- Supported formats hint -->
          <div class="text-xs text-ink-500 mt-2">
            支持：PDF、Word、图片等格式
          </div>
        </el-card>
      </div>
    </div>

    <!-- Category Templates Section -->
    <div class="px-4 xs:px-6 md:px-8 pb-8 md:pb-12">
      <div class="w-full">
        <!-- Header with view all button -->
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-ink-950">模板分类</h3>
          <el-button text @click="openTemplates">查看全部</el-button>
        </div>

        <!-- Category Filter Buttons -->
        <div class="flex items-center gap-2 mb-6 flex-wrap">
          <el-button
            @click="selectedCategory = null"
            :type="selectedCategory === null ? 'primary' : 'default'"
            :plain="selectedCategory !== null"
          >
            全部
          </el-button>
          <el-button
            v-for="category in categories"
            :key="category"
            @click="selectedCategory = category"
            :type="selectedCategory === category ? 'primary' : 'default'"
            :plain="selectedCategory !== category"
          >
            {{ category }}
          </el-button>
        </div>

        <!-- Loading state -->
        <div v-if="loading && cases.length === 0" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>

        <!-- Category Groups -->
        <div v-else class="space-y-8">
          <!-- All Templates Group -->
          <div class="category-group">
            <h4 class="text-base font-semibold text-ink-950 mb-4">
              {{ selectedCategory || '全部模板' }}
            </h4>
            <!-- Horizontal scroll cards -->
            <div v-if="filteredCases.length > 0" class="flex gap-4 overflow-x-auto pb-4 scrollbar-hide scroll-smooth -mx-4 px-4">
              <el-card
                v-for="caseItem in filteredCases.slice(0, 10)"
                :key="caseItem.id"
                @click="selectTemplate(caseItem)"
                shadow="hover"
                class="landing-template-card group relative w-48 flex-shrink-0 cursor-pointer overflow-hidden xs:w-56"
              >
                <div class="aspect-video relative">
                  <img
                    :src="getCaseImageSources(caseItem)[0]"
                    :data-fallback-src="getCaseImageSources(caseItem)[1] || ''"
                    :alt="caseItem.title"
                    class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    @error="handleImageFallback"
                  >
                  <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <div class="absolute bottom-2 left-2 right-2">
                    <span class="text-xs text-white font-medium px-2 py-1 bg-black/50 rounded backdrop-blur-sm">
                      {{ caseItem.category }}
                    </span>
                  </div>
                </div>
                <div class="p-3">
                  <h5 class="text-sm font-medium text-ink-950 line-clamp-1 mb-1">{{ caseItem.title }}</h5>
                  <p class="text-xs text-ink-500 line-clamp-2">{{ caseItem.description }}</p>
                </div>
              </el-card>
            </div>
            <el-empty v-else description="暂无模板" :image-size="60" />
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { useCaseStore } from '@/store/useCaseStore'
import NotificationCarousel from '@/components/NotificationCarousel.vue'
import ModelDropdown from '@/components/landing/ModelDropdown.vue'
import RatioDropdown from '@/components/landing/RatioDropdown.vue'
import ResolutionDropdown from '@/components/landing/ResolutionDropdown.vue'
import { handleImageFallback, resolveImageSrcCandidates } from '@/utils/imageFallback'

const appStore = useAppStore()
const generatorStore = useGeneratorStore()
const caseStore = useCaseStore()
const emit = defineEmits(['toggleSidebar', 'toggleSettings'])

const promptInput = ref('')
const promptInputRef = ref(null)
const uploadRef = ref(null)
const notificationCarouselRef = ref(null)
const attachments = ref([])
const hasStartedTyping = ref(false)
const selectedCategory = ref(null)
const heroPrompt = ref('你在做什么？')
let uploadSwitchTimer = null

const heroPrompts = [
  '你在做什么？',
  '今天想生成什么画面？',
  '把脑海里的灵感说给我听。',
  '这次想尝试什么新风格？',
  '你想先从一句描述开始吗？',
  '有没有一张你一直想做出来的图？'
]

// Get categories from caseStore
const categories = computed(() => caseStore.categories || [])

// Get cases from caseStore
const cases = computed(() => caseStore.cases || [])
const loading = computed(() => caseStore.loading || false)

// Filtered cases based on selected category
const filteredCases = computed(() => {
  if (!selectedCategory.value) {
    return cases.value
  }
  return cases.value.filter(c => c.category === selectedCategory.value)
})

const getCaseImageSources = (caseItem) => {
  return resolveImageSrcCandidates(caseItem?.thumbnail_url, caseItem?.image_url)
}

// Select template and switch to generate view
const selectTemplate = (caseItem) => {
  appStore.setSelectedCase(caseItem)
  // Switch to chat view to show details
  appStore.setCurrentView('chat')
}

// Handle prompt input - sync prompt to store, don't switch view
const handlePromptInput = () => {
  if (!hasStartedTyping.value && promptInput.value.trim().length > 0) {
    hasStartedTyping.value = true
  }
  // 同步 prompt 到 store，但不切换视图
  generatorStore.prompt = promptInput.value
}

// Pause notification carousel when input is focused
const handleInputFocus = () => {
  notificationCarouselRef.value?.pauseAutoplay()
}

// Resume notification carousel when input loses focus
const handleInputBlur = () => {
  notificationCarouselRef.value?.resumeAutoplay()
}

// Watch for view changes to sync prompt
watch(() => appStore.currentView, (newView) => {
  if (newView === 'landing') {
    // Clear local state when returning to landing
    promptInput.value = ''
    hasStartedTyping.value = false
    heroPrompt.value = heroPrompts[Math.floor(Math.random() * heroPrompts.length)]
  }
})

// Handle file selection
const handleUploadChange = (uploadFile) => {
  const file = uploadFile?.raw || uploadFile
  if (!file) return

  if (!validateFileType(file)) {
    alert(`文件 "${file.name}" 格式不支持。\n支持格式：PDF、Word (.docx)、图片 (.jpg, .png, .gif, .webp, .bmp, .svg)`)
    uploadRef.value?.clearFiles?.()
    return
  }

  attachments.value.push(file)
  uploadRef.value?.clearFiles?.()

  if (uploadSwitchTimer) clearTimeout(uploadSwitchTimer)
  uploadSwitchTimer = setTimeout(() => {
    if (attachments.value.length > 0 && appStore.currentView === 'landing') {
      appStore.setCurrentView('chat')
      attachments.value.forEach(file => {
        generatorStore.addAttachment(file)
      })
      attachments.value = []
    }
  }, 0)
}

// Validate file type
const validateFileType = (file) => {
  const validTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
    'image/svg+xml'
  ]
  return validTypes.includes(file.type) || /\.(pdf|docx|jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(file.name)
}

// Get file icon
const getFileIcon = (file) => {
  const extension = file.name.split('.').pop().toLowerCase()

  if (['pdf'].includes(extension)) {
    return 'picture_as_pdf'
  } else if (['doc', 'docx'].includes(extension)) {
    return 'description'
  } else if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(extension)) {
    return 'image'
  }
  return 'insert_drive_file'
}

// Remove file
const removeFile = (index) => {
  attachments.value.splice(index, 1)
}

// Start generation
const startGeneration = () => {
  // Transfer prompt and attachments to generator store
  generatorStore.prompt = promptInput.value
  attachments.value.forEach(file => {
    generatorStore.addAttachment(file)
  })

  // 设置自动发送标记
  if (promptInput.value.trim() || generatorStore.attachments.length > 0) {
    generatorStore.setPendingAutoSend(true)
  }

  // Switch to chat view
  appStore.setCurrentView('chat')

  // Clear landing inputs
  promptInput.value = ''
  attachments.value = []
  hasStartedTyping.value = false
}

// Open templates
const openTemplates = () => {
  appStore.setCurrentView('templates')
}

// Initialize cases on mount
onMounted(() => {
  heroPrompt.value = heroPrompts[Math.floor(Math.random() * heroPrompts.length)]
  if (caseStore.cases.length === 0) {
    caseStore.initialize()
  }
  // Ensure models are loaded
  if (generatorStore.availableModels.length === 0) {
    generatorStore.fetchAvailableModels()
  }
})
</script>

<style scoped>
.landing-input-card {
  border-radius: 28px;
  border-color: var(--color-border-dark);
  box-shadow: 0 28px 56px rgba(88, 28, 32, 0.12);
}

.landing-input-card :deep(.el-card__body) {
  padding: 14px;
}

.landing-template-card {
  border-radius: 22px;
  border-color: var(--color-border-dark);
}

.landing-template-card :deep(.el-card__body) {
  padding: 0;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
