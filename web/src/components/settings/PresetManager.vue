<template>
  <div class="space-y-3">
    <!-- 预设选择器 -->
    <label class="text-xs font-bold text-slate-500 uppercase">参数预设</label>

    <!-- 预设列表 -->
    <div class="space-y-2">
      <div
        v-for="preset in generatorStore.presets"
        :key="preset.id"
        class="bg-surface-dark border border-border-dark rounded-xl p-3 hover:border-primary/50 transition-colors group">
        <div class="flex items-center justify-between">
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-semibold truncate">{{ preset.name }}</h4>
            <div class="flex items-center gap-2 mt-1 text-[10px] text-slate-500">
              <span>{{ styleLabels[preset.params.style] || preset.params.style }}</span>
              <span>•</span>
              <span>{{ qualityLabels[preset.params.quality] || preset.params.quality }}</span>
              <span>•</span>
              <span>{{ preset.params.width }}x{{ preset.params.height }}</span>
              <span>•</span>
              <span>{{ preset.params.batchSize }}张</span>
            </div>
          </div>
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              @click="loadPreset(preset.id)"
              class="p-1.5 hover:bg-primary/20 rounded-lg text-slate-400 hover:text-primary transition-colors"
              title="加载此预设">
              <span class="material-symbols-outlined !text-sm">play_arrow</span>
            </button>
            <button
              @click="deletePreset(preset.id)"
              class="p-1.5 hover:bg-red-400/10 rounded-lg text-slate-400 hover:text-red-400 transition-colors"
              title="删除预设">
              <span class="material-symbols-outlined !text-sm">delete</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="generatorStore.presets.length === 0" class="text-center py-4 text-slate-500">
        <span class="material-symbols-outlined !text-3xl mb-1 block">bookmark_add</span>
        <p class="text-xs">暂无预设，保存当前参数创建第一个</p>
      </div>
    </div>

    <!-- 保存当前参数为预设 -->
    <div class="flex gap-2">
      <input
        v-model="newPresetName"
        @keyup.enter="saveCurrentPreset"
        type="text"
        placeholder="预设名称..."
        class="flex-1 bg-surface-dark border border-border-dark rounded-xl text-sm py-2.5 px-4 focus:ring-1 focus:ring-primary">
      <button
        @click="saveCurrentPreset"
        :disabled="!newPresetName.trim()"
        class="px-4 bg-primary text-white rounded-xl text-sm font-semibold hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1">
        <span class="material-symbols-outlined !text-lg">save</span>
        保存
      </button>
    </div>

    <!-- 快捷应用默认预设 -->
    <div class="grid grid-cols-2 gap-2">
      <button
        v-for="defaultPreset in defaultPresets"
        :key="defaultPreset.id"
        @click="applyDefaultPreset(defaultPreset)"
        class="py-2 px-3 bg-surface-dark border border-border-dark rounded-xl text-xs hover:border-primary/50 transition-colors text-left">
        <div class="font-semibold text-slate-300">{{ defaultPreset.name }}</div>
        <div class="text-[10px] text-slate-500 mt-0.5">{{ defaultPreset.description }}</div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { notification } from '@/utils/notification'

const generatorStore = useGeneratorStore()
const newPresetName = ref('')

// 风格标签映射
const styleLabels = {
  'photorealistic': '写实',
  'anime': '动漫',
  'cartoon': '卡通',
  'oil-painting': '油画',
  'watercolor': '水彩',
  'sketch': '素描',
  'cyberpunk': '赛博朋克',
  'fantasy': '奇幻',
  'minimalist': '简约',
  'abstract': '抽象'
}

// 质量标签映射
const qualityLabels = {
  'standard': '标准',
  'high': '高清',
  'ultra': '超清'
}

// 默认预设（用于快捷应用）
const defaultPresets = [
  {
    id: 'fast',
    name: '⚡ 快速生成',
    description: '1张 • 标准质量',
    params: {
      width: 1024,
      height: 1024,
      aspectRatio: '1:1',
      batchSize: 1,
      style: 'photorealistic',
      quality: 'standard',
      negativePrompt: ''
    }
  },
  {
    id: 'quality',
    name: '✨ 高质量',
    description: '2张 • 高清质量',
    params: {
      width: 1024,
      height: 1024,
      aspectRatio: '1:1',
      batchSize: 2,
      style: 'photorealistic',
      quality: 'high',
      negativePrompt: '模糊, 低质量, 扭曲'
    }
  },
  {
    id: 'artistic',
    name: '🎨 艺术创作',
    description: '4张 • 油画风格',
    params: {
      width: 1024,
      height: 1024,
      aspectRatio: '1:1',
      batchSize: 4,
      style: 'oil-painting',
      quality: 'high',
      negativePrompt: ''
    }
  },
  {
    id: 'wide',
    name: '🖥️ 宽屏壁纸',
    description: '1920x1080 • 超清',
    params: {
      width: 1920,
      height: 1080,
      aspectRatio: '16:9',
      batchSize: 1,
      style: 'photorealistic',
      quality: 'ultra',
      negativePrompt: '模糊, 低质量'
    }
  }
]

// 组件挂载时初始化
onMounted(() => {
  generatorStore.loadPresetsFromStorage()
  generatorStore.initDefaultPresets()
})

// 保存当前参数为预设
const saveCurrentPreset = () => {
  if (!newPresetName.value.trim()) {
    notification.warning('提示', '请输入预设名称')
    return
  }

  const preset = generatorStore.savePreset(newPresetName.value.trim())
  notification.success('保存成功', `预设"${newPresetName.value.trim()}"已保存`)
  newPresetName.value = ''
}

// 加载预设
const loadPreset = (presetId) => {
  const success = generatorStore.loadPreset(presetId)
  if (success) {
    const preset = generatorStore.presets.find(p => p.id === presetId)
    notification.success('加载成功', `已应用预设"${preset.name}"`)
  }
}

// 删除预设
const deletePreset = (presetId) => {
  const preset = generatorStore.presets.find(p => p.id === presetId)
  if (confirm(`确定要删除预设"${preset.name}"吗？`)) {
    generatorStore.deletePreset(presetId)
    notification.success('删除成功', `预设"${preset.name}"已删除`)
  }
}

// 应用默认预设
const applyDefaultPreset = (preset) => {
  generatorStore.width = preset.params.width
  generatorStore.height = preset.params.height
  generatorStore.aspectRatio = preset.params.aspectRatio
  generatorStore.batchSize = preset.params.batchSize
  generatorStore.style = preset.params.style
  generatorStore.quality = preset.params.quality
  generatorStore.negativePrompt = preset.params.negativePrompt

  notification.success('应用成功', `已应用"${preset.name}"预设`)
}
</script>
