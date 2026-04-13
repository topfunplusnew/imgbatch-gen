export const CASE_IMAGE_PLACEHOLDER = '/photo/template-placeholder.svg'
const ENV_API_ENDPOINT = String(import.meta.env.VITE_API_BASE_URL || '').trim()
const FORCE_SAME_ORIGIN_API = !import.meta.env.DEV && !ENV_API_ENDPOINT

type StoredApiConfig = {
  apiEndpoint?: string
}

function isLocalHostname(hostname: string): boolean {
  return ['localhost', '127.0.0.1', '0.0.0.0', '::1'].includes(hostname)
}

function isInternalServiceHostname(hostname: string): boolean {
  if (!hostname) {
    return false
  }

  const normalizedHost = hostname.trim().toLowerCase()
  if (!normalizedHost) {
    return false
  }

  if (isLocalHostname(normalizedHost)) {
    return true
  }

  return ['minio', 'backend', 'frontend', 'nginx'].includes(normalizedHost)
}

function getCurrentOrigin(): string {
  if (typeof window === 'undefined') {
    return ''
  }

  return window.location.origin
}

function getStoredApiEndpoint(): string {
  if (typeof window === 'undefined') {
    return ''
  }

  if (FORCE_SAME_ORIGIN_API) {
    return ''
  }

  try {
    const raw = window.localStorage.getItem('apiConfig')
    if (!raw) return ''

    const config = JSON.parse(raw) as StoredApiConfig
    return typeof config.apiEndpoint === 'string' ? config.apiEndpoint.trim() : ''
  } catch (error) {
    console.warn('Failed to parse stored api config for image fallback:', error)
    return ''
  }
}

function normalizeBaseOrigin(baseUrl: string): string {
  if (!baseUrl) {
    return ''
  }

  try {
    const currentOrigin = getCurrentOrigin()
    const currentHostname = currentOrigin ? new URL(currentOrigin).hostname : ''
    const parsedUrl = new URL(baseUrl, currentOrigin || undefined)

    if (currentHostname && !isLocalHostname(currentHostname) && isLocalHostname(parsedUrl.hostname)) {
      return ''
    }

    return parsedUrl.origin
  } catch {
    return ''
  }
}

function getPreferredAssetOrigin(): string {
  const envOrigin = normalizeBaseOrigin(import.meta.env.VITE_API_BASE_URL || '')
  if (envOrigin) {
    return envOrigin
  }

  const storedOrigin = normalizeBaseOrigin(getStoredApiEndpoint())
  if (storedOrigin) {
    return storedOrigin
  }

  return getCurrentOrigin()
}

function isBackendAssetPath(pathname: string): boolean {
  return /^\/(storage|images|api\/v1\/files)\//.test(pathname)
}

export function normalizeImageSrc(candidate?: string | null): string {
  if (typeof candidate !== 'string') {
    return ''
  }

  const value = candidate.trim()
  if (!value) {
    return ''
  }

  if (value.startsWith('data:') || value.startsWith('blob:')) {
    return value
  }

  const preferredOrigin = getPreferredAssetOrigin()

  if (value.startsWith('//')) {
    const protocol = typeof window !== 'undefined' ? window.location.protocol : 'https:'
    return `${protocol}${value}`
  }

  if (/^https?:\/\//i.test(value)) {
    try {
      const parsedUrl = new URL(value)

      if (
        preferredOrigin &&
        isBackendAssetPath(parsedUrl.pathname) &&
        isInternalServiceHostname(parsedUrl.hostname)
      ) {
        return new URL(`${parsedUrl.pathname}${parsedUrl.search}${parsedUrl.hash}`, preferredOrigin).toString()
      }

      return parsedUrl.toString()
    } catch {
      return value
    }
  }

  const normalizedPath = value.startsWith('/')
    ? value
    : isBackendAssetPath(`/${value}`) ? `/${value}` : value

  if (preferredOrigin && isBackendAssetPath(normalizedPath)) {
    return new URL(normalizedPath, preferredOrigin).toString()
  }

  return normalizedPath
}

export function resolveImageSrcCandidates(...candidates: Array<string | null | undefined>): string[] {
  const resolvedCandidates = candidates
    .map((candidate) => normalizeImageSrc(candidate))
    .filter((candidate, index, list) => candidate && list.indexOf(candidate) === index)

  return resolvedCandidates.length > 0 ? resolvedCandidates : [CASE_IMAGE_PLACEHOLDER]
}

export function resolveImageSrc(...candidates: Array<string | null | undefined>): string {
  return resolveImageSrcCandidates(...candidates)[0] || CASE_IMAGE_PLACEHOLDER
}

export function handleImageFallback(event: Event, nextSrc?: string | null): void {
  const target = event.target as HTMLImageElement | null

  if (!target) return

  const fallbackSrc = (nextSrc || target.dataset.fallbackSrc || '').trim()
  const currentSrc = target.currentSrc || target.src || ''

  if (fallbackSrc && fallbackSrc !== currentSrc && fallbackSrc !== CASE_IMAGE_PLACEHOLDER) {
    target.dataset.fallbackSrc = ''
    target.src = fallbackSrc
    return
  }

  target.onerror = null
  target.src = CASE_IMAGE_PLACEHOLDER
}
