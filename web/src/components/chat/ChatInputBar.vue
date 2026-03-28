<template>
  <div class="bg-white/70 backdrop-blur-xl border-t border-border-dark flex flex-col shrink-0">
    <div class="px-3 xs:px-4 md:px-6 py-2 xs:py-2.5 md:py-4">
      <div class="w-full md:w-[65%] mx-auto">
        <!-- 已选文件列表 -->
        <div v-if="generatorStore.attachments.length > 0" class="mb-2 flex flex-wrap gap-2">
          <div
            v-for="(file, index) in generatorStore.attachments"
            :key="index"
            class="relative flex max-w-full items-center gap-1.5 overflow-hidden rounded-lg border border-border-dark bg-white px-2 py-1 text-xs shadow-lg"
            :class="{ 'ring-2 ring-primary': isHoveringFile === index }">

            <!-- File content (z-index 10 to stay above overlay) -->
            <div class="relative z-10 flex min-w-0 items-center gap-1.5">
              <!-- 图片预览或文件图标 -->
              <div v-if="isImageFile(file)" class="relative shrink-0">
                <img
                  :src="getFilePreviewUrl(file)"
                  :alt="file.name"
                  class="h-[60px] w-[60px] rounded-lg border border-border-dark object-cover"
                  @load="revokeFilePreviewUrl(file)">
              </div>
              <span v-else class="material-symbols-outlined !text-sm text-primary">{{ getFileIcon(file) }}</span>

              <!-- 文件名（图片时不显示） -->
              <span v-if="!isImageFile(file)" class="max-w-[120px] truncate text-ink-700">{{ file.name }}</span>

              <button
                @click.stop="removeFile(index)"
                @mouseenter="isHoveringFile = index"
                @mouseleave="isHoveringFile = null"
                class="shrink-0 text-ink-500 transition-colors hover:text-red-400">
                <span class="material-symbols-outlined !text-sm">close</span>
              </button>
            </div>

            <!-- Hover overlay with absolute positioning -->
            <div
              class="absolute inset-0 z-0 grid place-items-center transition-opacity duration-200"
              :class="isHoveringFile === index ? 'opacity-100' : 'opacity-0'">
              <button
                class="max-w-[min(100%,14rem)] truncate rounded-full border-2 border-white bg-primary px-3 py-1 text-xs font-medium text-white shadow-lg transition-colors hover:bg-primary-deep">
                {{ file.name }}
              </button>
            </div>
          </div>
        </div>

        <div
          ref="inputBoxRef"
          @dragover.prevent="handleDragOver"
          @dragleave="handleDragLeave"
          @drop.prevent="handleDrop"
          :class="[
            'relative z-10 bg-white/95 rounded-2xl shadow-xl overflow-hidden',
            'w-full border',
            isDragging ? 'border-accent-purple border-2 bg-accent-purple/5' : 'border-gray-200'
          ]">

          <!-- Top Toolbar -->
          <div class="flex items-center justify-between px-3 py-2 border-b border-gray-100 bg-gray-50/50">
            <!-- Left: Model Selector -->
            <div ref="modelButtonRef" class="relative">
              <button
                @click="showModelPopup = !showModelPopup"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                :title="currentModelDisplay"
              >
                <span class="material-symbols-outlined !text-base text-accent-purple shrink-0">auto_awesome</span>
                <span class="text-sm font-medium text-gray-800 truncate max-w-[140px] md:max-w-[200px]">
                  {{ currentModelDisplay }}
                </span>
                <span class="material-symbols-outlined !text-sm text-gray-500 shrink-0">
                  {{ showModelPopup ? 'expand_less' : 'expand_more' }}
                </span>
              </button>

              <!-- Model Selector Popup -->
              <ModelSelectorPopup
                :visible="showModelPopup"
                :current-model="generatorStore.model"
                :attachments="generatorStore.attachments"
                :trigger-element="modelButtonRef"
                @select="handleModelSelect"
                @close="showModelPopup = false"
              />
            </div>

            <!-- Right: Attachment buttons -->
            <div class="flex items-center gap-1">
              <input
                ref="fileInputRef"
                type="file"
                multiple
                accept=".pdf,.docx,.jpg,.jpeg,.png,.gif,.webp,.bmp,.svg"
                @change="handleFileSelect"
                class="hidden">

              <button
                @click="triggerFileSelect"
                class="p-2 hover:bg-gray-200 rounded-lg text-gray-500 transition-colors"
                title="添加附件">
                <span class="material-symbols-outlined !text-lg">attach_file</span>
              </button>

              <button
                @click="handleNewConversation"
                class="w-7 h-7 flex items-center justify-center bg-gray-800 hover:bg-gray-700 rounded-full text-white transition-colors"
                title="新建对话">
                <span class="material-symbols-outlined !text-base">add</span>
              </button>
            </div>
          </div>

          <!-- Main Input Area -->
          <div class="relative">
            <!-- 拖拽把手 -->
            <div
              @mousedown.prevent="startResizeHeight"
              tabindex="-1"
              class="w-full h-3 flex items-center justify-center cursor-ns-resize select-none hover:bg-gray-100 transition-colors"
              title="拖拽调整高度">
              <div class="w-8 h-0.5 bg-gray-300 rounded-full opacity-60 hover:opacity-100 transition-opacity pointer-events-none"></div>
            </div>

            <textarea
              ref="textareaRef"
              v-model="generatorStore.prompt"
              @keydown.enter.exact.prevent="handleSend"
              @keydown.enter.shift.exact="() => {}"
              @focus="handleFocus"
              :style="{ height: textareaHeight + 'px' }"
              class="w-full bg-transparent border-none focus:ring-0 focus:outline-none text-sm px-4 pb-2 overflow-y-auto custom-scrollbar resize-none text-gray-900 placeholder:text-gray-400"
              placeholder="输入内容开始聊天 (Shift + Enter 换行) ...">
            </textarea>
          </div>

          <!-- Bottom Action Bar -->
          <div class="flex items-center justify-end px-3 py-2 border-t border-gray-100 bg-gray-50/50">
            <!-- Right side buttons -->
            <div class="flex flex-wrap items-center justify-end gap-2">
              <div
                class="flex items-center gap-1 rounded-xl border border-gray-200 bg-white px-1.5 py-1 shadow-sm"
                title="生图数量"
              >
                <span class="hidden lg:inline-flex items-center gap-1 px-1 text-[11px] font-semibold text-gray-500">
                  <span class="material-symbols-outlined !text-sm text-accent-purple">imagesmode</span>
                  生图数量
                </span>
                <button
                  @click="changeBatchSize(-1)"
                  :disabled="normalizedBatchSize <= MIN_BATCH_SIZE"
                  class="flex h-7 w-7 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
                  aria-label="减少生图数量"
                >
                  <span class="material-symbols-outlined !text-base">remove</span>
                </button>
                <div class="min-w-[44px] text-center">
                  <div class="text-sm font-semibold leading-none text-gray-800">{{ normalizedBatchSize }}</div>
                  <div class="mt-0.5 text-[10px] leading-none text-gray-400">张</div>
                </div>
                <button
                  @click="changeBatchSize(1)"
                  :disabled="normalizedBatchSize >= MAX_BATCH_SIZE"
                  class="flex h-7 w-7 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
                  aria-label="增加生图数量"
                >
                  <span class="material-symbols-outlined !text-base">add</span>
                </button>
              </div>

              <div class="hidden md:flex items-center gap-1">
                <button
                  v-for="preset in batchSizePresets"
                  :key="preset"
                  @click="setBatchSize(preset)"
                  :class="[
                    'rounded-lg px-2.5 py-1 text-xs font-medium transition-colors',
                    normalizedBatchSize === preset
                      ? 'bg-accent-purple/10 text-accent-purple'
                      : 'bg-white text-gray-500 hover:bg-gray-200 hover:text-gray-700'
                  ]"
                >
                  {{ preset }}张
                </button>
              </div>

              <!-- Purchase button -->
              <button
                @click="goToRecharge"
                class="hidden sm:flex items-center gap-1 px-2.5 py-1.5 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <span class="material-symbols-outlined !text-base text-accent-purple">diamond</span>
                <span class="text-sm font-medium text-accent-purple">购买</span>
              </button>

              <!-- Expand/Fullscreen button -->
              <button
                @click="toggleExpand"
                class="hidden md:flex p-1.5 text-gray-400 hover:bg-gray-200 hover:text-gray-600 rounded-lg transition-colors"
                title="全屏模式">
                <span class="material-symbols-outlined !text-lg">{{ isExpanded ? 'close_fullscreen' : 'open_in_full' }}</span>
              </button>

              <!-- Send button -->
              <button
                @click="handleSend"
                :disabled="generatorStore.isGenerating || (!generatorStore.prompt.trim() && generatorStore.attachments.length === 0)"
                :class="[
                  'p-2 rounded-xl transition-all shrink-0',
                  (generatorStore.prompt.trim() || generatorStore.attachments.length > 0) && !generatorStore.isGenerating
                    ? 'bg-accent-purple text-white hover:bg-accent-purple-dark shadow-md'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                ]">
                <span class="material-symbols-outlined !text-lg">
                  {{ generatorStore.isGenerating ? 'hourglass_empty' : 'send' }}
                </span>
              </button>
            </div>
          </div>
        </div>

        <div class="hidden md:block text-[10px] text-gray-400 text-center mt-2">
          支持格式：PDF、Word (.docx)、图片 (.jpg, .png, .gif, .webp, .bmp, .svg)
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, computed, onMounted, watch, nextTick } from 'vue';
import { useGeneratorStore } from '@/store/useGeneratorStore';
import { useAppStore } from '@/store/useAppStore';
import { notification } from '@/utils/notification';
import { api } from '@/services/api';
import ModelSelectorPopup from './ModelSelectorPopup.vue';

