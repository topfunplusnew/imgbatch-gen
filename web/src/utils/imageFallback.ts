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

export function resolveImageSrc(...candidates: Array<string | null | undefined>): string {
  const validCandidate = candidates.find((candidate) => {
    return typeof candidate === 'string' && candidate.trim().length > 0
  })

  return validCandidate?.trim() || CASE_IMAGE_PLACEHOLDER
}

export function handleImageFallback(event: Event): void {
  const target = event.target as HTMLImageElement | null

  if (!target) return

  target.onerror = null
  target.src = CASE_IMAGE_PLACEHOLDER
}
