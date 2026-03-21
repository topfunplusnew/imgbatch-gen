import { defineStore } from 'pinia'

export type PageType = 'agent' | 'login' | 'user-center' | 'admin'
export type UserCenterTab = 'account' | 'balance' | 'orders' | 'generations' | 'contact' | 'notifications'

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

export const useAppStore = defineStore('app', {
  state: () => ({
    currentPage: 'agent' as PageType,
    selectedCase: null as Case | null,
    selectedCreation: null as any | null,
    showCreationRecords: false,
    showTemplateDrawer: false,
    showProfileModal: false,
    userCenterTab: 'account' as UserCenterTab, // 新增：用户中心当前标签页
  }),
  actions: {
    setCurrentPage(page: PageType, tab?: UserCenterTab) {
      this.currentPage = page
      // 如果切换到用户中心，可以指定默认标签页
      if (page === 'user-center' && tab) {
        this.userCenterTab = tab
      }
    },
    setUserCenterTab(tab: UserCenterTab) {
      this.userCenterTab = tab
    },
    setSelectedCase(caseData: Case | null) {
      console.log('[AppStore] setSelectedCase called with:', caseData)
      this.selectedCase = caseData
      this.selectedCreation = null
    },
    setSelectedCreation(creationData: any | null) {
      console.log('[AppStore] setSelectedCreation called with:', creationData)
      this.selectedCreation = creationData
      this.selectedCase = null
    },
    clearSelectedCase() {
      console.log('[AppStore] clearSelectedCase called')
      this.selectedCase = null
      this.selectedCreation = null
    },
    toggleCreationRecords() {
      this.showCreationRecords = !this.showCreationRecords
      // 关闭其他面板
      if (this.showCreationRecords) {
        this.selectedCase = null
        this.selectedCreation = null
      }
    },
    closeCreationRecords() {
      this.showCreationRecords = false
    },
    toggleTemplateDrawer() {
      this.showTemplateDrawer = !this.showTemplateDrawer
      // 关闭其他面板
      if (this.showTemplateDrawer) {
        this.selectedCase = null
        this.selectedCreation = null
      }
    },
    closeTemplateDrawer() {
      this.showTemplateDrawer = false
    },
  },
})