const props = defineProps({
  showModelSelector: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:showModelSelector'])

const generatorStore = useGeneratorStore();
const appStore = useAppStore();
const fileInputRef = ref(null);
const inputBoxRef = ref(null);
const isDragging = ref(false);
const isHoveringFile = ref(null);

// Local state for model selector popup
const showModelPopup = ref(false);
const modelButtonRef = ref(null);

// Expand toggle
const isExpanded = ref(false);

// Textarea ref
const textareaRef = ref(null);

// 当前模型显示名称
const currentModelDisplay = computed(() => {
  if (generatorStore.selectedModelInfo?.display_name) {
    return generatorStore.selectedModelInfo.display_name;
  }
  return generatorStore.model || '选择模型';
});

const MIN_BATCH_SIZE = 1;
const MAX_BATCH_SIZE = 50;
const batchSizePresets = [1, 4, 8];

const normalizeBatchSize = (value) => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return MIN_BATCH_SIZE;
  return Math.min(MAX_BATCH_SIZE, Math.max(MIN_BATCH_SIZE, Math.round(numericValue)));
};

const normalizedBatchSize = computed(() => normalizeBatchSize(generatorStore.batchSize));

const setBatchSize = (value) => {
  generatorStore.setBatchSize(normalizeBatchSize(value));
};

const changeBatchSize = (delta) => {
  setBatchSize(normalizedBatchSize.value + delta);
};

watch(
  () => generatorStore.batchSize,
  (value) => {
    const normalizedValue = normalizeBatchSize(value);
    if (normalizedValue !== value) {
      generatorStore.setBatchSize(normalizedValue);
    }
  },
  { immediate: true }
);

// 聚焦时清除案例详情
const handleFocus = () => {
  if (appStore.selectedCase) {
    appStore.clearSelectedCase();
  }
};

const textareaHeight = ref(80)

const MIN_HEIGHT = 60
const MAX_HEIGHT = 300

// 上边框向上拖 → 高度增大，向下拖 → 高度减小
const startResizeHeight = (e) => {
  e.preventDefault()
  const startY = e.clientY
  const startH = textareaHeight.value

  const onMove = (ev) => {
    const delta = startY - ev.clientY  // 向上为正
    textareaHeight.value = Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, startH + delta))
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

// 触发文件选择
const triggerFileSelect = () => {
  fileInputRef.value?.click();
};

// 拖拽处理
const handleDragOver = (e) => {
  isDragging.value = true;
};

const handleDragLeave = (e) => {
  isDragging.value = false;
};

const handleDrop = (e) => {
  isDragging.value = false;
  const files = Array.from(e.dataTransfer.files || []);

  files.forEach(file => {
    if (!generatorStore.validateFileType(file)) {
      alert(`文件 "${file.name}" 格式不支持。\n支持格式：PDF、Word (.docx)、图片 (.jpg, .png, .gif, .webp, .bmp, .svg)`);
      return;
    }
    generatorStore.addAttachment(file);
  });
};

// 处理文件选择
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files || []);

  files.forEach(file => {
    // 验证文件格式
    if (!generatorStore.validateFileType(file)) {
      alert(`文件 "${file.name}" 格式不支持。\n支持格式：PDF、Word (.doc, .docx)、图片 (.jpg, .png, .gif, .webp, .bmp, .svg)`);
      return;
    }

    // 添加文件（支持任意大小）
    generatorStore.addAttachment(file);
  });

  // 清空 input，以便可以重复选择同一文件
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
};

