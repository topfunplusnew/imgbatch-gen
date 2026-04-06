<template>
  <section
    v-if="announcements.length > 0"
    class="notification-carousel"
    @mouseenter="pauseAutoplay"
    @mouseleave="resumeAutoplay"
  >
    <div class="notification-carousel__inner">
      <el-carousel
        ref="carouselRef"
        :autoplay="false"
        :loop="announcements.length > 1"
        arrow="never"
        height="132px"
        indicator-position="outside"
        @change="handleCarouselChange"
      >
        <el-carousel-item
          v-for="announcement in announcements"
          :key="announcement.id"
        >
          <el-card
            shadow="never"
            class="notification-carousel__card"
            @click="handleClick(announcement)"
          >
            <div class="notification-carousel__accent"></div>

            <div class="notification-carousel__content">
              <div class="notification-carousel__media">
                <el-image
                  v-if="announcement.cover_image_url"
                  :src="getImageUrl(announcement.cover_image_url)"
                  :alt="announcement.title"
                  fit="cover"
                  class="notification-carousel__image"
                >
                  <template #error>
                    <div class="notification-carousel__placeholder">
                      <el-icon :size="26"><Promotion /></el-icon>
                    </div>
                  </template>
                </el-image>

                <div v-else class="notification-carousel__placeholder">
                  <el-icon :size="26"><Promotion /></el-icon>
                </div>
              </div>

              <div class="min-w-0 flex-1">
                <div class="notification-carousel__meta">
                  <div class="notification-carousel__tags">
                    <el-tag
                      effect="plain"
                      size="small"
                      class="notification-carousel__tag"
                      :class="priorityTagClasses[announcement.priority]"
                    >
                      {{ getPriorityLabel(announcement.priority) }}
                    </el-tag>
                    <el-tag
                      v-if="announcement.is_pinned"
                      effect="plain"
                      size="small"
                      class="notification-carousel__tag notification-carousel__tag--pinned"
                    >
                      置顶
                    </el-tag>
                  </div>

                  <span class="notification-carousel__date">
                    {{ formatAnnouncementTime(announcement.published_at || announcement.created_at) }}
                  </span>
                </div>

                <div class="notification-carousel__title-row">
                  <el-icon class="notification-carousel__title-icon"><Bell /></el-icon>
                  <h3 class="notification-carousel__title">
                    {{ announcement.title }}
                  </h3>
                </div>

                <p class="notification-carousel__excerpt">
                  {{ stripHtml(announcement.content) }}
                </p>
              </div>

              <el-button
                text
                class="notification-carousel__action"
                @click.stop="handleClick(announcement)"
              >
                <span>查看</span>
                <el-icon :size="16"><ArrowRight /></el-icon>
              </el-button>
            </div>
          </el-card>
        </el-carousel-item>
      </el-carousel>

      <template v-if="announcements.length > 1">
        <el-button
          circle
          class="notification-carousel__nav notification-carousel__nav--prev"
          aria-label="上一张"
          @click.stop="previous"
        >
          <el-icon :size="18"><ArrowLeft /></el-icon>
        </el-button>

        <el-button
          circle
          class="notification-carousel__nav notification-carousel__nav--next"
          aria-label="下一张"
          @click.stop="next"
        >
          <el-icon :size="18"><ArrowRight /></el-icon>
        </el-button>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, Bell, Promotion } from '@element-plus/icons-vue'
import { useAppStore } from '@/store/useAppStore'
import { useNotificationStore, type Announcement } from '@/store/useNotificationStore'

const props = defineProps<{
  autoplay?: boolean
  autoplayInterval?: number
  maxItems?: number
}>()

const router = useRouter()
const appStore = useAppStore()
const notificationStore = useNotificationStore()

const announcements = ref<Announcement[]>([])
const currentIndex = ref(0)
const carouselRef = ref<any>(null)

let autoplayTimer: number | null = null
let isPaused = false

