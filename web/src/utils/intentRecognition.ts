/**
 * 意图识别模块
 * 分析用户输入，识别是否需要批量生成，并提取相关参数
 */

import { api } from '@/services/api'

export interface Intent {
  type: 'single' | 'batch' | 'unknown'
  confidence: number
  batchCount?: number
  styles?: string[]
  subjects?: string[]
  reasoning?: string
}

export interface BatchGenerateParams {
  prompts: string[]
  count: number
  styles?: string[]
}

/**
 * 调用LLM分析用户意图
 * 注意：这个功能需要后端支持，暂时使用规则识别
 */
export async function recognizeIntent(userInput: string): Promise<Intent> {
  // 规则识别（简化版）
  const input = userInput.toLowerCase()

  // 批量生成关键词
  const batchKeywords = [
    '批量', '多张', '多个', '几张', '一组', '一套',
    'batch', 'multiple', 'several', 'generate.*\\d+'
  ]

  // 数字模式：生成3张、5个等
  const numberPattern = /生成(\d+)[张个幅组]/g
  const numberMatch = [...input.matchAll(numberPattern)]

  let batchCount = 0
  let isBatch = false

  // 检查数字模式
  if (numberMatch.length > 0) {
    batchCount = parseInt(numberMatch[0][1])
    isBatch = batchCount > 1
  }

  // 检查批量关键词
  for (const keyword of batchKeywords) {
    if (input.includes(keyword)) {
      isBatch = true
      if (batchCount === 0) {
        // 默认批量数量
        batchCount = 4
      }
      break
    }
  }

  // 风格识别
  const styles = extractStyles(userInput)

  // 主题识别
  const subjects = extractSubjects(userInput)

  if (isBatch) {
    return {
      type: 'batch',
      confidence: 0.8,
      batchCount: Math.min(batchCount, 10), // 最多10张
      styles,
      subjects,
      reasoning: `识别到批量生成需求，数量：${batchCount}`
    }
  }

  // 默认单图生成
  return {
    type: 'single',
    confidence: 0.7,
    styles,
    subjects,
    reasoning: '单图生成'
  }
}

/**
 * 提取风格关键词
 */
function extractStyles(input: string): string[] {
  const styleKeywords = {
    '卡通': ['卡通', '动漫', '二次元', 'cartoon', 'anime'],
    '写实': ['写实', '照片', '真实', 'realistic', 'photorealistic'],
    '油画': ['油画', 'oil painting', 'artistic'],
    '水彩': ['水彩', 'watercolor'],
    '素描': ['素描', 'sketch'],
    '赛博朋克': ['赛博朋克', 'cyberpunk'],
    '古风': ['古风', '中国风', 'chinese'],
    '简约': ['简约', '极简', 'minimalist', 'simple'],
    '抽象': ['抽象', 'abstract'],
  }

  const detectedStyles: string[] = []
  const lowerInput = input.toLowerCase()

  for (const [style, keywords] of Object.entries(styleKeywords)) {
    for (const keyword of keywords) {
      if (lowerInput.includes(keyword.toLowerCase())) {
        detectedStyles.push(style)
        break
      }
    }
  }

  return detectedStyles
}

/**
 * 提取主体关键词
 */
function extractSubjects(input: string): string[] {
  const subjectPatterns = [
    /猫|狗|宠物|动物/g,
    /人|人物|肖像/g,
    /风景|景色|山水/g,
    /城市|建筑|街道/g,
    /花|植物|树木/g,
    /车|汽车|交通工具/g
  ]

  const subjects: string[] = []

  for (const pattern of subjectPatterns) {
    const matches = input.match(pattern)
    if (matches) {
      subjects.push(...matches)
    }
  }

  return [...new Set(subjects)] // 去重
}

/**
 * 根据意图生成批量提示词
 */
export async function generateBatchPrompts(
  originalPrompt: string,
  intent: Intent
): Promise<BatchGenerateParams> {
  if (intent.type !== 'batch' || !intent.batchCount) {
    return {
      prompts: [originalPrompt],
      count: 1
    }
  }

  const prompts: string[] = []
  const basePrompt = originalPrompt

  // 生成不同风格的提示词
  if (intent.styles && intent.styles.length > 0) {
    // 使用识别到的风格
    for (let i = 0; i < intent.batchCount; i++) {
      const style = intent.styles[i % intent.styles.length]
      prompts.push(`${basePrompt}，${style}风格`)
    }
  } else {
    // 使用默认风格变化
    const defaultStyles = ['写实风格', '艺术风格', '简约风格', '创意风格']
    for (let i = 0; i < intent.batchCount; i++) {
      const style = defaultStyles[i % defaultStyles.length]
      prompts.push(`${basePrompt}，${style}`)
    }
  }

  return {
    prompts,
    count: intent.batchCount,
    styles: intent.styles
  }
}

/**
 * 高级意图识别（使用LLM）
 * 这个功能需要后端支持
 */
export async function recognizeIntentWithLLM(userInput: string): Promise<Intent> {
  try {
    // TODO: 调用后端的LLM接口进行意图识别
    // 目前先使用规则识别
    return await recognizeIntent(userInput)
  } catch (error) {
    console.error('LLM意图识别失败，使用规则识别:', error)
    return await recognizeIntent(userInput)
  }
}
