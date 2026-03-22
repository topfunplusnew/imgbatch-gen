<template>
  <div
    @click="$emit('click')"
    class="bg-white rounded-xl p-4 hover:shadow-lg transition-shadow cursor-pointer border border-border-dark hover:border-primary/30"
  >
    <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-3">
      <span class="material-symbols-outlined text-primary !text-2xl">{{ icon }}</span>
    </div>
    <h4 class="font-semibold text-ink-950 text-sm">{{ title }}</h4>
    <p class="text-xs text-ink-500 mt-1">{{ description }}</p>
  </div>
</template>

<script setup>
defineProps({
  icon: {
    type: String,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  }
})

defineEmits(['click'])
</script>