const priorityTagClasses: Record<Announcement['priority'], string> = {
  urgent: 'notification-carousel__tag--urgent',
  high: 'notification-carousel__tag--high',
  normal: 'notification-carousel__tag--normal',
  low: 'notification-carousel__tag--low',
}

function getPriorityLabel(priority: Announcement['priority']): string {
  const labels: Record<Announcement['priority'], string> = {
    urgent: '紧急',
    high: '重要',
    normal: '普通',
    low: '低',
  }

  return labels[priority] || '普通'
}

async function loadAnnouncements() {
  try {
    const items = await notificationStore.fetchPublicAnnouncements(1, props.maxItems || 5)
    const normalizedItems = Array.isArray(items)
      ? items
      : (items && Array.isArray(items.items) ? items.items : [])

    announcements.value = normalizedItems as Announcement[]
    currentIndex.value = 0
  } catch (error) {
    console.error('[NotificationCarousel] 加载公告失败:', error)
    announcements.value = []
  }
}

function setActiveItem(index: number) {
  currentIndex.value = index
  carouselRef.value?.setActiveItem(index)
}

function next() {
  if (announcements.value.length <= 1) return
  setActiveItem((currentIndex.value + 1) % announcements.value.length)
}

function previous() {
  if (announcements.value.length <= 1) return
  setActiveItem(
    currentIndex.value === 0
      ? announcements.value.length - 1
      : currentIndex.value - 1
  )
}

function handleCarouselChange(index: number) {
  currentIndex.value = index
}

function handleClick(announcement: Announcement) {
  notificationStore.setSelectedNotification(announcement.id)
  router.push('/user-center')
}

function pauseAutoplay() {
  isPaused = true
  stopAutoplay()
}

function resumeAutoplay() {
  isPaused = false
  startAutoplay()
}

function startAutoplay() {
  if (!props.autoplay || isPaused || announcements.value.length <= 1) return

  stopAutoplay()
  autoplayTimer = window.setInterval(() => {
    next()
  }, props.autoplayInterval || 5000)
}

function stopAutoplay() {
  if (autoplayTimer !== null) {
    clearInterval(autoplayTimer)
    autoplayTimer = null
  }
}

watch(
  () => announcements.value.length,
  (length) => {
    if (length === 0) {
      stopAutoplay()
      currentIndex.value = 0
      return
    }

    if (currentIndex.value >= length) {
      setActiveItem(0)
    }

    if (length > 1 && !isPaused) {
      startAutoplay()
      return
    }

    stopAutoplay()
  }
)

onMounted(() => {
  loadAnnouncements()
})

onUnmounted(() => {
  stopAutoplay()
})

defineExpose({
  pauseAutoplay,
  resumeAutoplay,
})

function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

function formatAnnouncementTime(value: string | null): string {
  if (!value) return '最新公告'

  try {
    let normalized = value
    if (!value.endsWith('Z') && !value.includes('+') && !/[+-]\d{2}:\d{2}$/.test(value)) {
      normalized = value.replace(' ', 'T') + 'Z'
    }
    const date = new Date(normalized)
    if (Number.isNaN(date.getTime())) return '最新公告'
    return date.toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
    })
  } catch {
    return '最新公告'
  }
}

function getImageUrl(path: string | null): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  if (path.startsWith('/api/')) {
    return `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8888'}${path}`
  }
  return path
}
</script>

<style scoped>
.notification-carousel {
  border-bottom: 1px solid rgba(232, 215, 214, 0.8);
  background:
    radial-gradient(circle at top left, rgba(140, 42, 46, 0.06), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(253, 248, 247, 0.98));
  padding: 12px;
}

.notification-carousel__inner {
  position: relative;
}

.notification-carousel__card {
  overflow: hidden;
  border-radius: 24px;
  border: 1px solid rgba(140, 42, 46, 0.08);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 14px 32px rgba(88, 28, 32, 0.08);
  cursor: pointer;
}

.notification-carousel__accent {
  height: 3px;
  background: linear-gradient(90deg, rgba(140, 42, 46, 0.95), rgba(140, 42, 46, 0.28), rgba(255, 255, 255, 0));
}

