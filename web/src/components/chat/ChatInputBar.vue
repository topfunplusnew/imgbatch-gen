<template>
  <div class="bg-white/70 backdrop-blur-xl border-t border-border-dark flex flex-col shrink-0">
    <!-- 已选文件列表 -->
    <div v-if="generatorStore.attachments.length > 0" class="px-3 md:px-6 pt-2 flex flex-wrap gap-2">
      <div
        v-for="(file, index) in generatorStore.attachments"
        :key="index"
        class="flex items-center gap-1.5 px-2 py-1 bg-white border border-border-dark rounded-lg text-xs shadow-lg">
        <span class="material-symbols-outlined !text-sm text-primary">{{ getFileIcon(file) }}</span>
        <span class="text-ink-700 max-w-[120px] truncate">{{ file.name }}</span>
        <button @click="removeFile(index)" class="text-ink-500 hover:text-red-400 transition-colors">
          <span class="material-symbols-outlined !text-sm">close</span>
        </button>
      </div>
    </div>

    <div class="px-3 md:px-6 py-2 md:py-4">
      <div class="max-w-full md:max-w-4xl mx-auto w-full">
        <div
          ref="inputBoxRef"
          @dragover.prevent="handleDragOver"
          @dragleave="handleDragLeave"
          @drop.prevent="handleDrop"
          :class="[
            'relative z-10 bg-white/95 border rounded-2xl shadow-xl w-full min-w-[200px] md:min-w-[280px] max-w-full md:max-w-[800px]',
            isDragging ? 'border-primary border-2 bg-primary/5' : 'border-border-dark'
          ]">

          <!-- 上边框拖拽把手：拖动改变高度，不可获取焦点 -->
          <div
            @mousedown.prevent="startResizeHeight"
            tabindex="-1"
            class="w-full h-4 flex items-center justify-center cursor-ns-resize rounded-t-2xl select-none hover:bg-primary/5 transition-colors"
            title="拖拽调整高度">
            <div class="w-10 h-1 bg-border-dark rounded-full opacity-70 hover:opacity-100 transition-opacity pointer-events-none"></div>
          </div>

          <!-- 内容区 -->
          <div class="relative flex items-end gap-2 px-2 pb-2">
            <input
              ref="fileInputRef"
              type="file"
              multiple
              accept=".pdf,.docx,.jpg,.jpeg,.png,.gif,.webp,.bmp,.svg"
              @change="handleFileSelect"
              class="hidden">

            <button
              @click="triggerFileSelect"
              class="p-2 hover:bg-primary/5 rounded-xl text-ink-500 transition-colors shrink-0">
              <span class="material-symbols-outlined">attach_file</span>
            </button>

            <textarea
              v-model="generatorStore.prompt"
              @keydown.enter.exact.prevent="handleSend"
              :style="{ height: textareaHeight + 'px' }"
              class="flex-1 bg-transparent border-none focus:ring-0 text-sm py-2 px-2 overflow-y-auto custom-scrollbar min-w-0 resize-none text-ink-950 placeholder:text-ink-500"
              placeholder="描述您想要创建的图像...">
            </textarea>

            <button
              @click="handleSend"
              :disabled="generatorStore.isGenerating || (!generatorStore.prompt.trim() && generatorStore.attachments.length === 0)"
              class="p-2 bg-primary-strong text-white rounded-xl shadow-lg hover:bg-primary-deep disabled:opacity-50 disabled:cursor-not-allowed shrink-0">
              <span class="material-symbols-outlined">{{ generatorStore.isGenerating ? 'hourglass_empty' : 'send' }}</span>
            </button>

          </div>
        </div>

        <div class="hidden md:block text-[10px] text-ink-500 text-center mt-2">
          支持格式：PDF、Word (.docx)、图片 (.jpg, .png, .gif, .webp, .bmp, .svg)
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useGeneratorStore } from '@/store/useGeneratorStore';
import { notification } from '@/utils/notification';
import { api } from '@/services/api';

const generatorStore = useGeneratorStore();
const fileInputRef = ref(null);
const inputBoxRef = ref(null);
const isDragging = ref(false);

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

  // 添加用户消息
  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: prompt,
    files: generatorStore.attachments.map(f => ({
      name: f.name,
      size: f.size,
      type: f.type
    }))
  };
  await generatorStore.addMessage(userMessage);

  // 清空输入和附件
  generatorStore.prompt = '';
  const attachments = [...generatorStore.attachments];
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

  // 添加用户消息（包含附件预览信息）
  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: prompt,
    files: attachments.map(f => ({
      name: f.name,
      size: f.size,
      type: f.type
    }))
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
      // formData.append('style', generatorStore.style)
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

      const res = await fetch(`${baseURL}/api/v1/generate-unified`, {
        method: 'POST',
        headers: apiConfig.apiKey ? { Authorization: `Bearer ${apiConfig.apiKey}` } : {},
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
          // style: generatorStore.style,
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
        generatorStore.updateMessage(assistantMessage.id, {
          content: response.message.content,
          taskId: response.task_id,
          status: 'processing'
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
          batchCount: totalCount
        })

        notification.info('批量任务已创建', `共 ${totalCount} 张图片`)

        // 轮询批量任务状态
        generatorStore.pollBatchStatus(response.batch_id, assistantMessage.id, totalCount, 900, 2000).then(success => {
          if (success) {
            notification.success('批量生成完成！')
          }
        })

      } else {
        // 普通对话响应
        const updatedMessage = {
          content: response.message.content,
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