// 移除文件
const removeFile = (index) => {
  const file = generatorStore.attachments[index];
  if (file && filePreviewUrls.has(file.name)) {
    URL.revokeObjectURL(filePreviewUrls.get(file.name));
    filePreviewUrls.delete(file.name);
  }
  generatorStore.removeAttachment(index);
};

// 获取文件图标
const getFileIcon = (file) => {
  const extension = file.name.split('.').pop().toLowerCase();

  if (['pdf'].includes(extension)) {
    return 'description';
  } else if (['doc', 'docx'].includes(extension)) {
    return 'description';
  } else if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(extension)) {
    return 'image';
  }
  return 'insert_drive_file';
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

// 判断是否为图片文件
const isImageFile = (file) => {
  const imageTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/svg+xml'];
  return imageTypes.includes(file.type);
};

// 获取文件预览URL（用于图片）
const filePreviewUrls = new Map();

const getFilePreviewUrl = (file) => {
  if (!isImageFile(file)) return null;

  // 如果已经创建过URL，直接返回
  if (filePreviewUrls.has(file.name)) {
    return filePreviewUrls.get(file.name);
  }

  // 创建新的URL
  const url = URL.createObjectURL(file);
  filePreviewUrls.set(file.name, url);
  return url;
};

// 释放文件预览URL
const revokeFilePreviewUrl = (file) => {
  if (filePreviewUrls.has(file.name)) {
    URL.revokeObjectURL(filePreviewUrls.get(file.name));
    // 不删除Map中的条目，保持引用以避免重复创建
  }
};

