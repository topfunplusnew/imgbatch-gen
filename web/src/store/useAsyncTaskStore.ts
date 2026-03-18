import { defineStore } from 'pinia'

export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface AsyncTask {
  id: string
  taskId: string
  submitTime: string
  endTime?: string
  duration?: number
  type: string
  status: TaskStatus
  progress?: number
  prompt: string
  params: object
  resultUrls?: string[]
  error?: string
}

export const useAsyncTaskStore = defineStore('asyncTask', {
  state: () => ({
    tasks: [] as AsyncTask[],
    polling: new Map<string, number>(),
  }),

  actions: {
    async submitTask(prompt: string, params: object, type: string) {
      const task: AsyncTask = {
        id: Date.now().toString(),
        taskId: '',
        submitTime: new Date().toISOString(),
        type,
        status: 'pending',
        progress: 0,
        prompt,
        params,
      }

      this.tasks.unshift(task)

      // TODO: 调用API提交任务
      // const response = await fetch('/api/async/submit', { ... })
      // task.taskId = response.taskId

      this.startPolling(task.id)
      return task
    },

    startPolling(taskId: string) {
      if (this.polling.has(taskId)) return

      const timer = setInterval(() => {
        this.checkTaskStatus(taskId)
      }, 3000)

      this.polling.set(taskId, timer as unknown as number)
    },

    stopPolling(taskId: string) {
      const timer = this.polling.get(taskId)
      if (timer) {
        clearInterval(timer)
        this.polling.delete(taskId)
      }
    },

    async checkTaskStatus(taskId: string) {
      const task = this.tasks.find(t => t.id === taskId)
      if (!task) return

      // TODO: 调用API查询状态
      // const response = await fetch(`/api/async/status/${task.taskId}`)
      // task.status = response.status
      // task.progress = response.progress

      if (task.status === 'completed' || task.status === 'failed') {
        task.endTime = new Date().toISOString()
        task.duration = Math.floor((new Date(task.endTime).getTime() - new Date(task.submitTime).getTime()) / 1000)
        this.stopPolling(taskId)
      }
    },

    async loadTasks(filters?: { startTime?: string; endTime?: string; status?: string }) {
      try {
        const params = new URLSearchParams()
        if (filters?.status) params.append('status', filters.status)

        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/async/tasks?${params}`)
        const data = await response.json()

        this.tasks = data.tasks.map((t: any) => ({
          id: t.task_id,
          taskId: t.task_id,
          submitTime: t.submit_time,
          endTime: t.end_time,
          type: t.model,
          status: t.status,
          progress: t.progress,
          prompt: t.prompt,
          params: {},
          resultUrls: t.result_urls,
          error: t.error
        }))
      } catch (error) {
        console.error('加载任务失败:', error)
      }
    },

    addTask(task: any) {
      this.tasks.unshift({
        id: task.task_id,
        taskId: task.task_id,
        submitTime: new Date().toISOString(),
        type: task.model,
        status: task.status,
        progress: task.progress || 0,
        prompt: task.prompt,
        params: {},
      })
    },
  },
})
