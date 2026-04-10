<template>
  <div class="shrink-0 border-t border-border-dark bg-white/55 backdrop-blur-xl">
    <div class="px-3 py-3 xs:px-4 md:px-6 md:py-4">
      <div class="mx-auto w-full md:w-[68%]">
        <div v-if="generatorStore.attachments.length > 0" class="mb-3 flex flex-wrap gap-2">
          <div
            v-for="(file, index) in generatorStore.attachments"
            :key="index"
            class="relative flex max-w-full items-center gap-2 overflow-hidden rounded-2xl border border-border-dark bg-white px-2 py-2 text-xs shadow-sm"
            :class="{ 'ring-2 ring-primary/25': isHoveringFile === index }"
          >
            <div class="relative z-10 flex min-w-0 items-center gap-2">
              <div v-if="isImageFile(file)" class="relative shrink-0">
                <img
                  :src="getFilePreviewUrl(file)"
                  :alt="file.name"
                  class="h-[56px] w-[56px] rounded-xl border border-border-dark object-cover"
                >
              </div>
              <span v-else class="material-symbols-outlined !text-base text-primary">{{ getFileIcon(file) }}</span>
              <div class="min-w-0">
                <div class="max-w-[140px] truncate text-sm font-medium text-ink-950">{{ file.name }}</div>
                <div class="text-[11px] text-ink-500">{{ formatFileSize(file.size || 0) }}</div>
              </div>
              <el-button
                circle
                text
                @click.stop="removeFile(index)"
                @mouseenter="isHoveringFile = index"
                @mouseleave="isHoveringFile = null"
              >
                <span class="material-symbols-outlined !text-sm">close</span>
              </el-button>
            </div>
          </div>
        </div>

        <el-card
          ref="inputBoxRef"
          shadow="never"
          class="chat-input-card"
          :class="{ 'chat-input-card--dragging': isDragging }"
          @dragover.prevent="handleDragOver"
          @dragleave="handleDragLeave"
          @drop.prevent="handleDrop"
        >
          <template #header>
            <div class="flex items-center justify-between gap-3">
              <div ref="modelButtonRef" class="relative">
                <el-button round class="chat-input-card__model-btn" @click="showModelPopup = !showModelPopup">
                  <span class="material-symbols-outlined !text-base text-primary shrink-0">auto_awesome</span>
                  <span class="max-w-[160px] truncate text-sm font-medium">{{ currentModelDisplay }}</span>
                  <span class="material-symbols-outlined !text-sm text-ink-500 shrink-0">
                    {{ showModelPopup ? 'expand_less' : 'expand_more' }}
                  </span>
                </el-button>

                <ModelSelectorPopup
                  :visible="showModelPopup"
                  :current-model="generatorStore.model"
                  :attachments="generatorStore.attachments"
                  :trigger-element="modelButtonRef"
                  @select="handleModelSelect"
                  @close="showModelPopup = false"
                />
              </div>

              <div class="flex items-center gap-2">
                <el-upload
                  ref="uploadRef"
                  :auto-upload="false"
                  :show-file-list="false"
                  :multiple="true"
                  accept="image/*,.pdf,.docx,.doc,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  :on-change="handleUploadChange"
                >
                  <el-tooltip content="添加附件" placement="top">
                    <el-button circle>
                      <span class="material-symbols-outlined !text-lg">attach_file</span>
                    </el-button>
                  </el-tooltip>
                </el-upload>

                <el-tooltip content="新建对话" placement="top">
                  <el-button circle type="primary" plain @click="handleNewConversation">
                    <span class="material-symbols-outlined !text-base">add</span>
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </template>

          <div class="relative">
            <div
              tabindex="-1"
              class="flex h-3 w-full cursor-ns-resize items-center justify-center select-none transition-colors hover:bg-black/[0.03]"
              title="拖拽调整高度"
              @mousedown.prevent="startResizeHeight"
            >
              <div class="h-0.5 w-10 rounded-full bg-[rgba(140,42,46,0.25)]"></div>
            </div>

            <el-input
              ref="textareaRef"
              v-model="generatorStore.prompt"
              type="textarea"
              resize="none"
              class="chat-textarea"
              :style="{ '--chat-textarea-height': `${textareaHeight}px` }"
              placeholder="输入内容开始聊天 (Shift + Enter 换行) ..."
              @keydown.enter.exact.prevent="handleSend"
              @focus="handleFocus"
            />
          </div>

          <div class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border-dark/70 pt-3">
            <div class="flex flex-wrap items-center gap-2">
              <div class="flex items-center gap-2 rounded-2xl bg-[rgba(140,42,46,0.05)] px-3 py-2">
                <span class="material-symbols-outlined !text-base text-primary">imagesmode</span>
                <span class="hidden text-xs font-semibold text-ink-500 sm:inline">生图数量</span>
                <el-input-number
                  :model-value="normalizedBatchSize"
                  :min="MIN_BATCH_SIZE"
                  :max="MAX_BATCH_SIZE"
                  controls-position="right"
                  class="chat-batch-input"
                  @change="setBatchSize"
                />
              </div>

              <div class="hidden items-center gap-2 md:flex">
                <el-button
                  v-for="preset in batchSizePresets"
                  :key="preset"
                  :type="normalizedBatchSize === preset ? 'primary' : 'default'"
                  :plain="normalizedBatchSize !== preset"
                  @click="setBatchSize(preset)"
                >
                  {{ preset }}张
                </el-button>
              </div>
            </div>

            <div class="flex flex-wrap items-center justify-end gap-2">
              <el-button text class="hidden sm:inline-flex" @click="goToRecharge">
                <span class="material-symbols-outlined !text-base text-primary">diamond</span>
                <span class="text-sm font-medium text-primary">购买</span>
              </el-button>

              <el-button circle class="hidden md:inline-flex" @click="toggleExpand" title="全屏模式">
                <span class="material-symbols-outlined !text-lg">
                  {{ isExpanded ? 'close_fullscreen' : 'open_in_full' }}
                </span>
              </el-button>

              <el-button
                type="primary"
                round
                class="chat-send-button"
                :loading="generatorStore.isGenerating"
                :disabled="!canSend"
                @click="handleSend"
              >
                <span class="material-symbols-outlined !text-lg">
                  {{ generatorStore.isGenerating ? 'hourglass_empty' : 'send' }}
                </span>
                <span class="hidden sm:inline">发送</span>
              </el-button>
            </div>
          </div>
        </el-card>

        <div class="mt-2 hidden text-center text-[10px] text-gray-400 md:block">
          支持格式：PDF、Word (.docx)、图片 (.jpg, .png, .gif, .webp, .bmp, .svg)
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, computed, onMounted, watch, nextTick } from 'vue';
import { useGeneratorStore } from '@/store/useGeneratorStore';
import { useRouter } from 'vue-router';
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
const router = useRouter();
const appStore = useAppStore();
const uploadRef = ref(null);
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