// 清理所有预览URL
const cleanupFilePreviewUrls = () => {
  filePreviewUrls.forEach((url) => {
    URL.revokeObjectURL(url);
  });
  filePreviewUrls.clear();
};

/**
 * 从 File 对象构建消息文件元数据
 */
const buildMessageFileMeta = (file) => {
  return {
    name: file.name,
    type: file.type,
    size: file.size,
    url: null, // 上传前为 null，上传后更新
  }
}

/**
 * 将上传结果补丁到消息文件中
 */
const patchMessageFilesWithUploadResults = (messageId, messageFiles, uploadResults) => {
  const message = generatorStore.messages.find(m => m.id === messageId)
  if (!message || !message.files) return

  // 按顺序匹配上传结果
  message.files.forEach((file, index) => {
    if (uploadResults[index]) {
      file.url = uploadResults[index].url
      file.file_id = uploadResults[index].file_id
    }
  })
}

/**
 * 发送消息 - 根据模型类型分流
 */
const handleSend = async () => {
  if ((!generatorStore.prompt.trim() && generatorStore.attachments.length === 0) || generatorStore.isGenerating) return;

  // 判断模型类型：文本模型走流式聊天，图像模型走图片生成
  const modelInfo = generatorStore.selectedModelInfo;
  const modelType = modelInfo?.model_type;

  console.log('[发送消息] 模型类型:', modelType, '模型信息:', modelInfo);

  // 根据model_type判断：文本模型走聊天，图像模型走图像生成
  if (modelType === '图像') {
    await handleImageModelSend();
  } else {
    // 默认走聊天模型（包括文本模型和未知类型）
    await handleChatModelSend();
  }
};

/**
 * 聊天模型发送 - 流式打字机效果
 */
