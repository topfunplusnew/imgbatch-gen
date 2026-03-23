<template>
  <main class="flex-1 flex flex-col bg-background-dark min-h-screen overflow-y-auto">
    <!-- Hero Section -->
    <div class="flex-1 flex flex-col items-center justify-center px-4 xs:px-6 md:px-8 py-12 md:py-16 text-center">
      <!-- Logo -->
      <div class="mb-8 md:mb-12">
        <div class="flex items-center justify-center mb-4">
          <div class="w-16 h-16 bg-gradient-to-br from-primary to-primary-deep rounded-full flex items-center justify-center mr-4">
            <span class="material-symbols-outlined !text-3xl text-white">auto_awesome</span>
          </div>
          <h1 class="text-3xl md:text-4xl font-bold text-ink-950">AI 图像生成助手</h1>
        </div>
        <p class="text-base md:text-lg text-ink-500 max-w-2xl mx-auto">
          强大的AI图像生成工具，支持多种模型和风格，轻松创建您想要的图像
        </p>
      </div>

      <!-- 通知轮播 -->
      <div class="w-full mb-6">
        <NotificationCarousel ref="notificationCarouselRef" :autoplay="true" :autoplay-interval="5000" :max-items="3" />
      </div>

      <!-- Quick Input Area -->
      <div class="w-full">
        <div
          class="bg-white rounded-xl shadow-lg border border-border-dark p-4 md:p-6"
          @mouseenter="handleInputFocus"
          @mouseleave="handleInputBlur">
          <!-- Quick input with file attachment -->
          <div class="flex items-center mb-4">
            <input
              ref="fileInputRef"
              type="file"
              multiple
              accept=".pdf,.docx,.jpg,.jpeg,.png,.gif,.webp,.bmp,.svg"
              @change="handleFileSelect"
              class="hidden">

            <button
              @click="triggerFileSelect"
              class="flex items-center gap-2 px-4 py-2 bg-primary-soft text-primary rounded-lg hover:bg-primary/20 transition-colors">
              <span class="material-symbols-outlined !text-xl">attach_file</span>
              <span class="text-sm font-medium">上传文件</span>
            </button>
          </div>

          <!-- File attachments preview -->
          <div v-if="attachments.length > 0" class="flex flex-wrap gap-2 mb-4">
            <div
              v-for="(file, index) in attachments"
              :key="index"
              class="relative flex items-center gap-2 px-3 py-2 bg-primary-soft border border-primary/20 rounded-lg">
              <span class="material-symbols-outlined !text-lg text-primary">
                {{ getFileIcon(file) }}
              </span>
              <span class="text-xs text-ink-700 max-w-[100px] truncate">{{ file.name }}</span>
              <button
                @click="removeFile(index)"
                class="text-ink-500 hover:text-red-500 transition-colors">
                <span class="material-symbols-outlined !text-sm">close</span>
              </button>
            </div>
          </div>

          <!-- Text input -->
          <textarea
            ref="promptInputRef"
            v-model="promptInput"
            @input="handlePromptInput"
            @focus="handleInputFocus"
            @blur="handleInputBlur"
            class="w-full bg-gray-50 border border-border-dark rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
            rows="3"
            placeholder="描述您想要创建的图像，或点击上传参考文件..."
          ></textarea>

          <!-- Parameter Controls & Start Button Row -->
          <div class="flex items-center gap-2 xs:gap-3 mt-4">
            <ModelDropdown class="shrink-0" />
            <RatioDropdown class="shrink-0" />
            <ResolutionDropdown class="shrink-0" />
            <div class="flex-1 min-w-0"></div>
            <button
              @click="startGeneration"
              :disabled="!promptInput.trim() && attachments.length === 0"
              class="flex items-center gap-2 px-4 xs:px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-strong disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg shrink-0">
              <span class="material-symbols-outlined !text-xl">auto_awesome</span>
              <span class="font-medium hidden sm:inline">开始生成</span>
            </button>
          </div>

          <!-- Supported formats hint -->
          <div class="text-xs text-ink-500 mt-2">
            支持：PDF、Word、图片等格式
          </div>
        </div>
      </div>
    </div>

    <!-- Category Templates Section -->
    <div class="px-4 xs:px-6 md:px-8 pb-8 md:pb-12">
      <div class="w-full">
        <!-- Header with view all button -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="text-lg font-semibold text-ink-950">模板分类</h3>
            <p class="text-sm text-ink-500">按分类浏览精选模板</p>
          </div>
          <button
            @click="openTemplates"
            class="text-sm text-primary hover:text-primary-strong font-medium">
            查看全部 →
          </button>
        </div>

        <!-- Loading state -->
        <div v-if="loading && cases.length === 0" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>

        <!-- Category Groups -->
        <div v-else class="space-y-8">
          <!-- All Templates Group -->
          <div class="category-group">
            <h4 class="text-base font-semibold text-ink-950 mb-4">全部模板</h4>
            <!-- Horizontal scroll cards -->
            <div class="flex gap-4 overflow-x-auto pb-4 scrollbar-hide scroll-smooth -mx-4 px-4">
              <div
                v-for="caseItem in cases.slice(0, 10)"
                :key="caseItem.id"
                @click="selectTemplate(caseItem)"
                class="flex-shrink-0 w-48 xs:w-56 group relative rounded-lg overflow-hidden border border-border-dark hover:border-primary/50 hover:shadow-lg transition-all duration-200 bg-white cursor-pointer"
              >
                <div class="aspect-video relative">
                  <img
                    :src="caseItem.thumbnail_url || caseItem.image_url || '/placeholder-case.png'"
                    :alt="caseItem.title"
                    class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    @error="handleImageError"
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
              </div>
            </div>
          </div>

          <!-- Individual Category Groups -->
          <div
            v-for="category in categories"
            :key="category"
            class="category-group"
          >
            <h4 class="text-base font-semibold text-ink-950 mb-4">{{ category }}</h4>
            <!-- Horizontal scroll cards for this category -->
            <div class="flex gap-4 overflow-x-auto pb-4 scrollbar-hide scroll-smooth -mx-4 px-4">
              <div
                v-for="caseItem in getCasesByCategory(category)"
                :key="caseItem.id"
                @click="selectTemplate(caseItem)"
                class="flex-shrink-0 w-48 xs:w-56 group relative rounded-lg overflow-hidden border border-border-dark hover:border-primary/50 hover:shadow-lg transition-all duration-200 bg-white cursor-pointer"
              >
                <div class="aspect-video relative">
                  <img
                    :src="caseItem.thumbnail_url || caseItem.image_url || '/placeholder-case.png'"
                    :alt="caseItem.title"
                    class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    @error="handleImageError"
                  >
                  <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                </div>
                <div class="p-3">
                  <h5 class="text-sm font-medium text-ink-950 line-clamp-1 mb-1">{{ caseItem.title }}</h5>
                  <p class="text-xs text-ink-500 line-clamp-2">{{ caseItem.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="cases.length === 0 && !loading" class="text-center py-12">
          <span class="material-symbols-outlined !text-6xl text-ink-300 mb-4 block">search_off</span>
          <p class="text-sm text-ink-500">暂无模板</p>
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

const appStore = useAppStore()
const generatorStore = useGeneratorStore()
const caseStore = useCaseStore()

const promptInput = ref('')
const promptInputRef = ref(null)
const fileInputRef = ref(null)
const notificationCarouselRef = ref(null)
const attachments = ref([])
const hasStartedTyping = ref(false)

// Get categories from caseStore
const categories = computed(() => caseStore.categories || [])

// Get cases from caseStore
const cases = computed(() => caseStore.cases || [])
const loading = computed(() => caseStore.loading || false)

// Get cases by category
const getCasesByCategory = (category) => {
  return cases.value.filter(c => c.category === category).slice(0, 10)
}

// Select template and switch to generate view
const selectTemplate = (caseItem) => {
  appStore.setSelectedCase(caseItem)
  // Switch to chat view to show details
  appStore.setCurrentView('chat')
}

// Handle prompt input - switch to chat view when user starts typing
const handlePromptInput = () => {
  if (!hasStartedTyping.value && promptInput.value.trim().length > 0) {
    hasStartedTyping.value = true
  }

  // If user has typed something, switch to chat view
  if (promptInput.value.trim().length > 0 && appStore.currentView === 'landing') {
    appStore.setCurrentView('chat')
    // Keep the prompt in the generator store
    generatorStore.prompt = promptInput.value
  }
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
  }
})

