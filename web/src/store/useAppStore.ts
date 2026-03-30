import { defineStore } from 'pinia'

export type PageType = 'agent' | 'login' | 'user-center' | 'admin'
export type UserCenterTab = 'account' | 'balance' | 'orders' | 'generations' | 'contact' | 'notifications'
export type ViewType = 'chat' | 'landing' | 'templates'

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
    authRedirectNotice: null as { title: string; message: string } | null,
    selectedCase: null as Case | null,
    selectedCreation: null as any | null,
    showCreationRecords: false,
    showTemplateDrawer: false,
    showProfileModal: false,
    userCenterTab: 'account' as UserCenterTab, // 新增：用户中心当前标签页
    // View state for navigation
    currentView: 'landing' as ViewType,  // 'chat' | 'landing' | 'templates'
    selectedMenuItem: 'generate' as string,  // Current selected menu item
  }),
  actions: {
    setCurrentPage(page: PageType, tab?: UserCenterTab) {
      this.currentPage = page
      if (page !== 'login') {
        this.authRedirectNotice = null
      }
      // 如果切换到用户中心，可以指定默认标签页
      if (page === 'user-center' && tab) {
        this.userCenterTab = tab
      }
    },
    setAuthRedirectNotice(notice: { title: string; message: string } | null) {
      this.authRedirectNotice = notice
    },
    clearAuthRedirectNotice() {
      this.authRedirectNotice = null
    },
    goToLogin(preserveNotice: boolean = false) {
      if (!preserveNotice) {
        this.authRedirectNotice = null
      }
      this.currentPage = 'login'
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
      // Only clear other panels when opening the drawer
      // Don't clear selectedCase as it may be used to show details
      if (this.showTemplateDrawer) {
        this.selectedCreation = null
      }
    },
    closeTemplateDrawer() {
      this.showTemplateDrawer = false
    },
    // View state management
    setCurrentView(view: ViewType) {
      this.currentView = view
      // Update menu item based on view
      if (view === 'landing') {
        this.selectedMenuItem = 'landing'
      } else if (view === 'chat') {
        this.selectedMenuItem = 'generate'
      } else if (view === 'templates') {
        this.selectedMenuItem = 'templates'
      }
    },
    setSelectedMenuItem(item: string) {
      this.selectedMenuItem = item
      // Switch view based on menu item
      if (item === 'landing') {
        this.currentView = 'landing'
      } else if (item === 'generate') {
        this.currentView = 'chat'
      } else if (item === 'templates') {
        this.currentView = 'templates'
      } else if (item === 'settings') {
        this.showProfileModal = true
      }
    },
  },
})
