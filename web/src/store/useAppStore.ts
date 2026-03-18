import { defineStore } from 'pinia'

export type PageType = 'agent' | 'api' | 'async-tasks'

export const useAppStore = defineStore('app', {
  state: () => ({
    currentPage: 'agent' as PageType,
  }),
  actions: {
    setCurrentPage(page: PageType) {
      this.currentPage = page
    },
  },
})