// Trigger file selection
const triggerFileSelect = () => {
  fileInputRef.value?.click()
}

// Handle file selection
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files || [])

  files.forEach(file => {
    // Validate file type
    if (!validateFileType(file)) {
      alert(`文件 "${file.name}" 格式不支持。\n支持格式：PDF、Word (.docx)、图片 (.jpg, .png, .gif, .webp, .bmp, .svg)`)
      return
    }
    attachments.value.push(file)
  })

  // Clear input
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }

  // Switch to chat view when files are added
  if (attachments.value.length > 0 && appStore.currentView === 'landing') {
    appStore.setCurrentView('chat')
    attachments.value.forEach(file => {
      generatorStore.addAttachment(file)
    })
    attachments.value = []
  }
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

// Handle image error
const handleImageError = (event) => {
  event.target.src = '/placeholder-case.png'
}

// Start generation
const startGeneration = () => {
  // Transfer prompt and attachments to generator store
  generatorStore.prompt = promptInput.value
  attachments.value.forEach(file => {
    generatorStore.addAttachment(file)
  })

  // Switch to chat view
  appStore.setCurrentView('chat')

  // Clear landing inputs
  promptInput.value = ''
  attachments.value = []
  hasStartedTyping.value = false
}

// Open templates
const openTemplates = () => {
  appStore.toggleTemplateDrawer()
}

// Initialize cases on mount
onMounted(() => {
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
