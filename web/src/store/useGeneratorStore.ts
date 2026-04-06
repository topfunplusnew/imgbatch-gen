import { defineStore } from 'pinia'
import { useHistoryStore } from './useHistoryStore'
import { api } from '@/services/api'
import { mockGenerateImage, mockGetTaskStatus, isMockMode } from '@/utils/mockApi'

const ACTIVE_TASK_STATUSES = new Set(['pending', 'processing', 'running'])
const FAILED_TASK_STATUSES = new Set(['failed', 'error', 'cancelled', 'canceled'])
const TERMINAL_TASK_STATUSES = new Set(['completed', ...FAILED_TASK_STATUSES])
const DEFAULT_GEMINI_MODEL = 'gemini-3.1-flash-image-preview'

const STAGE_LABEL_MAP: Record<string, string> = {
    request_received: '请求已接收',
    queued: '排队中',
    extracting_prompt: '提示词提取中',
    semantic_understanding: '语义理解中',
    generating_images: '生图请求中',
    validating_images: '结果校验中',
    saving_images: '图片保存中',
    recording_result: '结果记录中',
    retrying: '重试等待中',
    completed: '已完成',
    failed: '失败',
}

const FALLBACK_STAGE_ORDER = [
    'generating_images',
    'saving_images',
    'validating_images',
    'recording_result',
    'semantic_understanding',
    'extracting_prompt',
    'retrying',
    'queued',
    'request_received',
    'completed',
    'failed',
]

const SINGLE_TASK_STAGE_ORDER = [
    'request_received',
    'queued',
    'extracting_prompt',
    'semantic_understanding',
    'generating_images',
    'validating_images',
    'saving_images',
    'recording_result',
    'completed',
]

const STAGE_PROGRESS_MAP: Record<string, number> = {
    request_received: 6,
    queued: 12,
    extracting_prompt: 24,
    semantic_understanding: 40,
    generating_images: 72,
    validating_images: 86,
    saving_images: 93,
    recording_result: 97,
    retrying: 46,
    completed: 100,
    failed: 100,
}

function clampPercent(value: number) {
    return Math.max(0, Math.min(100, Math.round(value)))
}

function normalizeProgressPercent(value: any): number | null {
    const num = Number(value)
    if (!Number.isFinite(num)) return null
    if (num <= 1) return clampPercent(num * 100)
    return clampPercent(num)
}

function getStageProgressPercent(stage?: string) {
    return STAGE_PROGRESS_MAP[String(stage || '').toLowerCase()] ?? 12
}

function getSingleTaskStageIndex(stage?: string) {
    const normalizedStage = String(stage || '').toLowerCase()
    const index = SINGLE_TASK_STAGE_ORDER.indexOf(normalizedStage)
    return index >= 0 ? index + 1 : null
}

function getStageLabel(stage?: string) {
    if (!stage) return '处理中'
    return STAGE_LABEL_MAP[stage] || stage
}

function getTaskStageMessage(task: any, fallbackMessage: string) {
    return task?.stage_message || task?.status_detail?.current_stage_message || fallbackMessage
}

function normalizeTaskStageHistory(events: any[]) {
    if (!Array.isArray(events)) return []

    return events
        .slice(-4)
        .map((event) => {
            const stage = String(event?.stage || '').trim()
            const status = String(event?.status || '').toLowerCase()
            return {
                stage,
                label: event?.label || getStageLabel(stage),
                message: event?.message || getStageLabel(stage),
                status,
                progressPercent: normalizeProgressPercent(event?.progress) ?? getStageProgressPercent(stage),
                attempt: Number.isFinite(event?.attempt) ? Number(event.attempt) : 0,
                timestamp: event?.timestamp || '',
            }
        })
        .filter((event) => event.stage || event.message)
}

function buildTaskProgressPayload(task: any, fallbackMessage: string) {
    const stage = String(task?.stage || '').trim() || 'queued'
    const history = normalizeTaskStageHistory(task?.stage_history)
    const latestHistory = history[history.length - 1]
    const taskStatus = String(task?.status || '').toLowerCase()
    const progressPercent = taskStatus === 'completed'
        ? 100
        : (
            normalizeProgressPercent(task?.progress)
            ?? latestHistory?.progressPercent
            ?? getStageProgressPercent(stage)
        )
    const attempt = Number.isFinite(task?.attempt)
        ? Number(task.attempt)
        : (latestHistory?.attempt || 0)

    return {
        stage,
        stageLabel: task?.stage_label || latestHistory?.label || getStageLabel(stage),
        stageMessage: getTaskStageMessage(task, fallbackMessage),
        progressPercent,
        attempt,
        stageIndex: getSingleTaskStageIndex(stage),
        totalStages: SINGLE_TASK_STAGE_ORDER.length,
        updatedAt: task?.updated_at || latestHistory?.timestamp || '',
        history,
    }
}

function buildInitialTaskProgressPayload(metadata: any, fallbackMessage: string) {
    const stage = String(metadata?.stage || 'request_received').trim() || 'request_received'
    return {
        stage,
        stageLabel: metadata?.stage_label || getStageLabel(stage),
        stageMessage: metadata?.stage_message || fallbackMessage,
        progressPercent: normalizeProgressPercent(metadata?.progress_percent ?? metadata?.progress) ?? getStageProgressPercent(stage),
        attempt: Number.isFinite(metadata?.attempt) ? Number(metadata.attempt) : 0,
        stageIndex: getSingleTaskStageIndex(stage),
        totalStages: SINGLE_TASK_STAGE_ORDER.length,
        updatedAt: metadata?.updated_at || '',
        history: [],
    }
}

function buildStageOverviewFromTasks(tasks: any[]) {
    const stageCounter = new Map<string, { label: string; count: number }>()

    tasks.forEach((task) => {
        const stage = String(task?.stage || '').trim()
        if (!stage) return
        const current = stageCounter.get(stage) || {
            label: task?.stage_label || getStageLabel(stage),
            count: 0,
        }
        current.count += 1
        stageCounter.set(stage, current)
    })

    return FALLBACK_STAGE_ORDER
        .map((stage) => {
            const current = stageCounter.get(stage)
            if (!current || current.count <= 0) return null
            return {
                stage,
                label: current.label,
                count: current.count,
            }
        })
        .filter(Boolean)
}

