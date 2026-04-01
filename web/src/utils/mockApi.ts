/**
 * 模拟API工具
 * 用于测试前端功能，当后端API不可用时
 */

import { ImageTask, GenerateRequest } from '@/services/api'

// 模拟延迟
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// 存储模拟任务
const mockTasks = new Map<string, ImageTask>()

/**
 * 生成模拟任务ID
 */
function generateTaskId(): string {
  return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 模拟生成图像
 */
export async function mockGenerateImage(request: GenerateRequest): Promise<ImageTask> {
  await delay(1000) // 模拟网络延迟

  const taskId = generateTaskId()
  const task: ImageTask = {
    task_id: taskId,
    status: 'pending',
    params: request
  }

  mockTasks.set(taskId, task)

  // 模拟处理过程
  setTimeout(() => {
    const currentTask = mockTasks.get(taskId)
    if (currentTask) {
      currentTask.status = 'processing'
    }
  }, 2000)

  // 5秒后完成
  setTimeout(() => {
    const currentTask = mockTasks.get(taskId)
    if (currentTask) {
      currentTask.status = 'completed'
      currentTask.result = {
        images: [
          {
            url: 'https://picsum.photos/1024/1024?random=' + Date.now(),
            alt: request.prompt
          }
        ]
      }
    }
  }, 5000)

  return task
}

/**
 * 模拟查询任务状态
 */
export async function mockGetTaskStatus(taskId: string): Promise<ImageTask> {
  await delay(500) // 模拟网络延迟

  const task = mockTasks.get(taskId)
  if (!task) {
    throw new Error('任务不存在')
  }

  return { ...task } // 返回副本
}

/**
 * 检查是否启用模拟模式
 */
export function isMockMode(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem('mockMode') === 'true'
}

/**
 * 设置模拟模式
 */
export function setMockMode(enabled: boolean) {
  if (typeof window === 'undefined') return
  if (enabled) {
    localStorage.setItem('mockMode', 'true')
  } else {
    localStorage.removeItem('mockMode')
  }
}
