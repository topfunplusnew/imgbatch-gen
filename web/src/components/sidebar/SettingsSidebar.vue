<template>
  <aside :class="['flex flex-col bg-white/90 backdrop-blur-xl shrink-0 transition-all duration-300', inDrawer ? 'w-full border-0' : 'w-56 md:w-64 lg:w-72 xl:w-80 border-l border-border-dark']">
    <div v-if="!inDrawer" class="p-6 border-b border-border-dark flex items-center justify-between shrink-0">
      <h2 class="font-bold text-sm uppercase tracking-wider">生成参数</h2>
      <button
        @click="showHelp = true"
        class="text-ink-500 hover:text-ink-950 flex items-center justify-center">
        <span class="material-symbols-outlined !text-lg">help</span>
      </button>
    </div>

    <div class="p-4 xs:p-5 md:p-6 space-y-4 md:space-y-6 overflow-y-auto flex-1 custom-scrollbar">
      <!-- 当前模型 -->
      <div class="space-y-3">
        <label class="text-xs font-bold text-slate-500 uppercase">当前模型</label>
        <div class="bg-white border border-border-dark rounded-xl p-3 shadow-lg">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined !text-lg text-primary">auto_awesome</span>
            <span class="text-sm font-semibold truncate">{{ currentModelDisplay }}</span>
          </div>
          <p v-if="generatorStore.selectedModelInfo" class="text-[10px] text-slate-500 mt-1 line-clamp-2">
            {{ generatorStore.selectedModelInfo.description }}
          </p>
        </div>
      </div>

      <!-- 图像质量 -->
      <div class="space-y-3">
        <label class="text-xs font-bold text-slate-500 uppercase">图像质量</label>
        <div class="grid grid-cols-3 gap-1.5 xs:gap-2">
          <button
            v-for="quality in qualityOptions"
            :key="quality.value"
            @click="generatorStore.setQuality(quality.value)"
            :class="[
              'py-2 xs:py-2.5 text-[10px] font-bold rounded-lg transition-colors',
              generatorStore.quality === quality.value
                ? 'bg-primary-strong text-white shadow-sm'
                : 'bg-white text-ink-700 border border-border-dark hover:bg-primary/5'
            ]">
            {{ quality.label }}
          </button>
        </div>
      </div>

      <!-- 图像尺寸 -->
      <div class="space-y-3">
        <div class="flex justify-between items-center">
          <label class="text-xs font-bold text-slate-500 uppercase">图像尺寸</label>
          <span class="text-[10px] text-primary bg-primary/10 px-2 py-0.5 rounded-full font-bold">
            {{ generatorStore.width }}×{{ generatorStore.height }}
          </span>
        </div>

        <!-- 比例选择网格 -->
        <div class="grid grid-cols-2 xs:grid-cols-3 sm:grid-cols-3 gap-1.5 xs:gap-2">
          <button
            v-for="ratio in ratioOptions"
            :key="ratio.value"
            @click="selectRatio(ratio)"
            :class="[
              'flex flex-col items-center justify-center gap-1 py-2 px-1 rounded-xl transition-colors text-center',
              selectedRatio === ratio.value
                ? 'bg-primary-strong text-white shadow-sm'
                : 'bg-white text-ink-700 border border-border-dark hover:bg-primary/5'
            ]">
            <!-- 比例预览框 -->
            <div class="flex items-center justify-center w-8 h-8">
              <div
                :style="getRatioBoxStyle(ratio)"
                :class="[
                  'rounded-sm border-2',
                  selectedRatio === ratio.value ? 'border-ink-950' : 'border-slate-500'
                ]">
              </div>
            </div>
            <span class="text-[10px] font-bold leading-tight">{{ ratio.label }}</span>
            <span class="text-[9px] leading-tight opacity-70">{{ ratio.desc }}</span>
          </button>
        </div>

        <!-- 自定义尺寸（展开） -->
        <div v-if="showCustomSize" class="grid grid-cols-2 gap-2 mt-2">
          <div class="relative flex items-center">
            <input type="number" v-model.number="generatorStore.width"
              class="w-full bg-white border border-border-dark rounded-xl text-sm py-2 px-3 focus:ring-1 focus:ring-primary focus:ring-offset-0">
            <span class="absolute right-2 text-[10px] text-slate-500 pointer-events-none">W</span>
          </div>
          <div class="relative flex items-center">
            <input type="number" v-model.number="generatorStore.height"
              class="w-full bg-white border border-border-dark rounded-xl text-sm py-2 px-3 focus:ring-1 focus:ring-primary focus:ring-offset-0">
            <span class="absolute right-2 text-[10px] text-slate-500 pointer-events-none">H</span>
          </div>
        </div>
      </div>

      <!-- 批量数量 -->
      <div class="space-y-3">
        <label class="text-xs font-bold text-slate-500 uppercase">批量生成数量</label>
        <input
          type="number"
          v-model.number="generatorStore.batchSize"
          min="1"
          max="50"
          placeholder="输入数量"
          class="w-full bg-white border border-border-dark rounded-xl text-sm py-2.5 px-4 focus:ring-1 focus:ring-primary">
      </div>

      <!-- 负面提示词 -->
      <div class="space-y-3">
        <label class="text-xs font-bold text-slate-500 uppercase">负面提示词</label>
        <textarea
          v-model="generatorStore.negativePrompt"
          placeholder="描述你不希望出现在图像中的内容..."
          class="w-full bg-white border border-border-dark rounded-xl text-sm py-3 px-4 focus:ring-1 focus:ring-primary resize-none h-20 custom-scrollbar">
        </textarea>
      </div>

      <!-- 随机种子 -->
      <div class="space-y-3">
        <div class="flex justify-between items-center">
          <label class="text-xs font-bold text-slate-500 uppercase">随机种子</label>
          <button
            v-if="generatorStore.seed"
            @click="generatorStore.setSeed('')"
            class="text-[10px] text-ink-500 hover:text-red-400">
            清除
          </button>
        </div>
        <div class="flex gap-2">
          <input
            type="text"
            v-model="generatorStore.seed"
            placeholder="留空为随机"
            class="flex-1 bg-white border border-border-dark rounded-xl text-sm py-2.5 px-4 focus:ring-1 focus:ring-primary">
          <button
            @click="generateRandomSeed"
            class="px-4 bg-white border border-border-dark rounded-xl hover:bg-primary/5 transition-colors">
            <span class="material-symbols-outlined !text-lg">shuffle</span>
          </button>
        </div>
      </div>

    </div>
  </aside>

  <!-- 帮助弹窗 -->
  <div
    v-if="showHelp"
    @click="showHelp = false"
    class="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/10 p-4 xs:p-6 backdrop-blur-sm">
    <div
      @click.stop
      class="bg-white border border-border-dark rounded-2xl p-4 xs:p-6 max-w-md w-full mx-4 space-y-4 shadow-xl">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">参数说明</h3>
        <button @click="showHelp = false" class="text-ink-500 hover:text-ink-950">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="space-y-3 text-sm text-ink-700">
        <div>
          <strong class="text-ink-950">图像风格：</strong>选择生成图像的艺术风格，如写实、动漫、油画等
        </div>
        <div>
          <strong class="text-ink-950">图像质量：</strong>标准（快速）、高清（更好质量）、超清（最佳质量）
        </div>
        <div>
          <strong class="text-ink-950">批量生成：</strong>一次性生成多张图像，数量1-10张
        </div>
        <div>
          <strong class="text-ink-950">负面提示词：</strong>描述你不希望出现在图像中的内容
        </div>
        <div>
          <strong class="text-ink-950">随机种子：</strong>设置固定值可以重复生成相同图像
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'

