export const DEFAULT_IMAGE_MODEL = 'gemini-3.1-flash-image-preview'

export const ALLOWED_IMAGE_MODELS = [
  'gemini-3.1-flash-image-preview',
  'gemini-3-pro-image-preview',
  'gemini-2.5-flash-image',
  'gemini-2.5-flash-image-preview',
  'grok-imagine-image-pro',
]

const IMAGE_TAGS = new Set(['image', '生图', '图像', '绘图', 'drawing', '绘画'])
const ALLOWED_IMAGE_MODEL_SET = new Set(ALLOWED_IMAGE_MODELS.map((name) => normalizeModelName(name)))

export function normalizeModelName(value: any) {
  return String(value || '').trim().toLowerCase()
}

function normalizeModelType(value: any) {
  return String(value || '').trim().toLowerCase()
}

function getModelTags(model: any): string[] {
  const tags = model?.tags || []
  if (Array.isArray(tags)) {
    return tags.map((tag) => String(tag || '').trim().toLowerCase()).filter(Boolean)
  }
  if (typeof tags === 'string') {
    return tags.split(',').map((tag) => tag.trim().toLowerCase()).filter(Boolean)
  }
  return []
}

export function isImageModel(model: any) {
  const modelName = normalizeModelName(model?.model_name || model?.name || model)
  const modelType = normalizeModelType(model?.model_type)
  const tags = getModelTags(model)

  if (modelType === '图像' || modelType.includes('image')) return true
  if (tags.some((tag) => IMAGE_TAGS.has(tag))) return true

  return modelName.includes('image')
}

export function isAllowedImageModelName(value: any) {
  return ALLOWED_IMAGE_MODEL_SET.has(normalizeModelName(value))
}

export function isSelectableImageModel(model: any) {
  return isImageModel(model) && isAllowedImageModelName(model?.model_name || model?.name || model)
}

export function isSelectableFrontendModel(model: any) {
  if (!model) return false
  if (!isImageModel(model)) return true
  return isSelectableImageModel(model)
}

export function filterSelectableFrontendModels(models: any[] = []) {
  return (Array.isArray(models) ? models : []).filter((model) => isSelectableFrontendModel(model))
}

export function filterSelectableImageModels(models: any[] = []) {
  return (Array.isArray(models) ? models : []).filter((model) => isSelectableImageModel(model))
}

export function pickPreferredFrontendModel(models: any[] = []) {
  const selectableModels = filterSelectableFrontendModels(models)
  if (selectableModels.length === 0) return null

  const exactDefault = selectableModels.find(
    (model) => normalizeModelName(model?.model_name) === DEFAULT_IMAGE_MODEL
  )
  if (exactDefault) return exactDefault

  const firstAllowedImage = selectableModels.find((model) => isSelectableImageModel(model))
  if (firstAllowedImage) return firstAllowedImage

  return selectableModels[0]
}
