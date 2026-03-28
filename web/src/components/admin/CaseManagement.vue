<template>
  <div class="space-y-4 xs:space-y-6">
    <!-- 头部操作栏 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div class="flex items-center gap-2 xs:gap-4">
        <h2 class="text-base xs:text-lg font-semibold text-gray-900">案例管理</h2>
        <span class="text-xs xs:text-sm text-gray-500">共 {{ totalCount }} 个案例</span>
      </div>
      <button
        @click="showCreateModal = true"
        class="inline-flex items-center justify-center gap-1.5 xs:gap-2 px-3 xs:px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-strong transition-colors text-sm xs:text-base min-h-[44px] min-w-[44px]"
      >
        <span class="material-symbols-outlined !text-base">add</span>
        <span class="hidden sm:inline">新建案例</span>
        <span class="sm:hidden">新建</span>
      </button>
    </div>

    <!-- 筛选栏 -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
      <div class="relative flex-1 sm:max-w-xs">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 !text-sm">search</span>
        <input
          v-model="filters.keyword"
          @input="handleSearch"
          type="text"
          placeholder="搜索标题、描述..."
          class="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-1 focus:ring-primary focus:border-primary min-h-[44px]"
        >
      </div>

      <select
        v-model="filters.category"
        @change="fetchCases()"
        class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-1 focus:ring-primary focus:border-primary min-h-[44px]"
      >
        <option value="">全部分类</option>
        <option v-for="cat in allCategories" :key="cat" :value="cat">
          {{ cat }}
        </option>
      </select>

      <select
        v-model="filters.is_published"
        @change="fetchCases()"
        class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-1 focus:ring-primary focus:border-primary min-h-[44px]"
      >
        <option value="">全部状态</option>
        <option value="true">已发布</option>
        <option value="false">未发布</option>
      </select>

      <button
        @click="resetFilters"
        class="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 min-h-[44px] flex items-center justify-center"
      >
        重置
      </button>
    </div>

    <!-- 案例列表 -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[200px]">
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>

      <div v-else-if="cases.length === 0" class="text-center py-12">
        <span class="material-symbols-outlined !text-5xl text-gray-300 mb-3 block">folder_open</span>
        <p class="text-sm text-gray-500">暂无案例</p>
        <button
          @click="fetchCases"
          class="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-strong transition-colors"
        >
          重新加载
        </button>
      </div>

      <!-- 桌面端表格 -->
      <table v-if="!loading && cases.length > 0" class="w-full hidden md:table">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">图片</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">标题</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">分类</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">状态</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">浏览/使用</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">排序</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="caseItem in cases" :key="caseItem.id" class="hover:bg-gray-50">
            <td class="px-4 py-3">
              <img
                :src="getCaseImageSources(caseItem)[0]"
                :data-fallback-src="getCaseImageSources(caseItem)[1] || ''"
                :alt="caseItem.title"
                class="w-16 h-16 rounded-lg object-cover"
                @error="handleImageFallback"
              >
            </td>
            <td class="px-4 py-3">
              <div class="max-w-xs">
                <p class="font-medium text-gray-900 truncate">{{ caseItem.title }}</p>
                <p v-if="caseItem.description" class="text-xs text-gray-500 truncate mt-1">
                  {{ caseItem.description }}
                </p>
              </div>
            </td>
            <td class="px-4 py-3">
              <span class="px-2 py-1 bg-primary/10 text-primary text-xs font-medium rounded">
                {{ caseItem.category }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span
                :class="[
                  'px-2 py-1 text-xs font-medium rounded',
                  caseItem.is_published
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                ]"
              >
                {{ caseItem.is_published ? '已发布' : '未发布' }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">
              {{ caseItem.view_count }} / {{ caseItem.use_count }}
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">
              {{ caseItem.sort_order }}
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-2">
                <button
                  @click="editCase(caseItem)"
                  class="p-1.5 text-gray-600 hover:text-primary hover:bg-primary/5 rounded transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                  title="编辑"
                >
                  <span class="material-symbols-outlined !text-lg">edit</span>
                </button>
                <button
                  @click="togglePublish(caseItem)"
                  :class="[
                    'p-1.5 rounded transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center',
                    caseItem.is_published
                      ? 'text-gray-600 hover:text-orange-600 hover:bg-orange-50'
                      : 'text-gray-600 hover:text-green-600 hover:bg-green-50'
                  ]"
                  :title="caseItem.is_published ? '隐藏' : '发布'"
                >
                  <span class="material-symbols-outlined !text-lg">
                    {{ caseItem.is_published ? 'visibility_off' : 'visibility' }}
                  </span>
                </button>
                <button
                  @click="deleteCase(caseItem)"
                  class="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                  title="删除"
                >
                  <span class="material-symbols-outlined !text-lg">delete</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 移动端卡片布局 -->
      <div v-if="!loading && cases.length > 0" class="divide-y divide-gray-200 md:hidden">
        <div
          v-for="caseItem in cases"
          :key="caseItem.id"
          class="p-4 space-y-3"
        >
          <!-- 卡片头部：图片 + 标题 + 状态 -->
          <div class="flex gap-3">
            <img
              :src="getCaseImageSources(caseItem)[0]"
              :data-fallback-src="getCaseImageSources(caseItem)[1] || ''"
              :alt="caseItem.title"
              class="w-20 h-20 rounded-lg object-cover flex-shrink-0"
              @error="handleImageFallback"
            >
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <h3 class="font-semibold text-gray-900 text-sm line-clamp-2">{{ caseItem.title }}</h3>
                <span
                  :class="[
                    'px-2 py-0.5 text-xs font-medium rounded flex-shrink-0',
                    caseItem.is_published
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-700'
                  ]"
                >
                  {{ caseItem.is_published ? '已发布' : '未发布' }}
                </span>
              </div>
              <p v-if="caseItem.description" class="text-xs text-gray-500 line-clamp-1 mt-1">
                {{ caseItem.description }}
              </p>
              <div class="flex items-center gap-2 mt-2">
                <span class="px-2 py-0.5 bg-primary/10 text-primary text-xs font-medium rounded">
                  {{ caseItem.category }}
                </span>
                <span class="text-xs text-gray-500">
                  {{ caseItem.view_count }} 浏览 / {{ caseItem.use_count }} 使用
                </span>
              </div>
            </div>
          </div>

          <!-- 卡片底部：操作按钮 -->
          <div class="flex items-center justify-end gap-2 pt-2 border-t border-gray-100">
            <button
              @click="editCase(caseItem)"
              class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-primary bg-primary/5 hover:bg-primary/10 rounded-lg transition-colors min-h-[44px]"
            >
              <span class="material-symbols-outlined !text-lg">edit</span>
              编辑
            </button>
            <button
              @click="togglePublish(caseItem)"
              :class="[
                'flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg transition-colors min-h-[44px]',
                caseItem.is_published
                  ? 'text-orange-600 bg-orange-50 hover:bg-orange-100'
                  : 'text-green-600 bg-green-50 hover:bg-green-100'
              ]"
            >
              <span class="material-symbols-outlined !text-lg">
                {{ caseItem.is_published ? 'visibility_off' : 'visibility' }}
              </span>
              {{ caseItem.is_published ? '隐藏' : '发布' }}
            </button>
            <button
              @click="deleteCase(caseItem)"
              class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors min-h-[44px]"
            >
              <span class="material-symbols-outlined !text-lg">delete</span>
              删除
            </button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalCount > pageSize" class="px-3 xs:px-4 py-3 border-t border-gray-200 flex flex-col sm:flex-row items-center justify-between gap-3">
        <span class="text-xs xs:text-sm text-gray-600 text-center sm:text-left">
          显示 {{ offset + 1 }}-{{ Math.min(offset + pageSize, totalCount) }} / 共 {{ totalCount }} 条
        </span>
        <div class="flex items-center justify-center gap-2 w-full sm:w-auto">
          <button
            @click="prevPage"
            :disabled="currentPage === 0"
            class="flex-1 sm:flex-none px-3 xs:px-4 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 min-h-[44px]"
          >
            上一页
          </button>
          <span class="text-xs xs:text-sm text-gray-600 px-2">
            {{ currentPage + 1 }} / {{ totalPages }}
          </span>
          <button
            @click="nextPage"
            :disabled="currentPage >= totalPages - 1"
            class="flex-1 sm:flex-none px-3 xs:px-4 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 min-h-[44px]"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑模态框 -->
    <CaseFormModal
      v-if="showCreateModal || showEditModal"
      :case-data="editingCase"
      @close="closeModal"
      @save="handleSave"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/api'