const handleChatModelSend = async () => {
  const prompt = generatorStore.prompt.trim();
  if (!prompt && generatorStore.attachments.length === 0) return;
  const attachments = [...generatorStore.attachments];
  const messageFiles = attachments.map(buildMessageFileMeta);

  // 添加用户消息
  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: prompt,
    files: messageFiles
  };
  await generatorStore.addMessage(userMessage);

  // 清空输入和附件
  generatorStore.prompt = '';
  generatorStore.clearAttachments();

  // 添加 AI 占位消息
  const assistantMessage = {
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    status: 'processing'
  };
  await generatorStore.addMessage(assistantMessage);

  generatorStore.isGenerating = true;

  try {
    const chatRequest = {
      messages: generatorStore.messages
        .filter(m => m.status !== 'error')
        .map(m => ({ role: m.role, content: m.content })),
      session_id: generatorStore.currentSessionId,
      enable_context: true,
      model: generatorStore.selectedModelInfo?.model_name || generatorStore.model,
      model_type: 'chat',
      stream: true,
    };

    // 如果有附件，需要先上传文件
    if (attachments.length > 0) {
      notification.info('上传文件中', `正在上传 ${attachments.length} 个文件...`);

      try {
        const uploadResults = await api.uploadFiles(attachments, (progress, current, total) => {
          generatorStore.updateMessage(assistantMessage.id, {
            content: `正在上传文件... (${current}/${total}) - ${progress}%`
          });
        });
        patchMessageFilesWithUploadResults(userMessage.id, messageFiles, uploadResults);

        // 获取上传的文件URL列表（MinIO完整URL）
        const uploadedFileUrls = uploadResults.map(f => f.url).filter(url => url);

        chatRequest.files = uploadedFileUrls.length > 0 ? uploadedFileUrls : undefined;
        notification.success('文件上传成功', `已上传 ${uploadedFileUrls.length} 个文件`);

        console.log('[聊天模型] 请求参数:', {
          ...chatRequest,
          files: chatRequest.files
        });
      } catch (uploadError) {
        console.error('[文件上传] 失败:', uploadError);
        generatorStore.updateMessage(assistantMessage.id, {
          content: `文件上传失败: ${uploadError?.response?.data?.detail || uploadError?.message || '未知错误'}`,
          status: 'error'
        });
        notification.error('文件上传失败', uploadError?.response?.data?.detail || uploadError?.message || '未知错误');
        generatorStore.isGenerating = false;
        return;
      }
    }

    let fullContent = '';

    api.assistantChatStream(chatRequest, {
      onChunk(content) {
        fullContent += content;
        generatorStore.updateMessage(assistantMessage.id, {
          content: fullContent,
          status: 'processing'
        });
      },
      onDone() {
        generatorStore.updateMessage(assistantMessage.id, {
          content: fullContent || '(空回复)',
          status: 'completed'
        });
        generatorStore.isGenerating = false;

        // 保存到服务器
        const completedMsg = generatorStore.messages.find(m => m.id === assistantMessage.id);
        if (completedMsg && generatorStore.sessionSavedToHistory) {
          generatorStore.saveMessageToServer(completedMsg);
        }
      },
      onError(error) {
        generatorStore.updateMessage(assistantMessage.id, {
          content: `请求失败: ${error}`,
          status: 'error'
        });
        generatorStore.isGenerating = false;
        notification.error('请求失败', error);
      }
    });
  } catch (error) {
    generatorStore.updateMessage(assistantMessage.id, {
      content: `请求失败: ${error?.message || '未知错误'}`,
      status: 'error'
    });
    generatorStore.isGenerating = false;
    notification.error('请求失败', error?.message || '未知错误');
  }
};

/**
 * 图片模型发送 - 原有图片生成逻辑
 */
