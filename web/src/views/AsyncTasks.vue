<template>
  <div class="h-screen flex overflow-hidden bg-background-dark text-ink-950">
    <MainSidebar />

    <div class="flex-1 flex flex-col bg-white/50">
      <!-- Header -->
      <header class="border-b border-border-dark px-6 py-4 bg-white/80 backdrop-blur-xl">
        <div>
          <h1 class="text-2xl font-bold">异步任务管理</h1>
          <p class="text-sm text-slate-400 mt-1">
            查看和管理所有异步生图任务
          </p>
        </div>
      </header>

      <!-- Search -->
      <div class="border-b border-border-dark bg-white/80 px-6 py-4">
        <div class="flex flex-wrap gap-3 items-end">
          <div class="flex-1 min-w-[200px]">
            <label class="text-xs text-slate-400 mb-1.5 block">开始时间</label>
            <input
                type="datetime-local"
                v-model="startTime"
                class="w-full bg-white border border-border-dark px-3 py-2 rounded-lg text-sm outline-none"
            />
          </div>

          <div class="flex-1 min-w-[200px]">
            <label class="text-xs text-slate-400 mb-1.5 block">结束时间</label>
            <input
                type="datetime-local"
                v-model="endTime"
                class="w-full bg-white border border-border-dark px-3 py-2 rounded-lg text-sm outline-none"
            />
          </div>

          <div class="flex-1 min-w-[160px]">
            <label class="text-xs text-slate-400 mb-1.5 block">模型</label>
            <select
                v-model="modelName"
                class="w-full bg-white border border-border-dark px-3 py-2 rounded-lg text-sm outline-none"
            >
              <option value="">全部</option>
              <option v-for="model in models" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
          </div>

          <div class="w-36">
            <label class="text-xs text-slate-400 mb-1.5 block">状态</label>
            <select
                v-model="status"
                class="w-full bg-white border border-border-dark px-3 py-2 rounded-lg text-sm outline-none"
            >
              <option value="">全部</option>
              <option value="pending">排队中</option>
              <option value="processing">生成中</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
            </select>
          </div>

          <button
              @click="search"
              class="bg-primary-strong hover:bg-primary-deep px-6 py-2 rounded-lg text-sm font-medium text-white shadow-lg"
          >
            查询
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="flex-1 overflow-auto px-4 md:px-6 py-4">
        <div
            class="bg-white rounded-lg border border-border-dark overflow-hidden shadow-lg"
        >
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-background-dark">
              <tr class="border-b border-border-dark">
                <th class="px-4 py-3 text-left">任务ID</th>
                <th class="px-4 py-3 text-left">模型</th>
                <th class="px-4 py-3 text-left">提交时间</th>
                <th class="px-4 py-3 text-left">状态</th>
                <th class="px-4 py-3 text-left">进度</th>
                <th class="px-4 py-3 text-left">操作</th>
              </tr>
              </thead>

              <tbody>
              <tr v-if="tasks.length === 0">
                <td colspan="6" class="px-4 py-12 text-center text-slate-500">
                  暂无任务数据
                </td>
              </tr>

              <tr
                  v-for="task in tasks"
                  :key="task.id"
                  class="border-b border-border-dark hover:bg-primary/5"
              >
                <!-- ID -->
                <td class="px-4 py-3 font-mono text-xs">
                  <button @click="copyTaskId(task.id)">
                    {{ task.id.slice(0, 12) }}...
                  </button>
                </td>

                <!-- Model -->
                <td class="px-4 py-3">
                    <span
                        class="px-2 py-1 bg-primary/10 text-primary rounded text-xs border border-primary/20"
                    >
                      {{ task.type }}
                    </span>
                </td>

                <!-- Time -->
                <td class="px-4 py-3 text-xs">
                  {{ formatTime(task.submitTime) }}
                </td>

                <!-- Status -->
                <td class="px-4 py-3">
                    <span :class="getStatusClass(task.status)">
                      {{ getStatusText(task.status) }}
                    </span>
                </td>

                <!-- Progress -->
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <div
                        class="flex-1 h-1.5 bg-border-dark rounded-full overflow-hidden"
                    >
                      <div
                          class="h-full bg-primary transition-all"
                          :style="{ width: (task.progress || 0) + '%' }"
                      />
                    </div>
                    <span class="text-xs w-10">
                        {{ task.progress || 0 }}%
                      </span>
                  </div>
                </td>

                <!-- Actions -->
                <td class="px-4 py-3">
                  <div class="flex gap-2">
                    <button
                        v-if="
                          task.status === 'completed' &&
                          task.resultUrls?.length > 0
                        "
                        @click="viewImages(task)"
                        class="text-primary text-xs font-medium"
                    >
                      查看图片
                    </button>

                    <button
                        @click="viewDetail(task)"
                        class="text-ink-500 text-xs font-medium"
                    >
                      详情
                    </button>
                  </div>
                </td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <ImagePreviewModal ref="previewModal" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import { useAsyncTaskStore } from "../store/useAsyncTaskStore"
