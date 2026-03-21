<template>
  <div class="space-y-6">
    <!-- 基本信息 -->
    <div class="space-y-4">
      <!-- 标题 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          公告标题 <span class="text-red-500">*</span>
        </label>
        <input
          v-model="form.title"
          type="text"
          placeholder="请输入公告标题"
          maxlength="200"
          class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        />
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ form.title.length }}/200</p>
      </div>

      <!-- 富文本编辑器 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          公告内容 <span class="text-red-500">*</span>
        </label>
        <div class="border border-gray-300 dark:border-gray-600 rounded-xl overflow-hidden bg-white dark:bg-gray-800">
          <!-- 工具栏 -->
          <div class="flex flex-wrap items-center gap-1 p-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
            <!-- 标题级别 -->
            <select
              v-model="editorCommand.headingLevel"
              @change="setHeading"
              class="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="0">段落</option>
              <option value="1">H1</option>
              <option value="2">H2</option>
              <option value="3">H3</option>
            </select>

            <div class="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1"></div>

            <!-- 文本格式 -->
            <button
              @click="editor?.chain().focus().toggleBold().run()"
              :class="{ 'bg-primary/10 text-primary': editor?.isActive('bold') }"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="粗体"
            >
              <span class="material-symbols-outlined !text-lg">format_bold</span>
            </button>
            <button
              @click="editor?.chain().focus().toggleItalic().run()"
              :class="{ 'bg-primary/10 text-primary': editor?.isActive('italic') }"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="斜体"
            >
              <span class="material-symbols-outlined !text-lg">format_italic</span>
            </button>
            <button
              @click="editor?.chain().focus().toggleUnderline().run()"
              :class="{ 'bg-primary/10 text-primary': editor?.isActive('underline') }"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="下划线"
            >
              <span class="material-symbols-outlined !text-lg">format_underlined</span>
            </button>
            <button
              @click="editor?.chain().focus().toggleStrike().run()"
              :class="{ 'bg-primary/10 text-primary': editor?.isActive('strike') }"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="删除线"
            >
              <span class="material-symbols-outlined !text-lg">strikethrough_s</span>
            </button>

            <div class="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1"></div>

            <!-- 对齐方式 -->
            <button
              @click="editor?.chain().focus().setTextAlign('left').run()"
              :class="{ 'bg-primary/10 text-primary': editor?.isActive({ textAlign: 'left' }) }"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="左对齐"
            >
              <span class="material-symbols-outlined !text-lg">format_align_left</span>
            </button>
            <button
              @click="editor?.chain().focus().setTextAlign('center').run()"
              :class="{ 'bg-primary/10 text-primary': editor?.isActive({ textAlign: 'center' }) }"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="居中"
            >
              <span class="material-symbols-outlined !text-lg">format_align_center</span>
            </button>
            <button
              @click="editor?.chain().focus().setTextAlign('right').run()"
              :class="{ 'bg-primary/10 text-primary': editor?.isActive({ textAlign: 'right' }) }"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="右对齐"
            >
              <span class="material-symbols-outlined !text-lg">format_align_right</span>
            </button>

            <div class="w-px h-6 bg-gray-300 dark:border-gray-600 mx-1"></div>

            <!-- 列表 -->
            <button
              @click="editor?.chain().focus().toggleBulletList().run()"
              :class="{ 'bg-primary/10 text-primary': editor?.isActive('bulletList') }"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="无序列表"
            >
              <span class="material-symbols-outlined !text-lg">format_list_bulleted</span>
            </button>
            <button
              @click="editor?.chain().focus().toggleOrderedList().run()"
              :class="{ 'bg-primary/10 text-primary': editor?.isActive('orderedList') }"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="有序列表"
            >
              <span class="material-symbols-outlined !text-lg">format_list_numbered</span>
            </button>

            <div class="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1"></div>

            <!-- 插入链接 -->
            <button
              @click="addLink"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="插入链接"
            >
              <span class="material-symbols-outlined !text-lg">link</span>
            </button>

            <!-- 插入图片 -->
            <button
              @click="$refs.imageInput.click()"
              class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="插入图片"
            >
              <span class="material-symbols-outlined !text-lg">image</span>
            </button>
            <input
              ref="imageInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleImageUpload"
            />
          </div>

          <!-- 编辑器内容区 -->
          <editor-content
            :editor="editor"
            class="min-h-[300px] max-h-[500px] overflow-y-auto"
          />
        </div>
      </div>

      <!-- 封面图片 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          封面图片
        </label>
        <div class="flex items-start gap-4">
          <!-- 封面预览 -->
          <div
            v-if="form.cover_image_url"
            class="w-32 h-32 rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600 flex-shrink-0"
          >
            <img
              :src="form.cover_image_url"
              alt="封面图片"
              class="w-full h-full object-cover"
            />
          </div>
          <div
            v-else
            class="w-32 h-32 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center flex-shrink-0"
          >
            <span class="material-symbols-outlined !text-4xl text-gray-400">add_photo_alternate</span>
          </div>

          <!-- 上传按钮 -->
          <div class="flex-1">
            <input
              ref="coverInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleCoverUpload"
            />
            <button
              @click="$refs.coverInput.click()"
              class="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300"
            >
              {{ form.cover_image_url ? '更换封面' : '上传封面' }}
            </button>
            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              支持 JPG、PNG、GIF、WebP 格式，最大 5MB
            </p>
            <button
              v-if="form.cover_image_url"
              @click="removeCover"
              class="mt-2 px-3 py-1 text-xs text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 transition-colors"
            >
              删除封面
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 设置 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- 优先级 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          优先级
        </label>
        <select
          v-model="form.priority"
          class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="low">低</option>
          <option value="normal">普通</option>
          <option value="high">高</option>
          <option value="urgent">紧急</option>
        </select>
      </div>

      <!-- 公告类型 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          公告类型
        </label>
        <select
          v-model="form.announcement_type"
          class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="system">系统公告</option>
          <option value="maintenance">维护通知</option>
          <option value="feature">功能更新</option>
          <option value="promotion">活动推广</option>
        </select>
      </div>

      <!-- 目标受众 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          目标受众
        </label>
        <select
          v-model="form.target_audience"
          class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="all">所有用户</option>
          <option value="users_only">普通用户</option>
          <option value="admins_only">管理员</option>
        </select>
      </div>

      <!-- 过期时间 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          过期时间
        </label>
        <input
          v-model="form.expires_at"
          type="datetime-local"
          class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        />
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
          留空表示永不过期
        </p>
      </div>
    </div>

    <!-- 开关选项 -->
    <div class="flex flex-wrap items-center gap-6">
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          v-model="form.is_pinned"
          type="checkbox"
          class="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
        />
        <span class="text-sm text-gray-700 dark:text-gray-300">
          置顶显示
        </span>
      </label>

      <label class="flex items-center gap-2 cursor-pointer">
        <input
          v-model="form.is_published"
          type="checkbox"
          class="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
        />
        <span class="text-sm text-gray-700 dark:text-gray-300">
          立即发布
        </span>
      </label>
    </div>

    <!-- 操作按钮 -->
    <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
      <button
        @click="$emit('cancel')"
        class="px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        取消
      </button>
      <button
        v-if="!editingId"
        @click="handleSaveDraft"
        :disabled="saving"
        class="px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ saving ? '保存中...' : '保存草稿' }}
      </button>
      <button
        @click="handleSubmit"
        :disabled="saving"
        class="px-6 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-primary to-primary-deep rounded-xl hover:from-primary-strong hover:to-primary-deep disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
      >
        {{ saving ? '保存中...' : (editingId ? '更新' : '发布') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import { api } from '@/services/api'

const props = defineProps<{
  announcementId?: string | null
}>()

const emit = defineEmits<{
  submit: []
  cancel: []
}>()

const editingId = ref(props.announcementId || null)
const saving = ref(false)
const editorCommand = ref({ headingLevel: '0' })

const form = ref({
  title: '',
  content: '',
  priority: 'normal',
  announcement_type: 'system',
  target_audience: 'all',
  is_pinned: false,
  is_published: true,
  expires_at: '',
  cover_image_url: '',
})

// TipTap 编辑器
const editor = useEditor({
  content: '',
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3],
      },
    }),
    Underline,
    TextAlign.configure({
      types: ['heading', 'paragraph'],
    }),
    Link.configure({
      openOnClick: false,
    }),
    Image,
  ],
  editorProps: {
    attributes: {
      class: 'prose dark:prose-invert max-w-none focus:outline-none min-h-[300px] p-4',
    },
  },
  onUpdate: ({ editor }) => {
    form.value.content = editor.getHTML()
  },
})

