<template>
  <div class="case-card group relative overflow-hidden rounded-lg border border-border-dark bg-white transition-all duration-200 hover:border-primary/50 hover:shadow-md">
    <div class="flex items-center gap-2 p-2 xs:p-2.5">
      <div class="flex min-w-0 flex-1 items-center">
        <h3 class="line-clamp-1 text-xs font-semibold leading-tight text-gray-900 xs:text-sm">
          {{ caseData.title }}
        </h3>
      </div>

      <div class="flex shrink-0 items-center border-l border-gray-200 pl-1">
        <button
          class="flex min-h-[40px] min-w-[40px] items-center justify-center rounded p-1.5 text-gray-500 transition-colors hover:bg-primary/5 hover:text-primary xs:min-h-[44px] xs:min-w-[44px] xs:p-2"
          title="查看详情"
          @click="viewDetails"
        >
          <span class="material-symbols-outlined !text-base xs:!text-lg">more_horiz</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAppStore } from '@/store/useAppStore'

const emit = defineEmits(['requestClose'])

const props = defineProps({
  caseData: {
    type: Object,
    required: true
  }
})

const appStore = useAppStore()

const viewDetails = () => {
  try {
    appStore.setSelectedCase(props.caseData)
    emit('requestClose')
  } catch (error) {
    console.error('Error in viewDetails:', error)
  }
}
</script>

<style scoped>
.case-card {
  width: 100%;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
