<template>
  <div
    v-if="announcements.length > 0"
    class="notification-carousel relative w-full overflow-hidden border-b border-border-dark/80 bg-[radial-gradient(circle_at_top_left,_rgba(17,24,39,0.06),_transparent_28%),linear-gradient(180deg,_rgba(255,255,255,0.96),_rgba(249,250,251,0.98))] px-3 py-3 md:px-4"
    @mouseenter="pauseAutoplay"
    @mouseleave="resumeAutoplay"
  >
    <transition :name="transitionDirection" mode="out-in">
      <div
        v-if="currentAnnouncement"
        :key="currentAnnouncement.id"
        class="notification-carousel__slide"
      >
        <ACard
          hoverable
          :bordered="false"
          size="small"
          class="notification-carousel__card"
          :body-style="{ padding: '0' }"
          @click="handleClick(currentAnnouncement)"
        >
          <div class="notification-carousel__card-accent"></div>

          <div class="notification-carousel__card-inner">
            <div class="notification-carousel__media">
              <AImage
                v-if="currentAnnouncement.cover_image_url"
                :src="getImageUrl(currentAnnouncement.cover_image_url)"
                :alt="currentAnnouncement.title"
                :preview="false"
                class="notification-carousel__image"
              />
              <div v-else class="notification-carousel__placeholder">
                <span class="material-symbols-outlined !text-[28px]">campaign</span>
              </div>
            </div>

            <div class="notification-carousel__content">
              <div class="notification-carousel__meta">
                <div class="notification-carousel__tags">
                  <ATag
                    class="notification-carousel__tag"
                    :class="priorityTagClasses[currentAnnouncement.priority]"
                  >
                    {{ getPriorityLabel(currentAnnouncement.priority) }}
                  </ATag>
                  <ATag
                    v-if="currentAnnouncement.is_pinned"
                    class="notification-carousel__tag notification-carousel__tag--pinned"
                  >
                    置顶
                  </ATag>
                </div>

                <span class="notification-carousel__date">
                  {{ formatAnnouncementTime(currentAnnouncement.published_at || currentAnnouncement.created_at) }}
                </span>
              </div>

              <div class="notification-carousel__title-row">
                <span class="material-symbols-outlined notification-carousel__title-icon">campaign</span>
                <h3 class="notification-carousel__title">
                  {{ currentAnnouncement.title }}
                </h3>
              </div>

              <p class="notification-carousel__excerpt">
                {{ stripHtml(currentAnnouncement.content) }}
              </p>
            </div>

            <AButton
              type="text"
              class="notification-carousel__action"
              @click.stop="handleClick(currentAnnouncement)"
            >
              <span class="notification-carousel__action-text">查看</span>
              <span class="material-symbols-outlined !text-base">arrow_forward</span>
            </AButton>
          </div>
        </ACard>
      </div>
    </transition>

    <template v-if="announcements.length > 1">
      <AButton
        type="default"
        shape="circle"
        size="small"
        class="notification-carousel__nav notification-carousel__nav--prev"
        aria-label="上一张"
        @click.stop="previous"
      >
        <span class="material-symbols-outlined !text-[18px]">chevron_left</span>
      </AButton>

      <AButton
        type="default"
        shape="circle"
        size="small"
        class="notification-carousel__nav notification-carousel__nav--next"
        aria-label="下一张"
        @click.stop="next"
      >
        <span class="material-symbols-outlined !text-[18px]">chevron_right</span>
      </AButton>
    </template>

    <div
      v-if="announcements.length > 1"
      class="notification-carousel__dots"
    >
      <button
        v-for="(announcement, index) in announcements"
        :key="announcement.id"
        type="button"
        class="notification-carousel__dot"
        :class="{ 'notification-carousel__dot--active': currentIndex === index }"
        :aria-label="`幻灯片 ${index + 1}`"
        @click.stop="goTo(index)"
      ></button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Button as AButton, Card as ACard, Image as AImage, Tag as ATag } from 'ant-design-vue'
import { useAppStore } from '@/store/useAppStore'
import { useNotificationStore, type Announcement } from '@/store/useNotificationStore'

const props = defineProps<{
  autoplay?: boolean
  autoplayInterval?: number
  maxItems?: number
}>()

const appStore = useAppStore()
const notificationStore = useNotificationStore()

const announcements = ref<Announcement[]>([])
const currentIndex = ref(0)
const transitionDirection = ref<'slide-left' | 'slide-right'>('slide-left')

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

const currentAnnouncement = computed<Announcement | null>(() => {
  if (!announcements.value.length) return null
  if (currentIndex.value >= announcements.value.length) {
    currentIndex.value = 0
  }
  return announcements.value[currentIndex.value] || null
})

async function loadAnnouncements() {
  try {
    const items = await notificationStore.fetchPublicAnnouncements(1, props.maxItems || 5)
    const normalizedItems = Array.isArray(items)
      ? items
      : (items && Array.isArray(items.items) ? items.items : [])

    announcements.value = normalizedItems as Announcement[]
  } catch (error) {
    console.error('[NotificationCarousel] 加载公告失败:', error)
    announcements.value = []
  }
}

function next() {
  if (announcements.value.length <= 1) return
  transitionDirection.value = 'slide-left'
  currentIndex.value = (currentIndex.value + 1) % announcements.value.length
}

