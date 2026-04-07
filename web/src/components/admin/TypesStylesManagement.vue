<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-ink-950">类型与风格管理</h2>
      <div class="flex gap-2">
        <el-button @click="loadData" :loading="loading" circle>
          <span class="material-symbols-outlined !text-lg">refresh</span>
        </el-button>
        <el-button type="primary" @click="saveData" :loading="saving">
          <span class="material-symbols-outlined !text-lg mr-1">save</span>
          保存
        </el-button>
      </div>
    </div>

    <el-alert v-if="saved" type="success" :closable="true" @close="saved = false">配置已保存</el-alert>

    <!-- 类型管理（纯文字标签，无需图片） -->
    <div class="bg-white rounded-2xl shadow-sm border border-border-dark p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-ink-950 flex items-center gap-2">
          <span class="material-symbols-outlined !text-xl text-primary">category</span>
          类型（文字标签，无需图片）
        </h3>
        <el-button size="small" @click="addType">
          <span class="material-symbols-outlined !text-sm mr-1">add</span>
          添加类型
        </el-button>
      </div>

      <div class="flex flex-wrap gap-2">
        <div v-for="(t, idx) in types" :key="idx" class="flex items-center gap-1.5 border border-border-dark rounded-lg px-2 py-1.5">
          <el-input v-model="t.label" size="small" class="!w-24" placeholder="名称" />
          <el-input v-model="t.value" size="small" class="!w-24" placeholder="英文KEY" />
          <el-button type="danger" size="small" text @click="types.splice(idx, 1)" class="!p-0 !ml-0">
            <span class="material-symbols-outlined !text-sm">close</span>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 风格管理（带封面图） -->
    <div class="bg-white rounded-2xl shadow-sm border border-border-dark p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-ink-950 flex items-center gap-2">
          <span class="material-symbols-outlined !text-xl text-primary">palette</span>
          风格（带封面图）
        </h3>
        <el-button size="small" @click="addStyle">
          <span class="material-symbols-outlined !text-sm mr-1">add</span>
          添加风格
        </el-button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div v-for="(s, idx) in styles" :key="idx" class="flex items-center gap-3 border border-border-dark rounded-xl p-3">
          <!-- 封面预览 -->
          <div class="w-16 h-16 shrink-0 rounded-lg overflow-hidden bg-primary-soft/20">
            <img v-if="s.cover" :src="s.cover" class="w-full h-full object-cover" />
            <div v-else class="flex h-full items-center justify-center text-sm font-bold text-ink-400">{{ s.label }}</div>
          </div>
          <!-- 表单 -->
          <div class="flex-1 min-w-0 space-y-1.5">
            <div class="flex gap-2">
              <el-input v-model="s.label" size="small" placeholder="风格名称" class="!flex-1" />
              <el-input v-model="s.value" size="small" placeholder="英文KEY" class="!flex-1" />
            </div>
            <el-input v-model="s.cover" size="small" placeholder="封面图URL（可选）" />
          </div>
          <el-button type="danger" size="small" text @click="styles.splice(idx, 1)">
            <span class="material-symbols-outlined !text-lg">delete</span>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const saved = ref(false)

const types = ref([])
const styles = ref([])

async function loadData() {
  loading.value = true
  try {
    const res = await fetch('/api/v1/admin/system-config/types-styles')
    if (res.ok) {
      const data = await res.json()
      types.value = data.types || []
      styles.value = data.styles || []
    }
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function saveData() {
  saving.value = true
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/v1/admin/system-config/types-styles', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ types: types.value, styles: styles.value })
    })
    if (res.ok) {
      saved.value = true
      ElMessage.success('保存成功')
    } else {
      const data = await res.json()
      ElMessage.error(data.detail || '保存失败')
    }
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function addType() {
  types.value.push({ value: `type_${Date.now()}`, label: '' })
}

function addStyle() {
  styles.value.push({ value: `style_${Date.now()}`, label: '', cover: '' })
}

onMounted(() => {
  loadData()
})
</script>
