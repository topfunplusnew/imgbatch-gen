<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 xs:p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[95vh] xs:max-h-[90vh] overflow-hidden flex flex-col">
      <!-- 标题 -->
      <div class="px-4 xs:px-6 py-3 xs:py-4 border-b border-gray-200 flex items-center justify-between">
        <h3 class="text-base xs:text-lg font-semibold text-gray-900">
          {{ isEdit ? '编辑案例' : '新建案例' }}
        </h3>
        <button
          @click="$emit('close')"
          class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
        >
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <!-- 表单内容 -->
      <div class="flex-1 overflow-y-auto p-4 xs:p-6 space-y-4 xs:space-y-6">
        <!-- 图片上传 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">案例图片 *</label>
          <div
            @click="selectImage"
            @drop.prevent="handleDrop"
            @dragover.prevent
            class="relative aspect-video border-2 border-dashed border-gray-300 rounded-xl overflow-hidden cursor-pointer hover:border-primary transition-colors"
          >
            <img
              v-if="imagePreview"
              :src="imagePreview"
              alt="案例图片"
              class="w-full h-full object-cover"
            >
            <div v-else class="flex flex-col items-center justify-center h-full text-gray-400 p-4">
              <span class="material-symbols-outlined !text-4xl xs:!text-5xl mb-2">add_photo_alternate</span>
              <p class="text-xs xs:text-sm text-center">点击或拖拽上传图片</p>
              <p class="text-[10px] xs:text-xs mt-1 text-center">支持 JPG、PNG、WEBP 格式</p>
            </div>
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleFileSelect"
            >
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 xs:gap-4">
          <div class="col-span-1 sm:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">标题 *</label>
            <input
              v-model="form.title"
              type="text"
              placeholder="请输入案例标题"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary focus:border-primary min-h-[44px]"
            >
          </div>

          <div class="col-span-1 sm:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
            <textarea
              v-model="form.description"
              rows="3"
              placeholder="请输入案例描述"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary focus:border-primary resize-none"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">行业分类 *</label>
            <div class="relative">
              <input
                v-model="categoryInput"
                list="category-list"
                placeholder="请选择或输入分类"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary focus:border-primary pr-16 min-h-[44px]"
              >
              <datalist id="category-list">
                <option v-for="cat in allCategories" :key="cat" :value="cat">
                  {{ cat }}
                </option>
              </datalist>
              <button
                v-if="categoryInput && !isExistingCategory(categoryInput)"
                @click.stop="addCustomCategory"
                class="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 bg-primary text-white text-xs rounded hover:bg-primary-strong transition-colors min-h-[32px]"
              >
                + 新建
              </button>
            </div>
            <p v-if="categoryInput && !isExistingCategory(categoryInput)" class="text-xs text-primary mt-1">
              新建自定义分类
            </p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">排序权重</label>
            <input
              v-model.number="form.sort_order"
              type="number"
              placeholder="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary focus:border-primary min-h-[44px]"
            >
          </div>

          <div class="col-span-1 sm:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">标签</label>
            <input
              v-model="tagsInput"
              type="text"
              placeholder="多个标签用逗号分隔，如：产品展示, 白色背景, 简约"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary focus:border-primary min-h-[44px]"
            >
          </div>
        </div>

        <!-- 生成参数 -->
        <div class="space-y-4">
          <h4 class="text-sm font-semibold text-gray-900">生成参数</h4>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">提示词 *</label>
            <textarea
              v-model="form.prompt"
              rows="4"
              placeholder="请输入生成图片的提示词"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary focus:border-primary resize-none font-mono text-xs xs:text-sm"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">负面提示词</label>
            <textarea
              v-model="form.negative_prompt"
              rows="2"
              placeholder="请输入负面提示词（可选）"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary focus:border-primary resize-none font-mono text-xs xs:text-sm"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">模型</label>
            <select
              v-model="form.model"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary focus:border-primary min-h-[44px]"
            >
              <option value="">请选择模型</option>
              <option v-if="loadingModels" disabled>加载中...</option>
              <option v-for="model in imageModels" :key="model.id" :value="model.name">
                {{ model.name }}
              </option>
            </select>
          </div>
        </div>

        <!-- 其他选项 -->
        <div class="flex items-center gap-4">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              v-model="form.is_published"
              type="checkbox"
              class="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
            >
            <span class="text-sm font-medium text-gray-700">立即发布</span>
          </label>
        </div>
      </div>

      <!-- 底部按钮 -->
      <div class="px-4 xs:px-6 py-3 xs:py-4 border-t border-gray-200 flex items-center justify-end gap-2 xs:gap-3">
        <button
          @click="$emit('close')"
          class="flex-1 sm:flex-none px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg transition-colors min-h-[44px] sm:min-h-0"
        >
          取消
        </button>
        <button
          @click="save"
          :disabled="saving || !form.title || !form.category || !form.prompt"
          class="flex-1 sm:flex-none px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-strong rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] sm:min-h-0"
        >
          {{ saving ? '保存中...' : isEdit ? '保存' : '创建' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '@/services/api'
import { filterSelectableImageModels } from '@/utils/modelSelection'

const props = defineProps({
  caseData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

const fileInput = ref(null)
const imageFile = ref(null)
const imagePreview = ref('')
const previewObjectUrl = ref('')
const saving = ref(false)
const tagsInput = ref('')
const categoryInput = ref('')

// 模型列表
const imageModels = ref([])
const loadingModels = ref(false)

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

// 自定义分类列表
const customCategories = ref([])

// 所有分类（预设 + 自定义）
const allCategories = computed(() => {
  return [...presetCategories, ...customCategories.value]
})

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

// 保存自定义分类
const saveCustomCategories = () => {
  localStorage.setItem('custom_case_categories', JSON.stringify(customCategories.value))
}

// 检查分类是否已存在
const isExistingCategory = (category) => {
  return allCategories.value.includes(category)
}

// 添加自定义分类
const addCustomCategory = () => {
  if (categoryInput.value && !isExistingCategory(categoryInput.value)) {
    customCategories.value.push(categoryInput.value)
    saveCustomCategories()
  }
}

const form = ref({
  title: '',
  description: '',
  category: '',
  tags: [],
  prompt: '',
  negative_prompt: '',
  model: '',
  is_published: true,
  sort_order: 0
})

// 获取生图模型列表
const fetchImageModels = async () => {
  console.log('===== fetchImageModels函数开始执行 =====')
  loadingModels.value = true
  try {
    console.log('开始获取图像模型列表...')
    const result = await api.getModels('image')
    console.log('模型列表返回结果:', result)
    imageModels.value = filterSelectableImageModels(result.models || [])
    console.log('imageModels.value设置后:', imageModels.value)
    console.log('===== fetchImageModels函数执行完成 =====')
  } catch (error) {
    console.error('获取模型列表失败:', error)
    console.error('错误详情:', error.response?.data || error.message)
  } finally {
    loadingModels.value = false
  }
}

const isEdit = computed(() => !!props.caseData?.id)

// 同步categoryInput到form.category
watch(categoryInput, (newVal) => {
  form.value.category = newVal
})

// 同步form.category到categoryInput
watch(() => form.value.category, (newVal) => {
  if (newVal !== categoryInput.value) {
    categoryInput.value = newVal
  }
})

// 初始化表单
watch(() => props.caseData, (newData) => {
  revokePreviewObjectUrl()
  if (newData) {
    form.value = {
      title: newData.title || '',
      description: newData.description || '',
      category: newData.category || '',
      tags: newData.tags || [],
      prompt: newData.prompt || '',
      negative_prompt: newData.negative_prompt || '',
      model: newData.model || '',
      is_published: newData.is_published ?? true,
      sort_order: newData.sort_order ?? 0
    }
    categoryInput.value = newData.category || ''
    imagePreview.value = newData.thumbnail_url || newData.image_url || ''
    tagsInput.value = (newData.tags || []).join(', ')
  } else {
    form.value = {
      title: '',
      description: '',
      category: '',
      tags: [],
      prompt: '',
      negative_prompt: '',
      model: '',
      is_published: true,
      sort_order: 0
    }
    categoryInput.value = ''
    imagePreview.value = ''
    tagsInput.value = ''
  }
}, { immediate: true })

// 组件挂载时获取模型列表和加载自定义分类
onMounted(async () => {
  console.log('===== CaseFormModal组件已挂载 =====')
  console.log('当前时间:', new Date().toISOString())

  // 测试API是否可用
  try {
    console.log('测试API连接...')
    const healthResult = await api.healthCheck()
    console.log('API健康检查结果:', healthResult)
  } catch (error) {
    console.error('API健康检查失败:', error)
  }

  // 获取模型列表
  await fetchImageModels()

  // 加载自定义分类
  loadCustomCategories()
})

// 监控imageModels变化
watch(imageModels, (newVal) => {
  console.log('imageModels变化:', newVal.length, '个模型')
  if (newVal.length > 0) {
    console.log('第一个模型:', newVal[0])
  }
}, { deep: true })

const selectImage = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    setImageFile(file)
  }
}

const handleDrop = (event) => {
  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    setImageFile(file)
  }
}

const setImageFile = (file) => {
  imageFile.value = file
  revokePreviewObjectUrl()
  previewObjectUrl.value = URL.createObjectURL(file)
  imagePreview.value = previewObjectUrl.value
}

const revokePreviewObjectUrl = () => {
  if (!previewObjectUrl.value) return
  URL.revokeObjectURL(previewObjectUrl.value)
  previewObjectUrl.value = ''
}

onBeforeUnmount(() => {
  revokePreviewObjectUrl()
})

const parseTags = () => {
  if (tagsInput.value) {
    form.value.tags = tagsInput.value.split(',').map(t => t.trim()).filter(t => t)
  } else {
    form.value.tags = []
  }
}

const save = async () => {
  if (!form.value.title || !form.value.category || !form.value.prompt) {
    alert('请填写必填字段')
    return
  }

  // 如果是新分类，自动保存
  if (form.value.category && !isExistingCategory(form.value.category)) {
    customCategories.value.push(form.value.category)
    saveCustomCategories()
  }

  saving.value = true
  parseTags()

  try {
    if (isEdit.value) {
      await api.updateCase(props.caseData.id, form.value)
      if (imageFile.value) {
        await api.updateCaseImage(props.caseData.id, imageFile.value)
      }
    } else {
      if (!imageFile.value) {
        alert('请上传案例图片')
        return
      }
      await api.createCase(form.value, imageFile.value)
    }
    emit('save')
  } catch (error) {
    console.error('保存案例失败:', error)
    alert('保存失败，请重试')
  } finally {
    saving.value = false
  }
}
</script>