import { handleImageFallback, resolveImageSrcCandidates } from '@/utils/imageFallback'
import CaseFormModal from './CaseFormModal.vue'

const cases = ref([])
const totalCount = ref(0)
const loading = ref(false)

const filters = ref({
  keyword: '',
  category: '',
  is_published: ''
})

const currentPage = ref(0)
const pageSize = ref(20)
const offset = computed(() => currentPage.value * pageSize.value)
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingCase = ref(null)

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

// 自定义分类
const customCategories = ref([])

// 所有分类
const allCategories = computed(() => {
  return [...presetCategories, ...customCategories.value]
})

const getCaseImageSources = (caseItem) => {
  return resolveImageSrcCandidates(caseItem?.thumbnail_url, caseItem?.image_url)
}

// 加载自定义分类
const loadCustomCategories = () => {
  const saved = localStorage.getItem('custom_case_categories')
  if (saved) {
    try {
      customCategories.value = JSON.parse(saved)
    } catch (e) {
      customCategories.value = []
    }
  }
}

let searchTimeout = null

const fetchCases = async () => {
  loading.value = true
  try {
    const params = {
      keyword: filters.value.keyword || undefined,
      category: filters.value.category || undefined,
      is_published: filters.value.is_published === '' ? undefined : filters.value.is_published === 'true',
      limit: pageSize.value,
      offset: offset.value
    }

    cases.value = await api.getAdminCases(params)

    const countResult = await api.getAdminCasesCount({
      keyword: params.keyword,
      category: params.category,
      is_published: params.is_published
    })
    totalCount.value = countResult.count
  } catch (error) {
    console.error('[案例管理] 获取案例列表失败:', error)
    // 显示错误信息
    alert('获取案例列表失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 0
    fetchCases()
  }, 300)
}

