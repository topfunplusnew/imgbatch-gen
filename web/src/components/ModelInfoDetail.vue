<template>
  <div class="overflow-hidden rounded-[1.25rem] border border-black/5 bg-white shadow-xl">
    <div class="border-b border-border-dark bg-background-dark/70 px-6 py-6">
      <div class="flex items-start justify-between gap-4">
        <div class="flex min-w-0 flex-1 items-start gap-4">
          <div class="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10">
            <span class="material-symbols-outlined !text-3xl text-primary">
              {{ getModelIcon(model?.vendor_name) }}
            </span>
          </div>

          <div class="min-w-0 flex-1">
            <h2 class="truncate text-xl font-bold text-ink-950">{{ model?.model_name }}</h2>
            <div class="mt-3 flex flex-wrap items-center gap-2">
              <span class="rounded-md border border-border-dark bg-white px-2.5 py-1 text-xs font-medium text-ink-700">
                {{ model?.vendor_name || '未知提供商' }}
              </span>
              <span
                v-if="model?.model_type === '图像'"
                class="rounded-md border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary-deep"
              >
                图像模型
              </span>
              <span
                v-else-if="model?.model_type === '文本'"
                class="rounded-md border border-border-dark bg-background-dark px-2.5 py-1 text-xs font-medium text-ink-700"
              >
                聊天模型
              </span>
              <span
                v-if="model?.is_async"
                class="rounded-md border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary-deep"
              >
                异步生成
              </span>
              <span class="text-xs text-ink-500">{{ model?.provider || '未标注 Provider' }}</span>
            </div>
          </div>
        </div>

        <button
          @click="$emit('close')"
          class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-border-dark bg-white text-ink-500 transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-ink-950"
          type="button"
        >
          <span class="material-symbols-outlined !text-xl">close</span>
        </button>
      </div>
    </div>

    <div class="space-y-6 px-6 py-6">
      <section class="space-y-2">
        <h3 class="text-xs font-bold uppercase tracking-[0.18em] text-ink-500">模型描述</h3>
        <p class="text-sm leading-7 text-ink-700">
          {{ model?.description || '暂无模型描述。' }}
        </p>
      </section>

      <section v-if="model?.tags?.length" class="space-y-3">
        <h3 class="text-xs font-bold uppercase tracking-[0.18em] text-ink-500">风格标签</h3>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tag in model.tags"
            :key="tag"
            class="rounded-lg border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary-deep"
          >
            {{ tag }}
          </span>
        </div>
      </section>

      <section class="space-y-3">
        <h3 class="text-xs font-bold uppercase tracking-[0.18em] text-ink-500">能力概览</h3>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div class="rounded-xl border border-border-dark bg-background-dark/80 p-4">
            <div class="flex items-center gap-2 text-sm font-semibold text-ink-950">
              <span class="material-symbols-outlined !text-lg text-primary">photo_size_select_large</span>
              支持尺寸
            </div>
            <p class="mt-2 text-xs leading-6 text-ink-500">适合常见图像生成尺寸与不同画幅比例。</p>
          </div>

          <div class="rounded-xl border border-border-dark bg-background-dark/80 p-4">
            <div class="flex items-center gap-2 text-sm font-semibold text-ink-950">
              <span class="material-symbols-outlined !text-lg text-primary">palette</span>
              风格控制
            </div>
            <p class="mt-2 text-xs leading-6 text-ink-500">适用于写实、插画、概念设计等多种风格方向。</p>
          </div>

          <div class="rounded-xl border border-border-dark bg-background-dark/80 p-4">
            <div class="flex items-center gap-2 text-sm font-semibold text-ink-950">
              <span class="material-symbols-outlined !text-lg text-primary">high_quality</span>
              输出质量
            </div>
            <p class="mt-2 text-xs leading-6 text-ink-500">支持更高质量输出，适合成品图与精细化创作。</p>
          </div>

          <div class="rounded-xl border border-border-dark bg-background-dark/80 p-4">
            <div class="flex items-center gap-2 text-sm font-semibold text-ink-950">
              <span class="material-symbols-outlined !text-lg text-primary">
                {{ model?.is_async ? 'schedule' : 'bolt' }}
              </span>
              生成方式
            </div>
            <p class="mt-2 text-xs leading-6 text-ink-500">
              {{ model?.is_async ? '异步任务，更适合较重的生成流程。' : '即时响应，适合快速试错与连续对话。' }}
            </p>
          </div>
        </div>
      </section>

      <section class="space-y-3">
        <h3 class="text-xs font-bold uppercase tracking-[0.18em] text-ink-500">技术信息</h3>
        <div class="rounded-xl border border-border-dark bg-background-dark/80 p-4">
          <div class="grid gap-3 text-sm sm:grid-cols-3">
            <div>
              <div class="text-xs uppercase tracking-[0.14em] text-ink-500">提供商</div>
              <div class="mt-1 font-medium text-ink-950">{{ model?.vendor_name || '未知' }}</div>
            </div>
            <div>
              <div class="text-xs uppercase tracking-[0.14em] text-ink-500">Provider</div>
              <div class="mt-1 font-mono text-xs text-ink-950">{{ model?.provider || '未标注' }}</div>
            </div>
            <div>
              <div class="text-xs uppercase tracking-[0.14em] text-ink-500">模式</div>
              <div class="mt-1 font-medium" :class="model?.is_async ? 'text-primary-deep' : 'text-ink-700'">
                {{ model?.is_async ? '异步' : '实时' }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="rounded-xl border border-primary/20 bg-primary/5 p-4">
        <div class="flex items-start gap-3">
          <span class="material-symbols-outlined !text-xl text-primary">tips_and_updates</span>
          <div>
            <h4 class="text-sm font-semibold text-ink-950">使用建议</h4>
            <p class="mt-1 text-xs leading-6 text-ink-700">
              这个模型更适合{{ getRecommendedUse(model?.tags) }}。
              {{ model?.is_async ? '如果你更关注质量和稳定产出，优先选择它。' : '如果你在频繁试提示词，它会更顺手。' }}
            </p>
          </div>
        </div>
      </section>
    </div>

    <div class="flex gap-3 border-t border-border-dark px-6 py-5">
      <button
        @click="handleSelect"
        class="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary-strong px-5 py-3 text-sm font-semibold text-white shadow-lg transition-colors hover:bg-primary-deep"
        type="button"
      >
        <span class="material-symbols-outlined">check_circle</span>
        选择此模型
      </button>
      <button
        @click="$emit('close')"
        class="inline-flex items-center justify-center rounded-xl border border-border-dark bg-white px-5 py-3 text-sm font-semibold text-ink-700 transition-colors hover:border-primary/30 hover:bg-primary/5"
        type="button"
      >
        关闭
      </button>
    </div>
  </div>
</template>

<script setup>
import { notification } from '@/utils/notification'

const props = defineProps({
  model: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'select'])

const getModelIcon = (vendorName) => {
  const icons = {
    Google: 'smart_toy',
    OpenAI: 'auto_awesome',
    'Doubao (豆包)': 'psychology',
    Tencent: 'language',
    Ideogram: 'image',
    'Stable Diffusion': 'gradient',
    Midjourney: 'palette',
    Anthropic: 'chat',
    Claude: 'chat',
    Gemini: 'smart_toy'
  }

  return icons[vendorName] || 'deployed_code'
}

const getRecommendedUse = (tags = []) => {
  if (tags.includes('写实') || tags.includes('photorealistic')) {
    return '写实场景、人物肖像和产品展示'
  }

  if (tags.includes('动漫') || tags.includes('二次元') || tags.includes('anime')) {
    return '动漫角色、插画草案和风格化表达'
  }

  if (tags.includes('卡通') || tags.includes('cartoon')) {
    return '卡通角色、轻松场景和品牌视觉草图'
  }

  if (tags.includes('油画') || tags.includes('艺术') || tags.includes('oil-painting')) {
    return '艺术创作、概念设计和更强的风格化画面'
  }

  if (tags.includes('创意') || tags.includes('抽象') || tags.includes('abstract')) {
    return '创意实验、抽象表现和概念探索'
  }

  return '多种通用创作场景'
}

const handleSelect = () => {
  emit('select', props.model)
  emit('close')
  notification.success('模型已选择', `当前模型：${props.model.model_name}`)
}
</script>