function normalizeBatchStatusDetail(batchTask: any, fallbackTotal: number) {
    const tasks = Array.isArray(batchTask?.tasks) ? batchTask.tasks : []
    const detail = batchTask?.status_detail || {}
    const completedTasks = Number.isFinite(detail.completed_tasks) ? detail.completed_tasks : (
        Number.isFinite(batchTask?.completed) ? Number(batchTask.completed) : tasks.filter((task) => String(task?.status || '').toLowerCase() === 'completed').length
    )
    const failedTasks = Number.isFinite(detail.failed_tasks) ? detail.failed_tasks : (
        Number.isFinite(batchTask?.failed) ? Number(batchTask.failed) : tasks.filter((task) => FAILED_TASK_STATUSES.has(String(task?.status || '').toLowerCase())).length
    )
    const totalTasks = Number.isFinite(batchTask?.total) && Number(batchTask.total) > 0
        ? Number(batchTask.total)
        : (fallbackTotal || tasks.length || 1)
    const runningTasks = Number.isFinite(detail.running_tasks) ? detail.running_tasks : (
        Number.isFinite(batchTask?.running) ? Number(batchTask.running) : tasks.filter((task) => String(task?.status || '').toLowerCase() === 'running').length
    )
    const pendingTasks = Number.isFinite(detail.pending_tasks) ? detail.pending_tasks : Math.max(
        totalTasks - completedTasks - failedTasks - runningTasks,
        0
    )
    const stageOverview = Array.isArray(detail.stage_overview) && detail.stage_overview.length > 0
        ? detail.stage_overview
        : buildStageOverviewFromTasks(tasks)
    const currentStage = detail.current_stage || batchTask?.stage || stageOverview[0]?.stage || 'queued'
    const currentStageLabel = detail.current_stage_label || batchTask?.stage_label || getStageLabel(currentStage)
    const progressFromTasks = tasks.reduce((totalProgress, task) => {
        const taskStatus = String(task?.status || '').toLowerCase()
        if (taskStatus === 'completed' || FAILED_TASK_STATUSES.has(taskStatus)) {
            return totalProgress + 1
        }
        const normalized = normalizeProgressPercent(task?.progress)
        if (normalized !== null) return totalProgress + normalized / 100
        return totalProgress + (getStageProgressPercent(task?.stage) / 100)
    }, 0)
    const progressPercent = Number.isFinite(detail.progress_percent)
        ? clampPercent(Number(detail.progress_percent))
        : clampPercent(progressFromTasks / Math.max(totalTasks, 1) * 100)
    const currentStageMessage = detail.current_stage_message
        || batchTask?.stage_message
        || `${currentStageLabel}，已完成 ${completedTasks}/${totalTasks}`

    return {
        currentStage,
        currentStageLabel,
        currentStageMessage,
        progressPercent,
        totalTasks,
        completedTasks,
        failedTasks,
        runningTasks,
        pendingTasks,
        stageOverview,
    }
}

function buildBatchProgressPayload(batchTask: any, images: any[], fallbackTotal: number) {
    const statusDetail = normalizeBatchStatusDetail(batchTask, fallbackTotal)
    return {
        completed: statusDetail.completedTasks,
        total: statusDetail.totalTasks,
        images,
        stage: statusDetail.currentStage,
        stageLabel: statusDetail.currentStageLabel,
        stageMessage: statusDetail.currentStageMessage,
        progressPercent: statusDetail.progressPercent,
        running: statusDetail.runningTasks,
        pending: statusDetail.pendingTasks,
        failed: statusDetail.failedTasks,
        stageOverview: statusDetail.stageOverview,
    }
}

function buildBatchProcessingContent(batchTask: any, fallbackTotal: number) {
    const statusDetail = normalizeBatchStatusDetail(batchTask, fallbackTotal)
    return statusDetail.currentStageMessage
}

function normalizeModelName(value: any) {
    return String(value || '').trim().toLowerCase()
}

function isGeminiModel(model: any) {
    const modelName = normalizeModelName(model?.model_name || model)
    const displayName = normalizeModelName(model?.display_name)
    const provider = normalizeModelName(model?.provider)

    return modelName.includes('gemini') || displayName.includes('gemini') || provider.includes('google')
}

function pickPreferredDefaultModel(models: any[] = []) {
    if (!Array.isArray(models) || models.length === 0) return null

    const exactGemini = models.find((model) => normalizeModelName(model?.model_name) === DEFAULT_GEMINI_MODEL)
    if (exactGemini) return exactGemini

    const firstGemini = models.find((model) => isGeminiModel(model))
    if (firstGemini) return firstGemini

    return models[0]
}