const props = defineProps({
  inDrawer: { type: Boolean, default: false }
})

const generatorStore = useGeneratorStore()
const showHelp = ref(false)
const showCustomSize = ref(false)

const ratioOptions = [
  { value: 'auto',  label: 'Auto',  desc: '自动',   w: 1024, h: 1024 },
  { value: '1:1',   label: '1:1',   desc: '方形',   w: 1024, h: 1024 },
  { value: '3:4',   label: '3:4',   desc: '竖版',   w: 768,  h: 1024 },
  { value: '4:3',   label: '4:3',   desc: '横版',   w: 1024, h: 768  },
  { value: '9:16',  label: '9:16',  desc: '竖版',   w: 576,  h: 1024 },
  { value: '16:9',  label: '16:9',  desc: '横版',   w: 1024, h: 576  },
  { value: '2:3',   label: '2:3',   desc: '竖版',   w: 683,  h: 1024 },
  { value: '3:2',   label: '3:2',   desc: '横版',   w: 1024, h: 683  },
  { value: '4:5',   label: '4:5',   desc: '竖版',   w: 819,  h: 1024 },
  { value: '5:4',   label: '5:4',   desc: '横版',   w: 1024, h: 819  },
  { value: '21:9',  label: '21:9',  desc: '影院',   w: 1024, h: 439  },
  { value: 'custom',label: '自定义', desc: '更多',   w: null, h: null },
]

const selectedRatio = ref('1:1')

const selectRatio = (ratio) => {
  if (ratio.value === 'custom') {
    showCustomSize.value = !showCustomSize.value
    return
  }
  selectedRatio.value = ratio.value
  showCustomSize.value = false

  // 根据当前质量设置调整尺寸
  const maxDimMap = { '720p': 1280, '2k': 2048, '4k': 3840 }
  const maxDim = maxDimMap[generatorStore.quality] || 1024

  // 计算当前比例
  const ratioValue = ratio.w / ratio.h

  // 根据比例和最大边长计算最终尺寸
  if (ratioValue >= 1) {
    // 横向或方形图片
    generatorStore.width = maxDim
    generatorStore.height = Math.round(maxDim / ratioValue)
  } else {
    // 竖向图片
    generatorStore.height = maxDim
    generatorStore.width = Math.round(maxDim * ratioValue)
  }
}

const getRatioBoxStyle = (ratio) => {
  if (!ratio.w || !ratio.h) return { width: '20px', height: '20px' }
  const maxDim = 24
  const r = ratio.w / ratio.h
  if (r >= 1) {
    return { width: `${maxDim}px`, height: `${Math.round(maxDim / r)}px` }
  } else {
    return { width: `${Math.round(maxDim * r)}px`, height: `${maxDim}px` }
  }
}

// 质量选项
const qualityOptions = [
  { value: '720p', label: '720P' },
  { value: '2k', label: '2K' },
  { value: '4k', label: '4K' },
]

// 当前模型显示
const currentModelDisplay = computed(() => {
  return generatorStore.selectedModelInfo?.model_name || generatorStore.model || '未选择模型'
})

// 生成随机种子
const generateRandomSeed = () => {
  generatorStore.setSeed(Math.floor(Math.random() * 999999999).toString())
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #d1d8d3;
  border-radius: 10px;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