const handleImageModelSend = async () => {
  if ((!generatorStore.prompt.trim() && generatorStore.attachments.length === 0) || generatorStore.isGenerating) return;

  // 保存输入和附件
  const prompt = generatorStore.prompt.trim()
  const attachments = [...generatorStore.attachments]
  const messageFiles = attachments.map(buildMessageFileMeta)

  // 添加用户消息（包含附件预览信息）
  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: prompt,
    files: messageFiles
  }
  await generatorStore.addMessage(userMessage)

  // 清空输入和附件
  generatorStore.prompt = ''
  generatorStore.clearAttachments()

  // 添加AI助手消息（占位）
  const assistantMessage = {
    id: Date.now() + 1,
    role: 'assistant',
    content: '正在处理...',
    status: 'processing'
  }
  await generatorStore.addMessage(assistantMessage)

  generatorStore.isGenerating = true

  try {
    // 检查是否有图片文件
    const hasImageFile = attachments.length > 0 && attachments.some(f => f.type.startsWith('image/'))

    // 如果有图片文件，直接调用统一生图接口（不需要先上传）
    let response
    if (hasImageFile) {
      // 使用FormData直接调用统一生图接口
      const formData = new FormData()
      formData.append('prompt', prompt || '根据参考图生成')
      formData.append('model_name', generatorStore.selectedModelInfo?.model_name || generatorStore.model)
      formData.append('provider', generatorStore.selectedModelInfo?.provider || '')
      formData.append('width', generatorStore.width.toString())
      formData.append('height', generatorStore.height.toString())
      formData.append('quality', generatorStore.quality)
      formData.append('n', generatorStore.batchSize.toString())
      formData.append('operation_type', 'generate')

      // 添加参考图片
      const imageFile = attachments.find(f => f.type.startsWith('image/'))
      if (imageFile) {
        formData.append('image', imageFile)
        console.log('[统一生图] 添加参考图片:', imageFile.name, imageFile.type, imageFile.size, 'bytes')
      }

      // 添加额外参数
      const extraParams = {}
      if (generatorStore.negativePrompt) extraParams.negative_prompt = generatorStore.negativePrompt
      if (generatorStore.seed) extraParams.seed = parseInt(generatorStore.seed)
      formData.append('extra_params', JSON.stringify(extraParams))

      console.log('[统一生图] 发送请求（带参考图）')
      console.log('[统一生图] FormData内容:', {
        prompt: prompt || '根据参考图生成',
        model_name: generatorStore.selectedModelInfo?.model_name || generatorStore.model,
        provider: generatorStore.selectedModelInfo?.provider,
        has_image: !!imageFile
      })

      const apiConfig = (await import('@/store/useApiConfigStore')).useApiConfigStore()
      const baseURL = apiConfig.apiEndpoint || ''
      const accessToken = localStorage.getItem('access_token')
      const requestHeaders = {}
      if (accessToken) {
        requestHeaders.Authorization = `Bearer ${accessToken}`
      }
      if (apiConfig.apiKey) {
        requestHeaders['X-Model-Api-Key'] = apiConfig.apiKey
      }

      const res = await fetch(`${baseURL}/api/v1/generate-unified`, {
        method: 'POST',
        headers: requestHeaders,
        body: formData
      })

      if (!res.ok) throw new Error(`请求失败 (${res.status})`)
      response = await res.json()

      // 转换为统一格式
      if (response.task_id) {
        response = {
          message: { content: '正在生成图像...' },
          intent: { type: 'single_generate' },
          task_id: response.task_id
        }
      }
    } else {
      // 非图片文件（PDF/Word等）需要先上传
      let uploadedFiles = []
      if (attachments.length > 0) {
        // 如果有 PDF，按页数设置批量数量
        const pdfFile = attachments.find(f => f.name.toLowerCase().endsWith('.pdf'))
        if (pdfFile) {
          try {
            const { getDocument } = await import('pdfjs-dist')
            const arrayBuffer = await pdfFile.arrayBuffer()
            const pdf = await getDocument({ data: arrayBuffer }).promise
            const pageCount = pdf.numPages

            // 对于大PDF文件，限制单次生成数量并提供提示
            const MAX_BATCH = 20
            if (pageCount > MAX_BATCH) {
              generatorStore.batchSize = MAX_BATCH
              notification.info('PDF 文件较大', `PDF 共 ${pageCount} 页，为避免超时将分批处理。当前批次将生成前 ${MAX_BATCH} 页，您可以多次发送请求完成全部页面。`)
            } else {
              generatorStore.batchSize = pageCount
              notification.info('PDF 已识别', `共 ${pageCount} 页，将生成 ${pageCount} 张图片`)
            }
          } catch (e) {
            console.warn('[PDF] 无法读取页数，使用当前批量设置', e)
          }
        }

        notification.info('上传文件中', `正在上传 ${attachments.length} 个文件...`)

        try {
          const uploadResults = await api.uploadFiles(attachments, (progress, current, total) => {
            generatorStore.updateMessage(assistantMessage.id, {
              content: `正在上传文件... (${current}/${total}) - ${progress}%`
            })
          })

          patchMessageFilesWithUploadResults(userMessage.id, messageFiles, uploadResults)
          uploadedFiles = uploadResults.map(f => f.url)
          notification.success('文件上传成功', `已上传 ${uploadedFiles.length} 个文件`)
        } catch (uploadError) {
          console.error('[文件上传] 失败:', uploadError)
          generatorStore.updateMessage(assistantMessage.id, {
            content: `文件上传失败: ${uploadError?.response?.data?.detail || uploadError?.message || '未知错误'}`,
            status: 'error'
          })
          notification.error('文件上传失败', uploadError?.response?.data?.detail || uploadError?.message || '未知错误')
          generatorStore.isGenerating = false
          return
        }
      }

      // 准备聊天请求
      const chatRequest = {
        messages: generatorStore.messages.map(m => ({
          role: m.role,
          content: m.content
        })),
        session_id: generatorStore.currentSessionId,
        files: uploadedFiles.length > 0 ? uploadedFiles : undefined,
        model: generatorStore.selectedModelInfo?.model_name || generatorStore.model,
        model_type: 'image',
        image_params: {
          width: generatorStore.width,
          height: generatorStore.height,
          quality: generatorStore.quality,
          n: generatorStore.batchSize,
          negative_prompt: generatorStore.negativePrompt || undefined,
          seed: generatorStore.seed ? parseInt(generatorStore.seed) : undefined,
          model_name: generatorStore.model || undefined,
          provider: generatorStore.selectedModelInfo?.provider || undefined
        }
      }

      console.log('[AI助手] 发送聊天请求:', chatRequest)

      // 调用统一AI助手接口
      response = await api.assistantChat(chatRequest)
    }

    console.log('[AI助手] 收到响应:', response)

    // 根据响应处理
    if (response.intent && response.intent.type) {
      const intent = response.intent

      if (intent.type === 'single_generate' && response.task_id) {
        // 单图生成
        const initialStage = response.metadata?.stage || 'request_received'
        const initialStageIndex = ({
          request_received: 1,
          queued: 2,
          extracting_prompt: 3,
          semantic_understanding: 4,
          generating_images: 5,
          validating_images: 6,
          saving_images: 7,
          recording_result: 8,
          completed: 9
        })[initialStage] || 1
        const initialProgressValue = Number(response.metadata?.progress_percent ?? response.metadata?.progress)
        const initialProgressPercent = Number.isFinite(initialProgressValue)
          ? Math.max(0, Math.min(100, Math.round(initialProgressValue <= 1 ? initialProgressValue * 100 : initialProgressValue)))
          : (initialStage === 'request_received' ? 6 : 12)
        generatorStore.updateMessage(assistantMessage.id, {
          content: response.message.content,
          taskId: response.task_id,
          status: 'processing',
          billing: response.metadata?.billing || undefined,
          generationProgress: {
            stage: initialStage,
            stageLabel: response.metadata?.stage_label || '请求已接收',
            stageMessage: response.metadata?.stage_message || response.message.content,
            progressPercent: initialProgressPercent,
            attempt: Number.isFinite(response.metadata?.attempt) ? Number(response.metadata.attempt) : 0,
            stageIndex: initialStageIndex,
            totalStages: 9,
            updatedAt: response.metadata?.updated_at || '',
            history: []
          }
        })

        notification.info('生成任务已创建', `任务ID: ${response.task_id}`)

        // 轮询任务状态
        generatorStore.pollTaskStatus(response.task_id, assistantMessage.id, 900, 2000).then(success => {
          if (success) {
            notification.success('图像生成完成！')
          }
        })

      } else if (intent.type === 'batch_generate' && response.batch_id) {
        // 批量生成
        const totalCount = response.metadata?.total_count || intent.parameters?.count || 4

        generatorStore.updateMessage(assistantMessage.id, {
          content: response.message.content,
          batchId: response.batch_id,
          status: 'processing',
          batchCount: totalCount,
          billing: response.metadata?.billing || undefined,
          batchProgress: {
            completed: 0,
            total: totalCount,
            images: [],
            stage: response.metadata?.stage || 'queued',
            stageLabel: response.metadata?.stage_label || '排队中',
            stageMessage: response.metadata?.stage_message || response.message.content,
            progressPercent: response.metadata?.status_detail?.progress_percent || 0,
            running: response.metadata?.status_detail?.running_tasks || 0,
            pending: response.metadata?.status_detail?.pending_tasks || totalCount,
            failed: response.metadata?.status_detail?.failed_tasks || 0,
            stageOverview: response.metadata?.status_detail?.stage_overview || [],
          }
        })

        notification.info('批量任务已创建', `共 ${totalCount} 张图片`)

        // 轮询批量任务状态
        generatorStore.pollBatchStatusIncremental(response.batch_id, assistantMessage.id, totalCount, 900, 2000).then(success => {
          if (success) {
            notification.success('批量生成完成！')
          }
        })

      } else {
        // 普通对话响应（或积分不足等情况）
        const updatedMessage = {
          content: response.message.content,
          status: 'completed',
          images: response.message.images || null,
          billing: response.metadata?.billing || undefined
        }
        generatorStore.updateMessage(assistantMessage.id, updatedMessage)

        // 同步助手回复到服务器
        const completedMessage = generatorStore.messages.find(m => m.id === assistantMessage.id)
        if (completedMessage && generatorStore.sessionSavedToHistory) {
          generatorStore.saveMessageToServer(completedMessage)
        }
      }
    } else {
      // 没有意图，直接显示消息
      const updatedMessage = {
        content: response.message.content || '处理完成',
        status: 'completed',
        images: response.message.images || null
      }
      generatorStore.updateMessage(assistantMessage.id, updatedMessage)

      // 同步助手回复到服务器
      const completedMessage = generatorStore.messages.find(m => m.id === assistantMessage.id)
      if (completedMessage && generatorStore.sessionSavedToHistory) {
        generatorStore.saveMessageToServer(completedMessage)
      }
    }

  } catch (error) {
    console.error('[AI助手] 请求失败:', error)

    // 显示错误消息
    generatorStore.updateMessage(assistantMessage.id, {
      content: `请求失败: ${error?.response?.data?.detail || error?.message || '未知错误'}`,
      status: 'error'
    })

    notification.error('请求失败', error?.response?.data?.detail || error?.message || '未知错误')
  } finally {
    generatorStore.isGenerating = false
  }
};

