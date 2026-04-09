const SECTION_MARKERS = [
  'Final grounded generation brief:',
  'Latest user request:',
]

const LEADING_LANGUAGE_PATTERN = /^(中文|英文|english)\b[:：]?\s*/i

const NOISE_LINE_PATTERNS = [
  /^system instructions?:/i,
  /^recent conversation context:/i,
  /^latest user request:/i,
  /^final grounded generation brief:/i,
  /^latest request:/i,
  /^final image prompt:/i,
  /^grounding content extracted from uploaded files/i,
  /^use the uploaded image/i,
  /^\[attachment \d+\]/i,
  /^\(no ocr\/text excerpt was extracted\.\)$/i,
  /^type\s*:/i,
  /^style\s*:/i,
  /^this is the .*image\.?$/i,
  /^这是第.*张$/i,
  /^类型[:：]/,
  /^风格[:：]/,
  /^尺寸[:：]/,
  /^模型[:：]/,
  /^assistant:/i,
  /^user:/i,
  /^gemini[\w.-]*$/i,
  /^grok[\w.-]*$/i,
  /^图像生成完成[！!。]?$/,
  /^生成失败[:：]?.*$/,
  /^尝试.*次后失败.*$/,
]

const INLINE_NOISE_PATTERNS = [
  /图像生成完成[！!。]?/g,
  /生成失败[:：]?/g,
  /尝试\s*\d*\s*次后失败[:：]?/g,
  /任务创建失败[:：]?/g,
  /任务处理中[！!。]?/g,
  /处理中[.。！!]*/g,
]

const PROMPT_STARTER_PATTERN = /\s+(?=(帮我|请|根据|生成|画|制作|设计|创建|帮忙|给我|把|将|create\b|generate\b|draw\b|make\b))/gi

function normalizePrompt(prompt: string) {
  return String(prompt || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim()
}

function cleanLine(line: string) {
  let value = line.trim()
  value = value.replace(/^(user|assistant)\s*:\s*/i, '').trim()
  if (!value) return ''
  if (NOISE_LINE_PATTERNS.some((pattern) => pattern.test(value))) return ''
  return value
}

function stripInlineNoise(text: string) {
  let cleaned = text
  for (const pattern of INLINE_NOISE_PATTERNS) {
    cleaned = cleaned.replace(pattern, '\n')
  }
  return cleaned
}

function splitInlinePromptCandidates(prompt: string) {
  const languageMatch = normalizePrompt(prompt).match(LEADING_LANGUAGE_PATTERN)
  const leadingLanguage = languageMatch?.[1]?.trim() || ''

  let cleaned = normalizePrompt(prompt)
  cleaned = stripInlineNoise(cleaned)
  cleaned = cleaned.replace(/\s+/g, ' ').trim()
  cleaned = cleaned.replace(PROMPT_STARTER_PATTERN, '\n')

  const segments = cleaned
    .split(/\n+/)
    .map((segment) => cleanLine(segment))
    .filter(Boolean)

  if (segments.length === 0) {
    return { segments: [], leadingLanguage }
  }

  return { segments, leadingLanguage }
}

function extractMarkedSection(prompt: string) {
  const normalized = normalizePrompt(prompt)
  const lower = normalized.toLowerCase()

  for (const marker of SECTION_MARKERS) {
    const markerLower = marker.toLowerCase()
    const index = lower.lastIndexOf(markerLower)
    if (index === -1) continue

    const section = normalized.slice(index + marker.length).trim()
    if (!section) continue

    const lines = section
      .split('\n')
      .map(cleanLine)
      .filter(Boolean)

    if (lines.length > 0) {
      return lines.join('\n')
    }
  }

  return ''
}

export function extractDisplayPrompt(prompt?: string) {
  if (!prompt) return ''

  const markedSection = extractMarkedSection(prompt)
  if (markedSection) return markedSection

  const { segments, leadingLanguage } = splitInlinePromptCandidates(prompt)
  if (segments.length > 1) {
    let lastSegment = segments[segments.length - 1]
    if (leadingLanguage && !lastSegment.toLowerCase().startsWith(leadingLanguage.toLowerCase())) {
      lastSegment = `${leadingLanguage} ${lastSegment}`.trim()
    }
    return lastSegment
  }

  let cleaned = normalizePrompt(prompt)
  cleaned = cleaned.replace(/System instructions?:[\s\S]*?(?=\n\n|$)/gi, '')
  cleaned = cleaned.replace(/Recent conversation context:[\s\S]*?(?=\n\n(?:Latest user request:|Final grounded generation brief:)|$)/gi, '')
  cleaned = cleaned.replace(/gemini[\w.-]*\s*\n\s*System[\s\S]*?(?=\n\n[^a-zA-Z]|$)/gi, '')

  const blocks = cleaned
    .split(/\n{2,}/)
    .map((block) =>
      block
        .split('\n')
        .map(cleanLine)
        .filter(Boolean)
        .join('\n')
        .trim()
    )
    .filter(Boolean)

  if (blocks.length > 0) {
    return blocks[blocks.length - 1]
  }

  if (segments.length > 0) {
    let lastSegment = segments[segments.length - 1]
    if (leadingLanguage && !lastSegment.toLowerCase().startsWith(leadingLanguage.toLowerCase())) {
      lastSegment = `${leadingLanguage} ${lastSegment}`.trim()
    }
    return lastSegment
  }

  const lines = normalizePrompt(prompt)
    .split('\n')
    .map(cleanLine)
    .filter(Boolean)

  return lines.length > 0 ? lines[lines.length - 1] : ''
}

export function displayPromptOrFallback(prompt?: string, fallback = '无提示词') {
  return extractDisplayPrompt(prompt) || fallback
}