const trimContextSnippet = (value, maxLength = 220) => {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}…`;
};

const isPlaceholderAssistantMessage = (value) => {
  const text = String(value || '').trim();
  if (!text) return true;
  return [
    '正在处理',
    '正在上传文件',
    '请求失败:',
    '抱歉，对话请求失败',
  ].some((prefix) => text.startsWith(prefix));
};

const buildImageGenerationMessages = (latestPrompt) => {
  const meaningfulMessages = generatorStore.messages.filter((message) => {
    if (message.status === 'error') return false;
    if (message.role === 'assistant' && isPlaceholderAssistantMessage(message.content)) return false;
    return Boolean(String(message.content || '').trim());
  });

  const latestUserMessage = [...meaningfulMessages].reverse().find((message) => message.role === 'user');
  const latestRequest = trimContextSnippet(latestPrompt || latestUserMessage?.content || '', 1400);

  const previousMessages = meaningfulMessages.filter((message) => message !== latestUserMessage);
  const previousUserPrompts = previousMessages
    .filter((message) => message.role === 'user')
    .slice(-3)
    .map((message, index) => `历史提示词 ${index + 1}: ${trimContextSnippet(message.content)}`);
  const previousAssistantReplies = previousMessages
    .filter((message) => message.role === 'assistant')
    .slice(-2)
    .map((message, index) => `历史辅助结果 ${index + 1}: ${trimContextSnippet(message.content, 180)}`);

  const contextSections = [];
  if (previousUserPrompts.length > 0) {
    contextSections.push(previousUserPrompts.join('\n'));
  }
  if (previousAssistantReplies.length > 0) {
    contextSections.push(previousAssistantReplies.join('\n'));
  }

  const messages = [];
  if (contextSections.length > 0) {
    messages.push({
      role: 'system',
      content: [
        '当前是连续生图场景：请始终以“最新用户请求”为主提示词，仅在相关时把历史内容当作辅助参考，不要被旧提示词覆盖。',
        contextSections.join('\n\n'),
      ].join('\n\n'),
    });
  }

  messages.push({
    role: 'user',
    content: latestRequest,
  });

  return messages;
};

const canSend = computed(() => {
  return !generatorStore.isGenerating && Boolean(generatorStore.prompt.trim() || generatorStore.attachments.length > 0);
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
const handleUploadChange = (uploadFile) => {
  const file = uploadFile?.raw || uploadFile;
  if (!file) return;

  if (!generatorStore.validateFileType(file)) {
    alert(`文件 "${file.name}" 格式不支持。\n支持格式：PDF、Word (.doc, .docx)、图片 (.jpg, .png, .gif, .webp, .bmp, .svg)`);
    uploadRef.value?.clearFiles?.();
    return;
  }

  generatorStore.addAttachment(file);
  uploadRef.value?.clearFiles?.();
};

// 移除文件
const removeFile = (index) => {
  const file = generatorStore.attachments[index];
  if (file) {
    releaseFilePreviewUrl(file);
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
  if (filePreviewUrls.has(file)) {
    return filePreviewUrls.get(file);
  }

  // 创建新的URL
  const url = URL.createObjectURL(file);
  filePreviewUrls.set(file, url);
  return url;
};

// 释放文件预览URL
const releaseFilePreviewUrl = (file) => {
  const previewUrl = filePreviewUrls.get(file);
  if (!previewUrl) return;
  URL.revokeObjectURL(previewUrl);
  filePreviewUrls.delete(file);
};

// 清理所有预览URL
const cleanupFilePreviewUrls = () => {
  filePreviewUrls.forEach((url) => {
    URL.revokeObjectURL(url);
  });
  filePreviewUrls.clear();
};

const releaseMessageFilePreviewUrl = (fileMeta) => {
  const previewUrl = fileMeta?.local_url || fileMeta?.preview_url;
  if (!previewUrl || !String(previewUrl).startsWith('blob:')) return;
  URL.revokeObjectURL(previewUrl);
};

const releaseMessageFilesPreviewUrls = (files = []) => {
  files.forEach((fileMeta) => releaseMessageFilePreviewUrl(fileMeta));
};

/**
 * 从 File 对象构建消息文件元数据
 */
const buildMessageFileMeta = (file) => {
  const messageFile = {
    name: file.name,
    type: file.type,
    size: file.size,
    url: null, // 上传前为 null，上传后更新
  };

  if (isImageFile(file)) {
    messageFile.local_url = URL.createObjectURL(file);
  }

  return messageFile;
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
      if (file.url) {
        releaseMessageFilePreviewUrl(file)
        delete file.local_url
        delete file.preview_url
      }
    }
  })
}

/**
 * 发送消息 - 根据模型类型分流（含防重复提交锁）
 */
let _sendLock = false
const handleSend = async () => {
  if ((!generatorStore.prompt.trim() && generatorStore.attachments.length === 0) || generatorStore.isGenerating) return;
  // 防止快速重复点击
  if (_sendLock) return;
  _sendLock = true;

  // 判断模型类型：文本模型走流式聊天，图像模型走图片生成
  const modelInfo = generatorStore.selectedModelInfo;
  const modelType = modelInfo?.model_type;
  const modelName = modelInfo?.model_name || generatorStore.model || '';
  const promptText = generatorStore.prompt.trim().toLowerCase();

  // 判断是否应该走图像生成流程
  const isImageModel = modelType === '图像' || modelName.includes('image');
  const hasImageKeywords = /生成|生图|画|海报|绘制|出图|创建图片|配图|封面|渲染|插画/.test(promptText);
  const hasAttachments = generatorStore.attachments.length > 0;

  console.log('[发送消息] 模型类型:', modelType, '模型名:', modelName, '图像模型:', isImageModel, '含生图关键词:', hasImageKeywords, '有附件:', hasAttachments);

  // 图像模型、或有附件+生图关键词 → 走图像生成
  try {
    if (isImageModel || (hasAttachments && hasImageKeywords)) {
      await handleImageModelSend();
    } else {
      // 默认走聊天模型
      await handleChatModelSend();
    }
  } finally {
    _sendLock = false;
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

        // 保存到服务器并更新会话标题
        const completedMsg = generatorStore.messages.find(m => m.id === assistantMessage.id);
        if (completedMsg && generatorStore.sessionSavedToHistory) {
          generatorStore.saveMessageToServer(completedMsg);
          generatorStore.summarizeSession();
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
 * 图片模型发送 - 统一走附件理解/ OCR 后再进入生图流程
 */
const handleImageModelSend = async () => {
  if ((!generatorStore.prompt.trim() && generatorStore.attachments.length === 0) || generatorStore.isGenerating) {
    _sendLock = false;
    return;
  }

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

  // 立即设置生成中状态，防止重复提交
  generatorStore.isGenerating = true

  try {
    let response
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
        uploadedFiles = uploadResults.map(f => f.url).filter(Boolean)
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

    // 所有附件统一走 assistant 工作流：
    // 上传附件 -> OCR/内容理解 -> 规划生图 -> 创建任务
    const chatRequest = {
      messages: buildImageGenerationMessages(prompt),
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

    console.log('[AI助手] 统一附件生图请求:', {
      ...chatRequest,
      files: chatRequest.files,
      attachmentCount: attachments.length
    })

    response = await api.assistantChat(chatRequest)

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
        if (response.metadata?.billing) {
          await generatorStore.refreshAccountInfoSilently(response.metadata.billing)
        }

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
        if (response.metadata?.billing) {
          await generatorStore.refreshAccountInfoSilently(response.metadata.billing)
        }

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
        if (response.metadata?.billing) {
          await generatorStore.refreshAccountInfoSilently(response.metadata.billing)
        }

        // 同步助手回复到服务器并更新标题
        const completedMessage = generatorStore.messages.find(m => m.id === assistantMessage.id)
        if (completedMessage && generatorStore.sessionSavedToHistory) {
          generatorStore.saveMessageToServer(completedMessage)
          generatorStore.summarizeSession()
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

      // 同步助手回复到服务器并更新标题
      const completedMessage = generatorStore.messages.find(m => m.id === assistantMessage.id)
      if (completedMessage && generatorStore.sessionSavedToHistory) {
        generatorStore.saveMessageToServer(completedMessage)
        generatorStore.summarizeSession()
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
  router.push('/user-center');
};

// Create new conversation
const handleNewConversation = async () => {
  generatorStore.messages.forEach((message) => {
    releaseMessageFilesPreviewUrls(message.files || []);
  });
  await generatorStore.startNewConversation();
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

watch(
  () => [...generatorStore.attachments],
  (newFiles, oldFiles) => {
    const activeFiles = new Set(newFiles);
    oldFiles
      .filter((file) => !activeFiles.has(file))
      .forEach((file) => releaseFilePreviewUrl(file));
  }
);
</script>

<style scoped>
.chat-input-card {
  border-radius: 28px;
  border: 1px solid var(--color-border-dark);
  background: rgba(255, 253, 252, 0.96);
  box-shadow: 0 24px 48px rgba(88, 28, 32, 0.12);
}

.chat-input-card--dragging {
  border-color: rgba(140, 42, 46, 0.5);
  background: rgba(140, 42, 46, 0.04);
}

.chat-input-card :deep(.el-card__header) {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(232, 215, 214, 0.8);
}

.chat-input-card :deep(.el-card__body) {
  padding: 0 16px 16px;
}

.chat-input-card__model-btn {
  max-width: min(100%, 260px);
}

.chat-textarea :deep(.el-textarea__inner) {
  min-height: var(--chat-textarea-height) !important;
  height: var(--chat-textarea-height) !important;
  padding: 8px 0 0;
  border: none;
  box-shadow: none !important;
  background: transparent;
  color: var(--color-ink-950);
  font-size: 14px;
  line-height: 1.7;
}

.chat-textarea :deep(.el-textarea__inner::placeholder) {
  color: var(--color-ink-500);
}

.chat-batch-input {
  width: 124px;
}

.chat-batch-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: rgba(255, 253, 252, 0.9);
}

.chat-send-button {
  min-width: 110px;
}
</style>