export const useGeneratorStore = defineStore('generator', {
    state: () => ({
        model: DEFAULT_GEMINI_MODEL,
        width: 0,
        height: 0,
        aspectRatio: 'auto',
        batchSize: 1,
        isGenerating: false,
        prompt: '',
        attachments: [], // 附件文件列表
        currentSessionId: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        currentSessionTitle: '无标题会话',
        messages: [], // 消息列表
        selectedModelInfo: null, // 选中的模型详细信息
        style: 'photorealistic', // 图像风格
        quality: '2k', // 图像质量
        negativePrompt: '', // 负面提示词
        seed: '', // 随机种子
        presets: [] as Array<{id: string, name: string, params: any}>, // 参数预设列表
        isStartingNewConversation: false, // 是否正在开启新对话（防止重复调用）
        activePollingTasks: new Map(), // 活跃的轮询任务映射 {taskId: sessionId}
        sessionSavedToHistory: false, // 当前会话是否已保存到历史记录（防止重复添加）
        justCreatedSession: false, // 标记是否刚刚创建了新会话
        availableModels: [] as Array<{model_name: string, display_name?: string, provider?: string, model_type?: string}>, // 可用模型列表
        quotedMessage: null as {id: string, content: string} | null, // 引用的消息
        pendingAutoSend: false, // 标记是否需要自动发送
    }),
    getters: {
        // 动态计算宽高比
        computedAspectRatio() {
            const ratio = this.width / this.height
            // 允许一定的误差范围（0.01）
            if (Math.abs(ratio - 1) < 0.01) return '1:1'
            if (Math.abs(ratio - 4/3) < 0.01) return '4:3'
            if (Math.abs(ratio - 16/9) < 0.01) return '16:9'
            // 如果不是标准比例，返回自定义比例（简化后的比例）
            const gcd = function(a, b) {
                return b === 0 ? a : gcd(b, a % b)
            }
            const divisor = gcd(this.width, this.height)
            return `${this.width / divisor}:${this.height / divisor}`
        }
    },
    actions: {
        setAspectRatio(ratio) {
            this.aspectRatio = ratio
            if (ratio === '1:1') { this.width = 1024; this.height = 1024 }
            if (ratio === '4:3') { this.width = 1024; this.height = 768 }
            if (ratio === '16:9') { this.width = 1024; this.height = 576 }
        },

        setSelectedModel(modelName) {
            this.model = modelName
        },

        setSelectedModelInfo(modelInfo) {
            this.selectedModelInfo = modelInfo
        },

        applyPreferredDefaultModel() {
            const preferredModel = pickPreferredDefaultModel(this.availableModels)
            const fallbackName = preferredModel?.model_name || DEFAULT_GEMINI_MODEL
            const matchedModel = preferredModel || this.availableModels.find((model) =>
                normalizeModelName(model?.model_name) === normalizeModelName(fallbackName)
            )

            this.model = fallbackName
            this.selectedModelInfo = matchedModel || null
        },

        setPendingAutoSend(value) {
            this.pendingAutoSend = value
        },

        clearPendingAutoSend() {
            this.pendingAutoSend = false
        },

        setStyle(style) {
            this.style = style
        },

        setQuality(quality) {
            this.quality = quality
            // 按质量等级调整尺寸，保持当前宽高比
            const maxDimMap = { '720p': 1024, '2k': 2048, '4k': 4096 }
            const maxDim = maxDimMap[quality]
            if (maxDim) {
                const ratio = this.width / this.height
                if (ratio >= 1) {
                    this.width = maxDim
                    this.height = Math.round(maxDim / ratio)
                } else {
                    this.height = maxDim
                    this.width = Math.round(maxDim * ratio)
                }
            }
        },

        setBatchSize(size) {
            this.batchSize = size
        },

        setNegativePrompt(prompt) {
            this.negativePrompt = prompt
        },

        setSeed(seed) {
            this.seed = seed
        },

        resetParams() {
            this.width = 0
            this.height = 0
            this.aspectRatio = 'auto'
            this.batchSize = 1
            this.style = 'photorealistic'
            this.quality = '2k'
            this.negativePrompt = ''
            this.seed = ''
        },

        // ========== 参数预设管理 ==========
        savePreset(name: string) {
            const preset = {
                id: `preset_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                name: name,
                params: {
                    width: this.width,
                    height: this.height,
                    aspectRatio: this.aspectRatio,
                    batchSize: this.batchSize,
                    style: this.style,
                    quality: this.quality,
                    negativePrompt: this.negativePrompt,
                }
            }
            this.presets.push(preset)
            this.savePresetsToStorage()
            return preset
        },

        loadPreset(presetId: string) {
            const preset = this.presets.find(p => p.id === presetId)
            if (preset) {
                this.width = preset.params.width
                this.height = preset.params.height
                this.aspectRatio = preset.params.aspectRatio
                this.batchSize = preset.params.batchSize
                this.style = preset.params.style
                this.quality = preset.params.quality
                this.negativePrompt = preset.params.negativePrompt
                return true
            }
            return false
        },

        deletePreset(presetId: string) {
            const index = this.presets.findIndex(p => p.id === presetId)
            if (index > -1) {
                this.presets.splice(index, 1)
                this.savePresetsToStorage()
                return true
            }
            return false
        },

        savePresetsToStorage() {
            try {
                localStorage.setItem('generator_presets', JSON.stringify(this.presets))
            } catch (error) {
                console.error('保存预设失败:', error)
            }
        },

        loadPresetsFromStorage() {
            try {
                const saved = localStorage.getItem('generator_presets')
                if (saved) {
                    this.presets = JSON.parse(saved)
                }
            } catch (error) {
                console.error('加载预设失败:', error)
            }
        },

        initDefaultPresets() {
            // 如果没有预设，创建默认预设
            if (this.presets.length === 0) {
                const defaultPresets = [
                    {
                        id: 'preset_default_fast',
                        name: '快速生成',
                        params: {
                            width: 1024,
                            height: 1024,
                            aspectRatio: '1:1',
                            batchSize: 1,
                            style: 'photorealistic',
                            quality: '2k',
                            negativePrompt: ''
                        }
                    },
                    {
                        id: 'preset_default_quality',
                        name: '高质量',
                        params: {
                            width: 1024,
                            height: 1024,
                            aspectRatio: '1:1',
                            batchSize: 2,
                            style: 'photorealistic',
                            quality: '4k',
                            negativePrompt: '模糊, 低质量, 扭曲'
                        }
                    },
                    {
                        id: 'preset_default_artistic',
                        name: '艺术创作',
                        params: {
                            width: 1024,
                            height: 1024,
                            aspectRatio: '1:1',
                            batchSize: 4,
                            style: 'oil-painting',
                            quality: '4k',
                            negativePrompt: ''
                        }
                    },
                    {
                        id: 'preset_default_wide',
                        name: '宽屏壁纸',
                        params: {
                            width: 1920,
                            height: 1080,
                            aspectRatio: '16:9',
                            batchSize: 1,
                            style: 'photorealistic',
                            quality: '4k',
                            negativePrompt: '模糊, 低质量'
                        }
                    }
                ]
                this.presets = defaultPresets
                this.savePresetsToStorage()
            }
        },
        async generateImage(customPrompt?: string): Promise<{ success: boolean; taskId?: string; error?: string }> {
            let promptToUse = customPrompt || this.prompt

            // 如果有引用的消息，将其附加到提示词中
            if (this.quotedMessage && this.quotedMessage.content) {
                promptToUse = `引用：${this.quotedMessage.content}\n\n${promptToUse}`
                // 清除引用，避免重复添加
                this.quotedMessage = null
            }

            if (!promptToUse.trim()) {
                return { success: false, error: '请输入描述文字' }
            }

            this.isGenerating = true

            // 清除失败状态的消息，为重试做准备
            this.messages = this.messages.filter(msg => msg.status !== 'error')

            try {
                let response

                // 使用模拟模式或真实API
                if (isMockMode()) {
                    console.log('[模拟模式] 创建图像生成任务')
                    response = await mockGenerateImage({
                        prompt: promptToUse,
                        width: this.width,
                        height: this.height,
                        quality: this.quality,
                    })
                } else {
                    // 调用后端API生成图像
                    const params: any = {
                        prompt: promptToUse,
                        model_name: this.model,
                        width: this.width,
                        height: this.height,
                        quality: this.quality,
                        n: this.batchSize,
                        provider: undefined,
                    }

                    // 添加负面提示词
                    if (this.negativePrompt) {
                        params.negative_prompt = this.negativePrompt
                    }

                    // 添加随机种子
                    if (this.seed) {
                        params.seed = parseInt(this.seed)
                    }

                    console.log('[生成图像] 请求参数:', params)
                    response = await api.generateImage(params)
                    console.log('[生成图像] 响应数据:', response)
                }

                // 保存任务ID
                const taskId = response.task_id

                console.log('图像生成任务已创建:', taskId)

                // 检查是否是异步任务
                if (response.is_async) {
                    console.log('[异步任务] 任务已提交到异步队列:', taskId)
                    // 显示提示消息
                    this.messages.push({
                        id: `msg_${Date.now()}`,
                        type: 'system',
                        content: '异步任务已提交，请在"生成历史"中查看进度',
                        timestamp: new Date().toISOString()
                    })
                    this.isGenerating = false
                    return { success: true, taskId: taskId }
                }

                return {
                    success: true,
                    taskId: taskId
                }
            } catch (error: any) {
                console.error('图像生成失败:', error)

                // 如果是404错误，提示用户使用模拟模式
                if (error?.response?.status === 404) {
                    return {
                        success: false,
                        error: '后端API未正确配置。请在浏览器控制台输入: localStorage.setItem("mockMode", "true") 启用模拟模式进行测试'
                    }
                }

                return {
                    success: false,
                    error: error?.response?.data?.detail || error?.message || '生成失败，请稍后重试'
                }
            } finally {
                this.isGenerating = false
            }
        },
        // 添加附件
        addAttachment(file) {
            this.attachments.push(file)
        },
        // 移除附件
        removeAttachment(index) {
            this.attachments.splice(index, 1)
        },
        // 清空附件
        clearAttachments() {
            this.attachments = []
        },
        // 验证文件格式
        validateFileType(file) {
            const allowedTypes = [
                // PDF
                'application/pdf',
                // Word
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                // 图片
                'image/jpeg',
                'image/jpg',
                'image/png',
                'image/gif',
                'image/webp',
                'image/bmp',
                'image/svg+xml'
            ]
            const allowedExtensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
            
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
            return allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension)
        },
        // 添加消息到当前会话
        async addMessage(message) {
            this.messages.push(message)

            // 如果是第一条用户消息，设置标题并创建会话
            if (message.role === 'user' && this.messages.filter(m => m.role === 'user').length === 1) {
                this.setSessionTitle(message.content || '无标题会话')
                await this.createSessionOnServer()
                this.justCreatedSession = false // 会话已创建完成
            }

            // 只保存用户消息到服务器，assistant 临时消息不存
            if (message.role === 'user') {
                await this.saveMessageToServer(message)
            }
        },

        // 同步单个消息到服务器
        async saveMessageToServer(message) {
            // 跳过 assistant 的临时状态消息（处理中的占位消息）
            if (message.role === 'assistant' && message.status === 'processing') {
                return
            }

            try {
                // 使用新的保存消息接口
                const apiUrl = '/api/v1/history/save_message'
                const serializedFiles = Array.isArray(message.files)
                    ? message.files
                        .map(file => ({
                            name: file?.name || file?.filename || file?.original_filename,
                            original_filename: file?.original_filename || file?.name || file?.filename,
                            file_url: file?.file_url || file?.url,
                            file_id: file?.file_id,
                            file_size: file?.file_size || file?.size,
                            file_type: file?.file_type || file?.type,
                            category: file?.category || ((file?.type || file?.file_type || '').startsWith('image/') ? 'image' : 'document')
                        }))
                        .filter(file => file.name || file.file_url)
                    : undefined

                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: this.currentSessionId,
                        role: message.role,
                        content: String(message.content || ''),
                        model: this.model,
                        provider: 'unknown',
                        timestamp: new Date().toISOString(),
                        images: (message.images || []).map(img => typeof img === 'string' ? img : img.url).filter(Boolean),
                        files: serializedFiles && serializedFiles.length > 0 ? serializedFiles : undefined
                    })
                })

                if (response.ok) {
                    console.log('消息已保存到服务器:', message.role, message.content.substring(0, 20))

                    // 如果是新会话的第一条消息，已经在createSessionOnServer中刷新了历史记录
                    // 如果是已有会话的消息，这里不刷新，避免频繁更新
                } else {
                    console.warn('保存消息到服务器失败:', response.statusText)
                }
            } catch (error) {
                console.error('保存消息到服务器时出错:', error)
            }
        },

        // 在服务器上创建会话记录
        async createSessionOnServer() {
            if (this.sessionSavedToHistory) {
                return // 如果会话已经保存过，跳过
            }

            try {
                const apiUrl = '/api/v1/history/create_session'

                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: this.currentSessionId,
                        title: this.currentSessionTitle,
                        model: this.model,
                        provider: 'unknown'
                    })
                })

                if (response.ok) {
                    this.sessionSavedToHistory = true
                    console.log('创建对话会话成功:', this.currentSessionId)

                    // 通知历史记录刷新
                    const historyStore = useHistoryStore()
                    historyStore.refresh()
                } else {
                    console.warn('创建对话会话失败:', response.statusText)
                }
            } catch (error) {
                console.error('创建对话会话时出错:', error)
            }
        },

        // 更新消息内容
        updateMessage(messageId: number, updates: Partial<any>) {
            const message = this.messages.find(m => m.id === messageId)
            if (message) {
                Object.assign(message, updates)
            }
        },

        // 轮询任务状态
        async pollTaskStatus(taskId: string, messageId: number, maxAttempts: number = 900, interval: number = 2000): Promise<boolean> {
            const sessionWhenStarted = this.currentSessionId
            let attempts = 0

            // 注册轮询任务
            this.activePollingTasks.set(taskId, sessionWhenStarted)

            while (attempts < maxAttempts) {
                // 检查会话是否已切换
                if (this.currentSessionId !== sessionWhenStarted) {
                    console.log(`轮询停止: 会话已切换 (${taskId})`)
                    this.activePollingTasks.delete(taskId)
                    return false
                }

                try {
                    let task
                    if (isMockMode()) {
                        task = await mockGetTaskStatus(taskId)
                    } else {
                        task = await api.getTaskStatus(taskId)
                    }

                    // 再次检查会话是否已切换（在API调用之后）
                    if (this.currentSessionId !== sessionWhenStarted) {
                        console.log(`轮询停止: 会话已切换 (${taskId})`)
                        this.activePollingTasks.delete(taskId)
                        return false
                    }

                    console.log(`任务状态更新 [${taskId}]:`, task.status)

                    const taskStatus = String(task?.status || '').toLowerCase()

                    // 更新消息内容
                    if (ACTIVE_TASK_STATUSES.has(taskStatus)) {
                        this.updateMessage(messageId, {
                            content: getTaskStageMessage(task, `正在生成图像... (${attempts + 1}/${maxAttempts})`),
                            status: 'processing',
                            generationProgress: buildTaskProgressPayload(task, `正在生成图像... (${attempts + 1}/${maxAttempts})`)
                        })
                    } else if (taskStatus === 'completed') {
                        // 任务完成，显示结果
                        let images = []

                        console.log('原始task数据:', task)
                        console.log('task.images类型:', typeof task.images)
                        console.log('task.images值:', task.images)

                        // 优先使用task.images，如果不存在则尝试从task.result构建
                        if (task.images) {
                            // 如果是字符串，尝试解析为JSON
                            if (typeof task.images === 'string') {
                                try {
                                    images = JSON.parse(task.images)
                                    console.log('解析后的images:', images)
                                } catch (e) {
                                    console.error('解析images失败:', e)
                                }
                            } else if (Array.isArray(task.images)) {
                                images = task.images
                            }
                        } else if (task.result && Array.isArray(task.result)) {
                            images = task.result.map(img => ({
                                url: img.url,
                                alt: img.alt || '生成的图像'
                            }))
                        }

                        // Update billing status: frozen → deducted on completion
                        const completedBilling = task.billing ? { ...task.billing } : undefined
                        if (completedBilling && completedBilling.status === 'frozen') {
                            completedBilling.status = 'deducted'
                        }

                        this.updateMessage(messageId, {
                            content: '图像生成完成！',
                            status: 'completed',
                            images: images,
                            generationProgress: buildTaskProgressPayload(task, '图像生成完成！'),
                            ...(completedBilling ? { billing: completedBilling } : {})
                        })
                        console.log('任务完成，图片数据:', this.messages.find(m => m.id === messageId)?.images)

                        // 更新历史记录中的消息
                        if (this.sessionSavedToHistory) {
                            const historyStore = useHistoryStore()
                            historyStore.updateSession(this.currentSessionId, {
                                messages: this.messages,
                                imageCount: this.messages.reduce((count, msg) =>
                                    count + (msg.images?.length || 0), 0
                                )
                            })

                            // 同步完成的消息到服务器
                            const completedMessage = this.messages.find(m => m.id === messageId)
                            if (completedMessage) {
                                this.saveMessageToServer(completedMessage)
                            }

                            // 自动调用总结接口更新会话标题
                            this.summarizeSession()
                        }

                        this.activePollingTasks.delete(taskId)
                        return true
                    } else if (FAILED_TASK_STATUSES.has(taskStatus)) {
                        // 任务失败 — billing status: frozen → refunded
                        const failedBilling = task.billing ? { ...task.billing } : undefined
                        if (failedBilling && failedBilling.status === 'frozen') {
                            failedBilling.status = 'refunded'
                        }
                        this.updateMessage(messageId, {
                            content: `生成失败: ${task.error || '未知错误'}`,
                            status: 'error',
                            generationProgress: buildTaskProgressPayload(task, `生成失败: ${task.error || '未知错误'}`),
                            ...(failedBilling ? { billing: failedBilling } : {})
                        })
                        this.activePollingTasks.delete(taskId)
                        return false
                    }

                    // 等待一段时间后再次检查
                    await new Promise(resolve => setTimeout(resolve, interval))
                    attempts++
                } catch (error) {
                    console.error('轮询任务状态失败:', error)
                    // 检查会话是否已切换（在错误时）
                    if (this.currentSessionId !== sessionWhenStarted) {
                        console.log(`轮询停止: 会话已切换 (${taskId})`)
                        this.activePollingTasks.delete(taskId)
                        return false
                    }
                    attempts++
                    await new Promise(resolve => setTimeout(resolve, interval))
                }
            }

            // 超时
            if (this.currentSessionId === sessionWhenStarted) {
                const currentMessage = this.messages.find(m => m.id === messageId)
                this.updateMessage(messageId, {
                    content: '生成超时，请稍后手动查看任务状态',
                    status: 'timeout',
                    generationProgress: currentMessage?.generationProgress
                        ? {
                            ...currentMessage.generationProgress,
                            stageMessage: '生成超时，请稍后手动查看任务状态'
                        }
                        : buildInitialTaskProgressPayload({}, '生成超时，请稍后手动查看任务状态')
                })
            }
            this.activePollingTasks.delete(taskId)
            return false
        },

        // 批量生成图像
        async batchGenerateImages(prompts: string[]): Promise<{ success: boolean; batchId?: string; error?: string }> {
            if (!prompts || prompts.length === 0) {
                return { success: false, error: '请提供至少一个提示词' }
            }

            this.isGenerating = true

            try {
                let response

                // 使用模拟模式或真实API
                if (isMockMode()) {
                    console.log('[模拟模式] 创建批量生成任务')
                    // 模拟批量生成
                    response = {
                        batch_id: `batch_${Date.now()}`,
                        tasks: prompts.map((prompt, i) => ({
                            task_id: `task_${Date.now()}_${i}`,
                            status: 'pending',
                            params: { prompt }
                        }))
                    }
                } else {
                    // 调用真实的批量生成API
                    response = await api.batchGenerate({
                        prompts: prompts,
                        provider: undefined,
                        default_params: {
                            width: this.width,
                            height: this.height,
                            quality: this.quality
                        }
                    })
                }

                console.log('批量生成任务已创建:', response.batch_id)

                return {
                    success: true,
                    batchId: response.batch_id
                }
            } catch (error: any) {
                console.error('批量生成失败:', error)
                return {
                    success: false,
                    error: error?.response?.data?.detail || error?.message || '批量生成失败，请稍后重试'
                }
            } finally {
                this.isGenerating = false
            }
        },

        // 轮询批量任务状态
        async pollBatchStatus(batchId: string, messageId: number, totalCount: number, maxAttempts: number = 900, interval: number = 2000): Promise<boolean> {
            const sessionWhenStarted = this.currentSessionId
            let attempts = 0
            const results = []
            let completedCount = 0

            // 注册轮询任务
            this.activePollingTasks.set(batchId, sessionWhenStarted)

            while (attempts < maxAttempts) {
                // 检查会话是否已切换
                if (this.currentSessionId !== sessionWhenStarted) {
                    console.log(`批量轮询停止: 会话已切换 (${batchId})`)
                    this.activePollingTasks.delete(batchId)
                    return false
                }

                try {
                    let batchTask
                    if (isMockMode()) {
                        // 模拟批量任务进度
                        batchTask = {
                            batch_id: batchId,
                            tasks: results.map((r, i) => ({
                                task_id: `${batchId}_${i}`,
                                status: i < completedCount ? 'completed' : 'processing',
                                result: i < completedCount ? {
                                    images: [{
                                        url: `https://picsum.photos/1024/1024?random=${Date.now()}_${i}`
                                    }]
                                } : undefined
                            }))
                        }

                        // 模拟进度
                        if (attempts % 5 === 0 && completedCount < totalCount) {
                            completedCount++
                        }
                    } else {
                        batchTask = await api.getBatchTaskStatus(batchId)
                    }

                    // 再次检查会话是否已切换（在API调用之后）
                    if (this.currentSessionId !== sessionWhenStarted) {
                        console.log(`批量轮询停止: 会话已切换 (${batchId})`)
                        this.activePollingTasks.delete(batchId)
                        return false
                    }

                    console.log(`批量任务状态更新 [${batchId}]:`, completedCount, '/', totalCount)

                    // 收集结果
                    if (batchTask.tasks) {
                        batchTask.tasks.forEach((task, index) => {
                            let imageUrl = null

                            // 优先使用task.images，然后尝试从task.result获取
                            if (task.images && Array.isArray(task.images) && task.images.length > 0) {
                                imageUrl = task.images[0]?.url
                            } else if (task.result && Array.isArray(task.result) && task.result.length > 0) {
                                imageUrl = task.result[0]?.url
                            }

                            console.log(`任务 ${index}:`, task.status, imageUrl)
                            if (task.status === 'completed' && imageUrl) {
                                if (!results[index]) {
                                    results[index] = imageUrl
                                }
                            }
                        })
                    }

                    // 更新消息内容
                    const currentCompleted = results.filter(r => r).length
                    const batchProgress = buildBatchProgressPayload(batchTask, results, totalCount)
                    this.updateMessage(messageId, {
                        content: buildBatchProcessingContent(batchTask, totalCount),
                        status: 'processing',
                        batchProgress
                    })

                    // 检查是否全部完成
                    const batchStatus = String(batchTask?.status || '').toLowerCase()
                    if (currentCompleted >= totalCount || (TERMINAL_TASK_STATUSES.has(batchStatus) && currentCompleted > 0)) {
                        // 全部完成
                        const finalImages = results.map((url, i) => ({
                            url: url || `https://picsum.photos/1024/1024?random=${Date.now()}_${i}`,
                            alt: `生成图片 ${i + 1}`
                        }))
                        console.log('批量任务全部完成，图片数据:', finalImages)
                        this.updateMessage(messageId, {
                            content: `批量生成完成！共 ${finalImages.length} 张图片`,
                            status: 'completed',
                            images: finalImages,
                            batchProgress: buildBatchProgressPayload(batchTask, finalImages, totalCount)
                        })

                        // 更新历史记录中的消息
                        if (this.sessionSavedToHistory) {
                            const historyStore = useHistoryStore()
                            historyStore.updateSession(this.currentSessionId, {
                                messages: this.messages,
                                imageCount: this.messages.reduce((count, msg) =>
                                    count + (msg.images?.length || 0), 0
                                )
                            })

                            // 同步完成的消息到服务器
                            const completedMessage = this.messages.find(m => m.id === messageId)
                            if (completedMessage) {
                                this.saveMessageToServer(completedMessage)
                            }
                        }

                        this.activePollingTasks.delete(batchId)
                        return true
                    }

                    if (FAILED_TASK_STATUSES.has(batchStatus) && currentCompleted === 0) {
                        this.updateMessage(messageId, {
                            content: buildBatchProcessingContent(batchTask, totalCount),
                            status: 'error',
                            batchProgress,
                        })
                        this.activePollingTasks.delete(batchId)
                        return false
                    }

                    // 等待一段时间后再次检查
                    await new Promise(resolve => setTimeout(resolve, interval))
                    attempts++
                } catch (error) {
                    console.error('轮询批量任务状态失败:', error)
                    // 检查会话是否已切换（在错误时）
                    if (this.currentSessionId !== sessionWhenStarted) {
                        console.log(`批量轮询停止: 会话已切换 (${batchId})`)
                        this.activePollingTasks.delete(batchId)
                        return false
                    }
                    attempts++
                    await new Promise(resolve => setTimeout(resolve, interval))
                }
            }

            // 超时
            if (this.currentSessionId === sessionWhenStarted) {
                const currentMessage = this.messages.find(m => m.id === messageId)
                this.updateMessage(messageId, {
                    content: `批量生成超时，已完成 ${results.filter(r => r).length}/${totalCount}`,
                    status: 'timeout',
                    images: results.map((url, i) => ({
                        url: url || `https://via.placeholder.com/400x300?text=Image+${i+1}`,
                        alt: `图片 ${i + 1}`
                    })),
                    batchProgress: currentMessage?.batchProgress
                        ? {
                            ...currentMessage.batchProgress,
                            stageMessage: `轮询超时，已完成 ${results.filter(r => r).length}/${totalCount}`
                        }
                        : undefined
                })
            }
            this.activePollingTasks.delete(batchId)
            return false
        },
        // 增量轮询批量任务状态：每个子任务完成后立即更新图片列表
        async pollBatchStatusIncremental(batchId: string, messageId: number, totalCount: number, maxAttempts: number = 900, interval: number = 2000): Promise<boolean> {
            const sessionWhenStarted = this.currentSessionId
            let attempts = 0
            let mockCompletedCount = 0
            const completedTaskImages = new Map<string, any[]>()

            const normalizeImage = (image: any, taskIndex: number, imageIndex: number) => {
                if (!image) return null
                if (typeof image === 'string') {
                    return {
                        url: image,
                        alt: `生成图片 ${taskIndex + 1}-${imageIndex + 1}`
                    }
                }
                if (!image.url) return null
                return {
                    ...image,
                    alt: image.alt || `生成图片 ${taskIndex + 1}-${imageIndex + 1}`
                }
            }

            const extractTaskImages = (task: any, taskIndex: number) => {
                const rawImages: any[] = []

                if (Array.isArray(task?.images)) {
                    rawImages.push(...task.images)
                }

                if (Array.isArray(task?.result)) {
                    rawImages.push(...task.result)
                } else if (Array.isArray(task?.result?.images)) {
                    rawImages.push(...task.result.images)
                }

                const dedup = new Set<string>()
                const images: any[] = []
                rawImages.forEach((image, imageIndex) => {
                    const normalized = normalizeImage(image, taskIndex, imageIndex)
                    const url = normalized?.url
                    if (!url || dedup.has(url)) return
                    dedup.add(url)
                    images.push(normalized)
                })
                return images
            }

            const buildOrderedImages = (tasks: any[]) => {
                const sortedTasks = [...tasks].sort((a, b) => {
                    const taskIndexA = typeof a?.metadata?.task_index === 'number' ? a.metadata.task_index : Number.MAX_SAFE_INTEGER
                    const taskIndexB = typeof b?.metadata?.task_index === 'number' ? b.metadata.task_index : Number.MAX_SAFE_INTEGER
                    return taskIndexA - taskIndexB
                })

                const imageDedup = new Set<string>()
                const orderedImages: any[] = []

                sortedTasks.forEach((task, index) => {
                    const taskKey = task?.task_id || `${batchId}_${index}`
                    const taskImages = completedTaskImages.get(taskKey) || extractTaskImages(task, index)
                    taskImages.forEach((image) => {
                        const url = typeof image === 'string' ? image : image?.url
                        if (!url || imageDedup.has(url)) return
                        imageDedup.add(url)
                        orderedImages.push(image)
                    })
                })

                return orderedImages
            }

            this.activePollingTasks.set(batchId, sessionWhenStarted)

            while (attempts < maxAttempts) {
                if (this.currentSessionId !== sessionWhenStarted) {
                    console.log(`批量轮询停止: 会话已切换 (${batchId})`)
                    this.activePollingTasks.delete(batchId)
                    return false
                }

                try {
                    let batchTask
                    if (isMockMode()) {
                        if (attempts % 3 === 0 && mockCompletedCount < totalCount) {
                            mockCompletedCount++
                        }

                        batchTask = {
                            batch_id: batchId,
                            status: mockCompletedCount >= totalCount ? 'completed' : 'processing',
                            tasks: Array.from({ length: totalCount }, (_, i) => ({
                                task_id: `${batchId}_${i}`,
                                status: i < mockCompletedCount ? 'completed' : 'processing',
                                images: i < mockCompletedCount ? [{
                                    url: `https://picsum.photos/1024/1024?random=${Date.now()}_${i}`
                                }] : []
                            }))
                        }
                    } else {
                        batchTask = await api.getBatchTaskStatus(batchId)
                    }

                    if (this.currentSessionId !== sessionWhenStarted) {
                        console.log(`批量轮询停止: 会话已切换 (${batchId})`)
                        this.activePollingTasks.delete(batchId)
                        return false
                    }

                    const tasks = Array.isArray(batchTask?.tasks) ? batchTask.tasks : []
                    let completedTaskCount = 0
                    let failedTaskCount = 0
                    let terminalTaskCount = 0

                    tasks.forEach((task, index) => {
                        const taskStatus = String(task?.status || '').toLowerCase()
                        const taskKey = task?.task_id || `${batchId}_${index}`

                        if (taskStatus === 'completed') {
                            completedTaskCount++
                            terminalTaskCount++
                            const taskImages = extractTaskImages(task, index)
                            if (taskImages.length > 0) {
                                completedTaskImages.set(taskKey, taskImages)
                            }
                        } else if (['failed', 'error', 'cancelled', 'canceled'].includes(taskStatus)) {
                            failedTaskCount++
                            terminalTaskCount++
                        }
                    })

                    const progressTotal = totalCount || tasks.length || 1
                    const orderedImages = buildOrderedImages(tasks)
                    const batchProgress = buildBatchProgressPayload(batchTask, orderedImages, progressTotal)

                    this.updateMessage(messageId, {
                        content: buildBatchProcessingContent(batchTask, progressTotal),
                        status: 'processing',
                        images: orderedImages,
                        batchProgress
                    })

                    const batchStatus = String(batchTask?.status || '').toLowerCase()
                    const isBatchTerminal = TERMINAL_TASK_STATUSES.has(batchStatus)
                    const isAllTaskTerminal = totalCount > 0
                        ? terminalTaskCount >= totalCount
                        : (tasks.length > 0 && terminalTaskCount >= tasks.length)

                    if (isBatchTerminal || isAllTaskTerminal) {
                        const finalStatus = orderedImages.length > 0 ? 'completed' : 'error'
                        const finalContent = failedTaskCount > 0
                            ? `批量生成完成：成功 ${completedTaskCount}，失败 ${failedTaskCount}`
                            : `批量生成完成！共 ${completedTaskCount} 张图片`

                        this.updateMessage(messageId, {
                            content: finalContent,
                            status: finalStatus,
                            images: orderedImages,
                            batchProgress: buildBatchProgressPayload(batchTask, orderedImages, progressTotal),
                            ...(batchTask.billing ? { billing: batchTask.billing } : {})
                        })

                        if (this.sessionSavedToHistory) {
                            const historyStore = useHistoryStore()
                            historyStore.updateSession(this.currentSessionId, {
                                messages: this.messages,
                                imageCount: this.messages.reduce((count, msg) =>
                                    count + (msg.images?.length || 0), 0
                                )
                            })

                            const completedMessage = this.messages.find(m => m.id === messageId)
                            if (completedMessage) {
                                this.saveMessageToServer(completedMessage)
                            }
                        }

                        this.activePollingTasks.delete(batchId)
                        return orderedImages.length > 0
                    }

                    await new Promise(resolve => setTimeout(resolve, interval))
                    attempts++
                } catch (error) {
                    console.error('轮询批量任务状态失败:', error)
                    if (this.currentSessionId !== sessionWhenStarted) {
                        console.log(`批量轮询停止: 会话已切换 (${batchId})`)
                        this.activePollingTasks.delete(batchId)
                        return false
                    }
                    attempts++
                    await new Promise(resolve => setTimeout(resolve, interval))
                }
            }

            if (this.currentSessionId === sessionWhenStarted) {
                const timeoutImages = Array.from(completedTaskImages.values()).reduce((all, taskImages) => {
                    return all.concat(taskImages)
                }, [] as any[])
                const currentMessage = this.messages.find(m => m.id === messageId)

                this.updateMessage(messageId, {
                    content: `批量生成超时，已返回 ${timeoutImages.length} 张图片`,
                    status: 'timeout',
                    images: timeoutImages,
                    batchProgress: currentMessage?.batchProgress
                        ? {
                            ...currentMessage.batchProgress,
                            completed: Math.max(Number(currentMessage.batchProgress.completed || 0), timeoutImages.length),
                            images: timeoutImages,
                            stageMessage: `轮询超时，已返回 ${timeoutImages.length} 张图片`
                        }
                        : {
                            completed: timeoutImages.length,
                            total: totalCount || timeoutImages.length || 1,
                            images: timeoutImages,
                            stage: 'queued',
                            stageLabel: '轮询超时',
                            stageMessage: `轮询超时，已返回 ${timeoutImages.length} 张图片`,
                            progressPercent: normalizeProgressPercent(timeoutImages.length / Math.max(totalCount || timeoutImages.length || 1, 1)) || 0,
                            running: 0,
                            pending: Math.max((totalCount || timeoutImages.length || 1) - timeoutImages.length, 0),
                            failed: 0,
                            stageOverview: [],
                        }
                })
            }

            this.activePollingTasks.delete(batchId)
            return false
        },
        // 设置会话标题
        setSessionTitle(title) {
            if (title && title.trim()) {
                // 截取前8个字符作为标题
                this.currentSessionTitle = title.length > 8 ? title.substring(0, 8) : title
            } else {
                this.currentSessionTitle = '无标题会话'
            }
        },
        // 调用总结接口更新会话标题
        async summarizeSession() {
            if (!this.currentSessionId || !this.sessionSavedToHistory) return
            try {
                const response = await fetch(`/api/v1/history/${this.currentSessionId}/summary`, {
                    method: 'POST'
                })
                if (response.ok) {
                    const data = await response.json()
                    if (data.summary) {
                        const title = data.summary.length > 8 ? data.summary.substring(0, 8) : data.summary
                        this.currentSessionTitle = title
                        // 同步更新历史记录
                        const historyStore = useHistoryStore()
                        historyStore.updateSession(this.currentSessionId, { title })
                    }
                }
            } catch (error) {
                console.error('会话总结失败:', error)
            }
        },
        // 开启新对话
        async startNewConversation() {
            // 防止重复调用
            if (this.isStartingNewConversation) {
                console.warn('正在开启新对话，请勿重复点击')
                return
            }

            this.isStartingNewConversation = true

            try {
                // 清空消息列表
                this.messages = []

                // 清空输入框和附件
                this.prompt = ''
                this.clearAttachments()

                // 重置生成参数到默认值
                this.applyPreferredDefaultModel()
                this.width = 0
                this.height = 0
                this.aspectRatio = 'auto'
                this.batchSize = 1
                this.isGenerating = false

                // 生成新的会话ID和标题（在清空状态之后）
                this.currentSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
                this.currentSessionTitle = '无标题会话'
                this.sessionSavedToHistory = false // 重置历史记录标志
                this.justCreatedSession = true // 标记刚刚创建了新会话

                console.log('新对话已开启，会话ID:', this.currentSessionId)
                console.log('注意：实际的会话记录将在第一条消息发送时创建')
            } finally {
                // 确保标志位被重置
                this.isStartingNewConversation = false
            }
        },

        // 重试生成
        async retryGeneration(messageId: number): Promise<{ success: boolean; taskId?: string; batchId?: string; error?: string }> {
            const message = this.messages.find(m => m.id === messageId)
            if (!message) {
                return { success: false, error: '消息不存在' }
            }

            if (message.role !== 'assistant') {
                return { success: false, error: '只能重试AI助手的消息' }
            }

            try {
                // 重置消息状态
                message.status = 'processing'
                message.content = '正在重试生成...'

                // 获取之前的用户消息作为提示词
                const userMessages = this.messages.filter(m => m.role === 'user')
                if (userMessages.length === 0) {
                    return { success: false, error: '找不到用户消息' }
                }

                const lastUserMessage = userMessages[userMessages.length - 1]
                const prompt = lastUserMessage.content

                this.isGenerating = true

                const isTextModel = this.selectedModelInfo?.model_type !== '图像'

                // 文本模型走流式聊天
                if (isTextModel) {
                    const chatRequest = {
                        messages: this.messages
                            .filter(m => m.status !== 'error' && m.id !== messageId)
                            .map(m => ({ role: m.role, content: m.content })),
                        session_id: this.currentSessionId,
                        model: this.selectedModelInfo?.model_name || this.model,
                        model_type: 'chat',
                        stream: true,
                    }

                    return new Promise((resolve) => {
                        let fullContent = ''
                        api.assistantChatStream(chatRequest, {
                            onChunk(content) {
                                fullContent += content
                                this.updateMessage(messageId, { content: fullContent, status: 'processing' })
                            },
                            onDone: () => {
                                this.updateMessage(messageId, { content: fullContent || '(空回复)', status: 'completed' })
                                this.isGenerating = false
                                resolve({ success: true })
                            },
                            onError: (error) => {
                                message.status = 'error'
                                message.content = `重试失败: ${error}`
                                this.isGenerating = false
                                resolve({ success: false, error })
                            }
                        })
                    })
                }

                // 图像模型走统一助手接口
                const chatRequest = {
                    messages: this.messages
                        .filter(m => m.status !== 'error' && m.id !== messageId)
                        .map(m => ({ role: m.role, content: m.content })),
                    session_id: this.currentSessionId,
                    model: this.selectedModelInfo?.model_name || this.model,
                    model_type: 'image',
                    image_params: {
                        width: this.width,
                        height: this.height,
                        quality: this.quality,
                        n: this.batchSize,
                        negative_prompt: this.negativePrompt || undefined,
                        seed: this.seed ? parseInt(this.seed) : undefined,
                        model_name: this.selectedModelInfo?.model_name || this.model || undefined,
                        provider: this.selectedModelInfo?.provider || undefined
                    }
                }

                const response = await api.assistantChat(chatRequest)

                if (response.intent && response.intent.type) {
                    const intent = response.intent

                    if (intent.type === 'single_generate' && response.task_id) {
                        this.updateMessage(messageId, {
                            content: response.message.content,
                            taskId: response.task_id,
                            status: 'processing',
                            billing: response.metadata?.billing || undefined,
                            generationProgress: buildInitialTaskProgressPayload(response.metadata, response.message.content)
                        })
                        this.pollTaskStatus(response.task_id, messageId, 900, 2000)
                        return { success: true, taskId: response.task_id }

                    } else if (intent.type === 'batch_generate' && response.batch_id) {
                        const totalCount = response.metadata?.total_count || intent.parameters?.count || 4
                        this.updateMessage(messageId, {
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
                        this.pollBatchStatusIncremental(response.batch_id, messageId, totalCount, 900, 2000)
                        return { success: true, batchId: response.batch_id }

                    } else {
                        this.updateMessage(messageId, {
                            content: response.message.content,
                            status: 'completed'
                        })
                        return { success: true }
                    }
                } else {
                    this.updateMessage(messageId, {
                        content: response.message?.content || '处理完成',
                        status: 'completed'
                    })
                    return { success: true }
                }

            } catch (error) {
                message.status = 'error'
                message.content = `重试失败: ${error?.response?.data?.detail || error?.message || '未知错误'}`
                return { success: false, error: error?.message || '未知错误' }
            } finally {
                this.isGenerating = false
            }
        },

        // Fetch available models from API
        async fetchAvailableModels() {
            try {
                const response = await api.getModels()
                if (response && response.models) {
                    this.availableModels = response.models.map(model => ({
                        model_name: model.model_name,
                        display_name: model.display_name || model.model_name,
                        provider: model.provider || 'unknown',
                        model_type: model.model_type || 'image',
                        tags: typeof model.tags === 'string' ? model.tags.split(',').map(t => t.trim()) : (model.tags || []),
                        is_async: model.is_async || false
                    }))

                    const matchedCurrentModel = this.availableModels.find((model) =>
                        normalizeModelName(model.model_name) === normalizeModelName(this.model)
                    )

                    if (matchedCurrentModel) {
                        this.model = matchedCurrentModel.model_name
                        this.selectedModelInfo = matchedCurrentModel
                    } else {
                        this.applyPreferredDefaultModel()
                    }

                    console.log('Available models loaded:', this.availableModels.length)
                }
            } catch (error) {
                console.error('Failed to fetch available models:', error)
                this.availableModels = []
            }
        }
    }
})
