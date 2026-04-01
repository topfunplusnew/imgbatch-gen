<template>
  <button
    @click="$emit('toggle')"
    class="relative p-2 rounded-lg hover:bg-primary/5 min-h-[44px] min-w-[44px] flex items-center justify-center transition-colors"
    :class="{ 'bg-primary/10': active }"
    aria-label="通知"
  >
    <span class="material-symbols-outlined !text-xl">notifications</span>

    <!-- 未读徽章 -->
    <span
      v-if="unreadCount > 0"
      class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-medium animate-pulse"
      :class="{ 'w-6 h-6 text-xs': unreadCount > 99 }"
    >
      {{ unreadCount > 99 ? '99+' : unreadCount }}
    </span>
  </button>
</template>

<script setup lang="ts">
defineProps<{
  unreadCount?: number
  active?: boolean
}>()

defineEmits<{
  toggle: []
}>()
</script>