// 组件卸载时清理预览URL
onUnmounted(() => {
  cleanupFilePreviewUrls();
});

// Navigate to recharge page
const goToRecharge = () => {
  appStore.setCurrentPage('user-center', 'balance');
};

// Create new conversation
const handleNewConversation = () => {
  generatorStore.clearMessages();
  generatorStore.clearAttachments();
  generatorStore.prompt = '';
};

// Toggle expand/fullscreen mode
const toggleExpand = () => {
  isExpanded.value = !isExpanded.value;
  if (isExpanded.value) {
    textareaHeight.value = MAX_HEIGHT;
  } else {
    textareaHeight.value = 80;
  }
};

// Handle model selection from popup
const handleModelSelect = (model) => {
  generatorStore.setSelectedModel(model.model_name);
  generatorStore.setSelectedModelInfo(model);
  showModelPopup.value = false;
};

// 自动发送处理
const handleAutoSend = async () => {
  // 确保有内容可发送
  if ((!generatorStore.prompt.trim() && generatorStore.attachments.length === 0)) {
    return;
  }

  // 确保模型信息已加载
  if (!generatorStore.selectedModelInfo) {
    console.warn('[自动发送] 模型信息未加载');
    return;
  }

  // 清除标记，防止重复触发
  generatorStore.clearPendingAutoSend();

  // 使用 nextTick 确保 DOM 已更新
  await nextTick();

  // 触发发送
  await handleSend();
};

// 监听自动发送标记
watch(
  () => generatorStore.pendingAutoSend,
  async (newValue) => {
    if (newValue) {
      // 延迟执行，确保 ChatView 完全渲染
      setTimeout(() => {
        handleAutoSend();
      }, 100);
    }
  },
  { immediate: true }
);
</script>

<style scoped>
/* 自定义滚动条样式，如果全局没有定义的话 */
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
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #b7c0ba;
}
</style>
