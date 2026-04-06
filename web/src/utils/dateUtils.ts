/**
 * 统一日期解析 - 后端返回UTC时间不带Z后缀，需要补上
 * 所有从后端API获取的时间字符串，都应通过此函数解析
 */
export function parseUTCDate(dateStr: string | null | undefined): Date {
  if (!dateStr) return new Date(0)

  let normalized = dateStr
  // 如果是ISO格式但没有时区标识，当作UTC处理（加Z）
  if (
    typeof dateStr === 'string' &&
    !dateStr.endsWith('Z') &&
    !dateStr.includes('+') &&
    !/[+-]\d{2}:\d{2}$/.test(dateStr)
  ) {
    normalized = dateStr.replace(' ', 'T') + 'Z'
  }

  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? new Date(0) : date
}