function previous() {
  if (announcements.value.length <= 1) return
  transitionDirection.value = 'slide-right'
  currentIndex.value =
    currentIndex.value === 0
      ? announcements.value.length - 1
      : currentIndex.value - 1
}

function goTo(index: number) {
  if (index === currentIndex.value) return
  transitionDirection.value = index < currentIndex.value ? 'slide-right' : 'slide-left'
  currentIndex.value = index
}

function handleClick(announcement: Announcement) {
  notificationStore.setSelectedNotification(announcement.id)
  appStore.setCurrentPage('user-center')
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
      currentIndex.value = 0
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
    const date = new Date(value)
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
.notification-carousel__slide {
  cursor: pointer;
}

.notification-carousel__card {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(17, 24, 39, 0.06);
  box-shadow: 0 14px 32px rgba(17, 24, 39, 0.06);
  backdrop-filter: blur(14px);
}

.notification-carousel__card-accent {
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(90deg, rgba(17, 24, 39, 0.95), rgba(107, 114, 128, 0.28), rgba(255, 255, 255, 0));
}

.notification-carousel__card-inner {
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
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.08), rgba(255, 255, 255, 0.95));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.notification-carousel__placeholder {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
  color: rgba(17, 24, 39, 0.5);
  background:
    radial-gradient(circle at top left, rgba(17, 24, 39, 0.1), transparent 40%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(243, 244, 246, 0.9));
}

.notification-carousel__content {
  min-width: 0;
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
  min-width: 0;
  flex-wrap: wrap;
  gap: 8px;
}

.notification-carousel__date {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 500;
  color: rgba(17, 24, 39, 0.42);
}

.notification-carousel__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification-carousel__title-icon {
  flex-shrink: 0;
  font-size: 18px;
  color: rgba(17, 24, 39, 0.5);
}

.notification-carousel__title {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: #111827;
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
  color: rgba(17, 24, 39, 0.64);
  font-size: 13px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.notification-carousel__action {
  align-self: center;
  height: 36px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.04);
  color: #111827;
}

.notification-carousel__action-text {
  font-size: 12px;
  font-weight: 600;
}

.notification-carousel__dots {
  position: absolute;
  left: 50%;
  bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  transform: translateX(-50%);
}

.notification-carousel__dot {
  width: 7px;
  height: 7px;
  border: 0;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.16);
  transition: width 180ms ease, background-color 180ms ease, transform 180ms ease;
}

.notification-carousel__dot--active {
  width: 22px;
  background: rgba(17, 24, 39, 0.82);
}

.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.28s ease;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(18px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-18px);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-18px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(18px);
}

.notification-carousel :deep(.ant-card-body) {
  padding: 0 !important;
}

.notification-carousel :deep(.ant-image),
.notification-carousel :deep(.ant-image-img) {
  display: block;
  width: 100%;
  height: 100%;
}

.notification-carousel :deep(.ant-image-img) {
  object-fit: cover;
}

.notification-carousel :deep(.ant-tag) {
  margin-inline-end: 0;
  border: none;
  border-radius: 999px;
  padding: 1px 10px;
  font-size: 11px;
  font-weight: 600;
  line-height: 20px;
}

.notification-carousel__tag--urgent {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.notification-carousel__tag--high {
  background: rgba(249, 115, 22, 0.12);
  color: #c2410c;
}

.notification-carousel__tag--normal {
  background: rgba(17, 24, 39, 0.08);
  color: #111827;
}

.notification-carousel__tag--low {
  background: rgba(107, 114, 128, 0.12);
  color: #4b5563;
}

.notification-carousel__tag--pinned {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.notification-carousel :deep(.notification-carousel__action.ant-btn),
.notification-carousel :deep(.notification-carousel__action.ant-btn:hover),
.notification-carousel :deep(.notification-carousel__action.ant-btn:focus) {
  box-shadow: none;
}

.notification-carousel :deep(.notification-carousel__action.ant-btn:hover),
.notification-carousel :deep(.notification-carousel__action.ant-btn:focus) {
  background: rgba(17, 24, 39, 0.08) !important;
  color: #111827 !important;
}

.notification-carousel :deep(.notification-carousel__nav.ant-btn) {
  position: absolute;
  top: 50%;
  z-index: 10;
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  border-color: rgba(17, 24, 39, 0.08);
  background: rgba(255, 255, 255, 0.82);
  color: rgba(17, 24, 39, 0.72);
  box-shadow: 0 10px 20px rgba(17, 24, 39, 0.08);
  transform: translateY(-50%);
}

.notification-carousel :deep(.notification-carousel__nav.ant-btn:hover),
.notification-carousel :deep(.notification-carousel__nav.ant-btn:focus) {
  border-color: rgba(17, 24, 39, 0.12);
  background: rgba(255, 255, 255, 0.96) !important;
  color: #111827 !important;
}

.notification-carousel__nav--prev {
  left: 12px;
}

.notification-carousel__nav--next {
  right: 12px;
}

@media (max-width: 768px) {
  .notification-carousel__card-inner {
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

  .notification-carousel__action {
    padding: 0 10px;
  }

  .notification-carousel__action-text {
    display: none;
  }
}
</style>