import MainSidebar from "../components/sidebar/MainSidebar.vue"
import ImagePreviewModal from "../components/ImagePreviewModal.vue"
import { api } from "@/services/api"

const taskStore = useAsyncTaskStore()
const previewModal = ref(null)

const startTime = ref("2026-03-16T00:00")
const endTime = ref("2026-03-16T23:46")
const modelName = ref("")
const status = ref("")

const tasks = ref([])
const models = ref([])
let timer = null

const updateTasks = () => {
  let filteredTasks = taskStore.tasks

  // 按模型名称筛选
  if (modelName.value) {
    filteredTasks = filteredTasks.filter(t => t.type === modelName.value)
  }

  tasks.value = filteredTasks
}

const search = () => {
  taskStore.loadTasks({
    startTime: startTime.value,
    endTime: endTime.value,
    status: status.value,
    modelName: modelName.value,
  })
  updateTasks()
}

const testSubmit = async () => {
  await taskStore.submitTask(
      "测试提示词：生成一张风景图",
      { width: 1024, height: 1024 },
      "image"
  )
  updateTasks()
}

const viewImages = (task) => {
  if (!task.resultUrls?.length) return alert("暂无图片")
  previewModal.value.show(task.resultUrls)
}

const viewDetail = (task) => {
  alert(JSON.stringify(task, null, 2))
}

const formatTime = (time) => {
  if (!time) return "-"
  return new Date(time).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

const getStatusClass = (status) => {
  const map = {
    pending: "px-2 py-1 text-xs bg-amber-500/10 text-amber-700 border border-amber-500/20 rounded",
    processing: "px-2 py-1 text-xs bg-primary/10 text-primary border border-primary/20 rounded",
    completed: "px-2 py-1 text-xs bg-primary/10 text-primary border border-primary/20 rounded",
    failed: "px-2 py-1 text-xs bg-red-500/10 text-red-500 border border-red-500/20 rounded",
  }
  return map[status] || map.pending
}

const getStatusText = (status) =>
    ({
      pending: "排队中",
      processing: "生成中",
      completed: "已完成",
      failed: "失败",
    }[status] || status)

const copyTaskId = (id) => {
  navigator.clipboard.writeText(id)
  alert("任务ID已复制")
}

const loadModels = async () => {
  try {
    const response = await api.getModels('image')
    const modelList = response.models || []
    const asyncModels = modelList.filter(m => m.tags?.includes('异步'))
    models.value = [...new Set(asyncModels.map(m => m.model_name))].sort()
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

onMounted(() => {
  loadModels()
  search()
  timer = setInterval(updateTasks, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
  taskStore.polling.forEach((_, id) => taskStore.stopPolling(id))
})
</script>
