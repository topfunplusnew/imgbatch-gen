<template>
  <main class="flex-1 flex flex-col relative bg-white/60 min-w-0 xs:min-w-[300px] md:min-w-[400px] lg:min-w-[500px] h-screen overflow-hidden">
    <TopHeader
      @openHistory="$emit('openHistory')"
      @openTemplates="$emit('openTemplates')"
      @toggleSettings="$emit('toggleSettings')"
      @toggleSidebar="$emit('toggleSidebar')"
      @openModelSelector="showModelSelector = true"
    />

    <!-- 对话滚动区域 -->
    <div
      ref="chatAreaRef"
      class="flex-1 overflow-y-auto custom-scrollbar p-3 xs:p-4 sm:p-6 md:p-8 min-h-0 pb-8"
      :style="chatAreaStyle">

      <!-- 案例详情面板 -->
      <CaseDetailPanel />

      <!-- 创作记录详情面板 -->
      <CreationDetailPanel />

      <div class="max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-5xl mx-auto space-y-6 md:space-y-8">
        <MessageItem v-for="msg in generatorStore.messages" :key="msg.id" :msg="msg" />
      </div>
    </div>

    <!-- 底部输入框 -->
    <ChatInputBar
      :show-model-selector="showModelSelector"
      @update:showModelSelector="showModelSelector = $event"
    />

    <!-- 模型选择器弹窗（全局） -->
    <Teleport to="body">
      <ModelSelector
        v-if="showModelSelector"
        :current-model="generatorStore.model"
        :attachments="generatorStore.attachments"
        @select="handleModelSelect"
        @close="showModelSelector = false"
      />
    </Teleport>
  </main>
</template>

<script setup>
import { ref, computed } from 'vue'
import TopHeader from '@/components/layout/TopHeader.vue'
import MessageItem from '@/components/chat/MessageItem.vue'
import ChatInputBar from '@/components/chat/ChatInputBar.vue'
import CaseDetailPanel from '@/components/cases/CaseDetailPanel.vue'
import CreationDetailPanel from '@/components/creation/CreationDetailPanel.vue'
import ModelSelector from '@/components/ModelSelector.vue'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { notification } from '@/utils/notification'

const generatorStore = useGeneratorStore()

// Define emits
defineEmits(['openHistory', 'openTemplates', 'toggleSettings', 'toggleSidebar'])

// 模型选择器状态
const showModelSelector = ref(false)

// 处理模型选择
const handleModelSelect = (model) => {
  generatorStore.setSelectedModel(model.model_name)
  generatorStore.setSelectedModelInfo(model)
  showModelSelector.value = false

  // 保存到localStorage
  localStorage.setItem('selectedModel', JSON.stringify({
    modelName: model.model_name,
    modelInfo: model
  }))

  notification.success('模型已切换', `已切换到 ${model.model_name}`)
}

// 对话区域高度拖拽（通过 chatAreaStyle 控制，这里保持 flex-1 自动）
const chatAreaStyle = computed(() => ({}))
const chatAreaRef = ref(null)
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #d1d8d3; border-radius: 10px; }
</style>
