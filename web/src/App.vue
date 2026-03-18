<script setup>
import { computed } from 'vue'
import { useAppStore } from './store/useAppStore'
import ImageStudio from './views/ImageStudio.vue'
import ApiConfig from './views/ApiConfig.vue'
import AsyncTasks from './views/AsyncTasks.vue'
import NotificationContainer from './components/NotificationContainer.vue'

const appStore = useAppStore()

const currentComponent = computed(() => {
  switch (appStore.currentPage) {
    case 'agent':
      return ImageStudio
    case 'api':
      return ApiConfig
    case 'async-tasks':
      return AsyncTasks
    default:
      return ImageStudio
  }
})
</script>

<template>
  <component :is="currentComponent" />
  <NotificationContainer />
</template>

<style scoped>
</style>
