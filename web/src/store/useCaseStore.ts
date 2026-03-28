import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

// 案例类型定义
export interface Case {
  id: string
  title: string
  description?: string
  category: string
  tags?: string[]
  thumbnail_url?: string
  image_url?: string
  prompt: string
  negative_prompt?: string
  parameters?: Record<string, any>
  provider?: string
  model?: string
  is_published: boolean
  sort_order: number
  view_count: number
  use_count: number
  created_by?: string
  created_at: string
  updated_at: string
}

export const useCaseStore = defineStore('cases', () => {
  // 状态
  const cases = ref<Case[]>([])

  // 预设分类
  const presetCategories = [
    '电商',
    '广告',
    '动漫',
    '室内',
    'logo',
    '摄影',
    '插画',
    '其他'
  ]

  // 所有可用的分类（预设 + 从案例中提取的实际分类）
  const availableCategories = computed(() => {
    const usedCategories = new Set<string>()
    cases.value.forEach(c => {
      if (c.category) {
        usedCategories.add(c.category)
      }
    })
    // 合并预设分类和实际使用的分类
    return [...presetCategories, ...Array.from(usedCategories)]
  })

  const selectedCategory = ref<string | null>(null)
  const searchQuery = ref('')
  const loading = ref(false)
  const hasMore = ref(true)
  const currentPage = ref(0)
  const pageSize = ref(20)
  const totalCount = ref(0)

  // 计算属性
  const filteredCases = computed(() => {
    let result = cases.value

    // 按分类筛选
    if (selectedCategory.value) {
      result = result.filter(c => c.category === selectedCategory.value)
    }

    // 按关键词搜索
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(c =>
        c.title.toLowerCase().includes(query) ||
        c.description?.toLowerCase().includes(query) ||
        c.tags?.some(tag => tag.toLowerCase().includes(query))
      )
    }

    return result
  })

  // Actions
  async function fetchCases(page: number = 0, append: boolean = false) {
    if (loading.value) return

    loading.value = true

    try {
      const offset = page * pageSize.value
      const result = await api.getPublishedCases({
        category: selectedCategory.value || undefined,
        keyword: searchQuery.value || undefined,
        limit: pageSize.value,
        offset,
      })

      if (append) {
        cases.value = [...cases.value, ...result]
      } else {
        cases.value = result
      }

      currentPage.value = page
      hasMore.value = result.length === pageSize.value

      // 获取总数
      const countResult = await api.getPublishedCasesCount({
        category: selectedCategory.value || undefined,
        keyword: searchQuery.value || undefined,
      })
      totalCount.value = countResult.count
    } catch (error: any) {
      console.error('获取案例列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    if (!hasMore.value || loading.value) return
    await fetchCases(currentPage.value + 1, true)
  }

  async function refresh() {
    currentPage.value = 0
    await fetchCases(0, false)
  }

  function setCategory(category: string | null) {
    selectedCategory.value = category
    refresh()
  }

  function setSearch(query: string) {
    searchQuery.value = query
    refresh()
  }

  async function getCaseById(caseId: string): Promise<Case | null> {
    try {
      const result = await api.getCaseById(caseId)
      // 更新本地列表中的数据
      const index = cases.value.findIndex(c => c.id === caseId)
      if (index !== -1) {
        cases.value[index] = result
      }
      return result
    } catch (error: any) {
      console.error('获取案例详情失败:', error)
      return null
    }
  }

  async function useCaseTemplate(caseId: string): Promise<boolean> {
    try {
      await api.useCaseTemplate(caseId)

      // 更新本地使用次数
      const caseItem = cases.value.find(c => c.id === caseId)
      if (caseItem) {
        caseItem.use_count++
      }

      return true
    } catch (error: any) {
      console.error('使用案例模板失败:', error)
      return false
    }
  }

  async function copyCasePrompt(caseId: string): Promise<boolean> {
    const caseItem = cases.value.find(c => c.id === caseId)
    if (!caseItem) {
      console.error('案例不存在')
      return false
    }

    try {
      await navigator.clipboard.writeText(caseItem.prompt)
      return true
    } catch (error: any) {
      console.error('复制失败:', error)
      return false
    }
  }

  function resetFilters() {
    selectedCategory.value = null
    searchQuery.value = ''
    refresh()
  }

  // 初始化
  function initialize() {
    refresh()
  }

  return {
    // 状态
    cases,
    categories: availableCategories,
    selectedCategory,
    searchQuery,
    loading,
    hasMore,
    currentPage,
    pageSize,
    totalCount,

    // 计算属性
    filteredCases,

    // Actions
    fetchCases,
    loadMore,
    refresh,
    setCategory,
    setSearch,
    getCaseById,
    useCaseTemplate,
    copyCasePrompt,
    resetFilters,
    initialize,
  }
})
