const CASE_PLACEHOLDER_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120" role="img" aria-label="No image available">
  <rect width="160" height="120" rx="16" fill="#f3f4f6" />
  <rect x="24" y="24" width="112" height="72" rx="12" fill="#e5e7eb" stroke="#cbd5e1" stroke-width="2" />
  <circle cx="54" cy="50" r="9" fill="#cbd5e1" />
  <path d="M42 84l21-20 14 12 20-24 21 32H42z" fill="#94a3b8" />
  <text x="80" y="104" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#64748b">No Image</text>
</svg>
`.trim()

export const CASE_IMAGE_PLACEHOLDER = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(CASE_PLACEHOLDER_SVG)}`

type StoredApiConfig = {
  apiEndpoint?: string
}

function isLocalHostname(hostname: string): boolean {
  return ['localhost', '127.0.0.1', '0.0.0.0', '::1'].includes(hostname)
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
  return /^\/(storage|api\/v1\/files)\//.test(pathname)
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
        isLocalHostname(parsedUrl.hostname)
      ) {
        const preferredUrl = new URL(preferredOrigin)
        if (!isLocalHostname(preferredUrl.hostname)) {
          return new URL(`${parsedUrl.pathname}${parsedUrl.search}${parsedUrl.hash}`, preferredOrigin).toString()
        }
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
