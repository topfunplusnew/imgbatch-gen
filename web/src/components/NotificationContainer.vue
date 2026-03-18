<template>
  <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
    <TransitionGroup name="notification">
      <div
        v-for="notif in notifications"
        :key="notif.id"
        :class="[
          'pointer-events-auto min-w-[300px] max-w-md rounded-xl border border-black/5 bg-white/95 p-4 shadow-xl backdrop-blur-xl',
          'flex items-start gap-3',
          getNotificationClasses(notif.type)
        ]"
      >
        <!-- 图标 -->
        <span class="material-symbols-outlined !text-xl flex-shrink-0 mt-0.5">
          {{ getNotificationIcon(notif.type) }}
        </span>

        <!-- 内容 -->
        <div class="flex-1 min-w-0">
          <div class="font-semibold text-sm">{{ notif.title }}</div>
          <div v-if="notif.message" class="text-xs mt-1 opacity-80">{{ notif.message }}</div>
        </div>

        <!-- 关闭按钮 -->
        <button
          @click="removeNotification(notif.id)"
          class="flex-shrink-0 rounded p-1 transition-colors hover:bg-ink-950/5">
          <span class="material-symbols-outlined !text-base">close</span>
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useNotifications } from '@/utils/notification'

const { notifications, removeNotification } = useNotifications()

function getNotificationClasses(type: string): string {
  const classes = {
    success: 'border-primary/20 text-ink-950',
    error: 'border-red-500/20 text-red-500',
    warning: 'border-amber-500/20 text-amber-700',
    info: 'border-primary/20 text-ink-950'
  }
  return classes[type as keyof typeof classes] || classes.info
}

function getNotificationIcon(type: string): string {
  const icons = {
    success: 'check_circle',
    error: 'error',
    warning: 'warning',
    info: 'info'
  }
  return icons[type as keyof typeof icons] || 'info'
}
</script>

<style scoped>
/* 通知动画 */
.notification-enter-active {
  transition: all 0.3s ease-out;
}

.notification-leave-active {
  transition: all 0.2s ease-in;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.notification-move {
  transition: transform 0.3s ease;
}
</style>