// 设置标题级别
function setHeading() {
  const level = parseInt(editorCommand.value.headingLevel)
  if (level === 0) {
    editor.value?.chain().focus().setParagraph().run()
  } else {
    editor.value?.chain().focus().toggleHeading({ level }).run()
  }
  editorCommand.value.headingLevel = '0'
}

// 检查内容是否为空（更智能的检测）
function isContentEmpty(html: string): boolean {
  if (!html) return true

  // 检查空段落标签
  if (html === '<p></p>' || html === '<p></p>\n') return true

  // 去除HTML标签检查是否有实际文本
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html
  const textContent = tempDiv.textContent || tempDiv.innerText || ''

  return !textContent.trim()
}

// 添加链接
function addLink() {
  const url = prompt('请输入链接地址:')
  if (url) {
    editor.value?.chain().focus().setLink({ href: url }).run()
  }
}

// 处理编辑器内图片上传
async function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  try {
    // 将图片转为 base64 插入到编辑器
    const reader = new FileReader()
    reader.onload = (e) => {
      editor.value?.chain().focus().setImage({ src: e.target?.result as string }).run()
    }
    reader.readAsDataURL(file)
  } catch (error) {
    console.error('上传图片失败:', error)
    alert('上传图片失败，请重试')
  }

  // 清空 input
  input.value = ''
}

