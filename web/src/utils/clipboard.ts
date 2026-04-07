/**
 * 兼容性复制文本到剪贴板
 * navigator.clipboard.writeText 需要 HTTPS 或 localhost，
 * 在 HTTP 环境下使用 execCommand('copy') 作为 fallback。
 */
export async function copyText(text: string): Promise<boolean> {
  // 优先使用现代 API
  if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      // 可能因权限或非安全上下文失败，走 fallback
    }
  }

  // Fallback: 创建隐藏 textarea 用 execCommand
  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    textarea.style.top = '-9999px'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.focus()
    textarea.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    return ok
  } catch {
    return false
  }
}