.notification-carousel__content {
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  min-height: 110px;
  padding: 16px 18px 18px;
}

.notification-carousel__media {
  width: 92px;
  height: 92px;
  overflow: hidden;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(140, 42, 46, 0.08), rgba(255, 255, 255, 0.95));
}

.notification-carousel__image,
.notification-carousel__image :deep(.el-image__inner) {
  display: block;
  width: 100%;
  height: 100%;
}

.notification-carousel__placeholder {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
  color: rgba(140, 42, 46, 0.55);
  background:
    radial-gradient(circle at top left, rgba(140, 42, 46, 0.1), transparent 40%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(243, 244, 246, 0.9));
}

.notification-carousel__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.notification-carousel__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.notification-carousel__date {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 500;
  color: rgba(88, 28, 32, 0.46);
}

.notification-carousel__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification-carousel__title-icon {
  flex-shrink: 0;
  color: rgba(140, 42, 46, 0.56);
}

.notification-carousel__title {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--color-ink-950);
  font-size: 16px;
  font-weight: 600;
  line-height: 1.35;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
}

.notification-carousel__excerpt {
  display: -webkit-box;
  overflow: hidden;
  margin: 8px 0 0;
  color: var(--color-ink-700);
  font-size: 13px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.notification-carousel__action {
  color: var(--color-primary);
}

.notification-carousel__tag {
  border-radius: 999px;
}

.notification-carousel__tag--urgent {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.14);
  color: #dc2626;
}

.notification-carousel__tag--high {
  background: rgba(249, 115, 22, 0.12);
  border-color: rgba(249, 115, 22, 0.14);
  color: #c2410c;
}

.notification-carousel__tag--normal {
  background: rgba(140, 42, 46, 0.08);
  border-color: rgba(140, 42, 46, 0.12);
  color: var(--color-primary);
}

.notification-carousel__tag--low {
  background: rgba(107, 114, 128, 0.12);
  border-color: rgba(107, 114, 128, 0.14);
  color: #4b5563;
}

.notification-carousel__tag--pinned {
  background: rgba(245, 158, 11, 0.14);
  border-color: rgba(245, 158, 11, 0.18);
  color: #b45309;
}

.notification-carousel__nav {
  position: absolute;
  top: 50%;
  z-index: 10;
  width: 34px;
  height: 34px;
  border-color: rgba(140, 42, 46, 0.08);
  background: rgba(255, 255, 255, 0.84);
  color: rgba(88, 28, 32, 0.72);
  box-shadow: 0 10px 20px rgba(88, 28, 32, 0.08);
  transform: translateY(-50%);
}

.notification-carousel__nav--prev {
  left: 12px;
}

.notification-carousel__nav--next {
  right: 12px;
}

.notification-carousel :deep(.el-card__body) {
  padding: 0;
}

.notification-carousel :deep(.el-carousel__container) {
  height: 132px;
}

.notification-carousel :deep(.el-carousel__indicators--horizontal) {
  bottom: -2px;
}

.notification-carousel :deep(.el-carousel__button) {
  width: 18px;
  height: 6px;
  border-radius: 999px;
  background: rgba(140, 42, 46, 0.16);
}

.notification-carousel :deep(.el-carousel__indicator.is-active .el-carousel__button) {
  background: rgba(140, 42, 46, 0.82);
}

@media (max-width: 768px) {
  .notification-carousel {
    padding: 12px 10px;
  }

  .notification-carousel__content {
    grid-template-columns: 72px minmax(0, 1fr) auto;
    gap: 12px;
    min-height: 96px;
    padding: 14px 14px 16px;
  }

  .notification-carousel__media {
    width: 72px;
    height: 72px;
    border-radius: 14px;
  }

  .notification-carousel__title {
    font-size: 14px;
  }

  .notification-carousel__excerpt {
    font-size: 12px;
  }

  .notification-carousel__action span:first-child {
    display: none;
  }
}
</style>