// 处理封面上传
async function handleCoverUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 验证文件大小（5MB）
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过 5MB')
    return
  }

  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    alert('只支持 JPG、PNG、GIF、WebP 格式的图片')
    return
  }

  saving.value = true
  try {
    // 如果是编辑模式，先保存公告获取ID
    if (!editingId.value && !form.value.title) {
      alert('请先输入公告标题')
      return
    }

    // 创建临时公告以获取ID（如果是新建）
    let announcementId = editingId.value
    if (!announcementId) {
      const tempResult = await api.createAnnouncement({
        title: form.value.title,
        content: form.value.content || '<p></p>',
        priority: form.value.priority,
        announcement_type: form.value.announcement_type,
        is_pinned: form.value.is_pinned,
        is_published: false, // 先不发布
        target_audience: form.value.target_audience,
      })
      announcementId = tempResult.id
      editingId.value = announcementId
    }

    // 上传封面
    const result = await api.uploadAnnouncementCover(announcementId, file)
    form.value.cover_image_url = result.url
  } catch (error) {
    console.error('上传封面失败:', error)
    alert('上传封面失败，请重试')
  } finally {
    saving.value = false
  }

  // 清空 input
  input.value = ''
}

// 删除封面
function removeCover() {
  form.value.cover_image_url = ''
}

// 保存草稿
async function handleSaveDraft() {
  if (!form.value.title) {
    alert('请输入公告标题')
    return
  }

  saving.value = true
  try {
    const data = {
      ...form.value,
      is_published: false,
    }

    if (editingId.value) {
      await api.updateAnnouncement(editingId.value, data)
    } else {
      const result = await api.createAnnouncement(data)
      editingId.value = result.id
    }

    alert('草稿已保存')
  } catch (error: any) {
    console.error('[Announcement Form] Save draft error:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    })

    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 403) {
      alert('权限不足：需要管理员权限')
    } else if (status === 401) {
      alert('未授权，请重新登录')
    } else {
      alert(detail || '保存失败，请重试')
    }
  } finally {
    saving.value = false
  }
}

// 提交表单
async function handleSubmit() {
  if (!form.value.title) {
    alert('请输入公告标题')
    return
  }

  if (!form.value.content || isContentEmpty(form.value.content)) {
    alert('请输入公告内容')
    return
  }

  // 添加详细日志
  console.log('[Announcement Form] Submitting:', {
    isEdit: !!editingId.value,
    hasTitle: !!form.value.title,
    hasContent: !!form.value.content,
    contentLength: form.value.content?.length,
    contentPreview: form.value.content?.substring(0, 100)
  })

  saving.value = true
  const startTime = Date.now()

  try {
    const data = {
      ...form.value,
      expires_at: form.value.expires_at || null,
    }

    let response
    if (editingId.value) {
      console.log('[Announcement Form] Calling update API')
      response = await api.updateAnnouncement(editingId.value, data)
    } else {
      console.log('[Announcement Form] Calling create API')
      response = await api.createAnnouncement(data)
    }

    console.log('[Announcement Form] Success:', response)
    emit('submit')
  } catch (error: any) {
    const duration = Date.now() - startTime
    console.error('[Announcement Form] Error:', {
      duration,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    })

    // 提取详细错误信息
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 403) {
      alert('权限不足：需要管理员权限')
    } else if (status === 401) {
      alert('未授权，请重新登录')
    } else if (status === 400) {
      alert(detail || '请求参数错误，请检查输入')
    } else {
      alert(detail || '保存失败，请重试')
    }
  } finally {
    saving.value = false
  }
}

// 加载公告数据（编辑模式）
async function loadAnnouncement() {
  if (!editingId.value) return

  try {
    const announcement = await api.getAdminAnnouncementById(editingId.value)

    form.value = {
      title: announcement.title,
      content: announcement.content,
      priority: announcement.priority,
      announcement_type: announcement.announcement_type,
      target_audience: announcement.target_audience,
      is_pinned: announcement.is_pinned,
      is_published: announcement.is_published,
      expires_at: announcement.expires_at ? announcement.expires_at.slice(0, 16) : '',
      cover_image_url: announcement.cover_image_url || '',
    }

    // 设置编辑器内容
    editor.value?.commands.setContent(announcement.content)
  } catch (error) {
    console.error('加载公告失败:', error)
    alert('加载公告失败')
  }
}

onMounted(() => {
  loadAnnouncement()
})

// 监听 announcementId 变化
watch(() => props.announcementId, (newId) => {
  editingId.value = newId || null
  if (newId) {
    loadAnnouncement()
  } else {
    // 重置表单
    form.value = {
      title: '',
      content: '',
      priority: 'normal',
      announcement_type: 'system',
      target_audience: 'all',
      is_pinned: false,
      is_published: true,
      expires_at: '',
      cover_image_url: '',
    }
    editor.value?.commands.setContent('')
  }
})
</script>

<style>
/* TipTap 编辑器样式 */
.ProseMirror {
  outline: none;
}

.ProseMirror p.is-editor-empty:first-child::before {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

.ProseMirror img {
  max-width: 100%;
  height: auto;
  border-radius: 0.5rem;
  margin: 1rem 0;
}

.ProseMirror a {
  color: #3b82f6;
  text-decoration: underline;
}
</style>