const resetFilters = () => {
  filters.value = {
    keyword: '',
    category: '',
    is_published: ''
  }
  currentPage.value = 0
  fetchCases()
}

const prevPage = () => {
  if (currentPage.value > 0) {
    currentPage.value--
    fetchCases()
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value - 1) {
    currentPage.value++
    fetchCases()
  }
}

const editCase = (caseItem) => {
  editingCase.value = { ...caseItem }
  showEditModal.value = true
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingCase.value = null
}

const handleSave = async () => {
  closeModal()
  await fetchCases()
}

const togglePublish = async (caseItem) => {
  try {
    const updated = await api.toggleCasePublishStatus(caseItem.id)
    const index = cases.value.findIndex(c => c.id === caseItem.id)
    if (index !== -1) {
      cases.value[index] = updated
    }
  } catch (error) {
    console.error('切换发布状态失败:', error)
  }
}

const deleteCase = async (caseItem) => {
  if (!confirm(`确定要删除案例"${caseItem.title}"吗？`)) return

  try {
    await api.deleteCase(caseItem.id)
    cases.value = cases.value.filter(c => c.id !== caseItem.id)
    totalCount.value--
  } catch (error) {
    console.error('删除案例失败:', error)
  }
}

onMounted(() => {
  loadCustomCategories()
  fetchCases()
})
</script>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
