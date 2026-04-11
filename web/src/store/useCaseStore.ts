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
  const categories = ref<string[]>([])

  // 所有可用的分类（后端返回 + 从已加载案例中补齐）
  const availableCategories = computed(() => {
    const usedCategories = new Set<string>(categories.value.filter(Boolean))
    cases.value.forEach(c => {
      if (c.category) {
        usedCategories.add(c.category)
      }
    })
    return Array.from(usedCategories)
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
  async function fetchCategories() {
    try {
      const result = await api.getCaseCategories()
      categories.value = (result.categories || [])
        .map((item) => item?.value || item?.label)
        .filter(Boolean)
    } catch (error: any) {
      console.error('获取案例分类失败:', error)
      categories.value = Array.from(new Set(cases.value.map((item) => item.category).filter(Boolean)))
    }
  }

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

    const { copyText } = await import('@/utils/clipboard')
    return await copyText(caseItem.prompt)
  }

  function resetFilters() {
    selectedCategory.value = null
    searchQuery.value = ''
    refresh()
  }

  // 初始化
  function initialize() {
    fetchCategories()
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
    fetchCategories,
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
