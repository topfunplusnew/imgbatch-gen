<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-ink-950">产品定价管理</h2>
      <div class="flex gap-2">
        <el-button @click="loadConfig" :loading="loading" circle>
          <span class="material-symbols-outlined !text-lg">refresh</span>
        </el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">
          <span class="material-symbols-outlined !text-lg mr-1">save</span>
          保存配置
        </el-button>
      </div>
    </div>

    <el-alert v-if="saveSuccess" type="success" :closable="true" @close="saveSuccess = false">
      配置已保存成功
    </el-alert>

    <div v-if="loading && !config" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-3 border-primary border-t-transparent"></div>
    </div>

    <template v-if="config">
      <!-- 基础配置 -->
      <div class="bg-white rounded-2xl shadow-sm border border-border-dark p-6">
        <h3 class="text-lg font-semibold text-ink-950 mb-4 flex items-center gap-2">
          <span class="material-symbols-outlined !text-xl text-primary">tune</span>
          基础配置
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1">积分兑换比率</label>
            <el-input-number
              v-model="config.points_exchange.rate"
              :min="1" :max="10000"
              class="!w-full"
            />
            <p class="text-xs text-ink-400 mt-1">1元 = {{ config.points_exchange.rate }} 积分</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1">新用户赠送积分</label>
            <el-input-number
              v-model="config.initial_quota.points"
              :min="0" :max="100000"
              class="!w-full"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1">每日签到奖励积分</label>
            <el-input-number
              v-model="config.daily_checkin.reward_points"
              :min="0" :max="10000"
              class="!w-full"
            />
          </div>
        </div>
      </div>

      <!-- 充值选项 -->
      <div class="bg-white rounded-2xl shadow-sm border border-border-dark p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-ink-950 flex items-center gap-2">
            <span class="material-symbols-outlined !text-xl text-primary">account_balance_wallet</span>
            充值选项
          </h3>
          <el-button size="small" @click="addRechargeOption">
            <span class="material-symbols-outlined !text-sm mr-1">add</span>
            添加选项
          </el-button>
        </div>

        <el-table :data="config.recharge_options.options" border stripe>
          <el-table-column label="名称" min-width="120">
            <template #default="{ row }">
              <el-input v-model="row.name" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="金额(元)" width="110">
            <template #default="{ row }">
              <el-input-number v-model="row.amount_yuan" :min="1" size="small" class="!w-full"
                @change="v => { row.amount = v * 100 }" />
            </template>
          </el-table-column>
          <el-table-column label="积分" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.points" :min="0" size="small" class="!w-full" />
            </template>
          </el-table-column>
          <el-table-column label="赠送积分" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.bonus" :min="0" size="small" class="!w-full" />
            </template>
          </el-table-column>
          <el-table-column label="推荐" width="70" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.popular" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" align="center">
            <template #default="{ $index }">
              <el-button type="danger" size="small" text @click="removeRechargeOption($index)">
                <span class="material-symbols-outlined !text-lg">delete</span>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 订阅套餐 -->
      <div class="bg-white rounded-2xl shadow-sm border border-border-dark p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-ink-950 flex items-center gap-2">
            <span class="material-symbols-outlined !text-xl text-primary">card_membership</span>
            订阅套餐
          </h3>
          <el-button size="small" @click="addSubscriptionPlan">
            <span class="material-symbols-outlined !text-sm mr-1">add</span>
            添加套餐
          </el-button>
        </div>

        <div class="space-y-4">
          <div
            v-for="(plan, idx) in config.subscription_plans.plans"
            :key="idx"
            class="border border-border-dark rounded-xl p-4"
          >
            <div class="flex items-center justify-between mb-3">
              <span class="font-semibold text-ink-950">{{ plan.name || '新套餐' }}</span>
              <el-button v-if="plan.id !== 'free'" type="danger" size="small" text @click="removeSubscriptionPlan(idx)">
                <span class="material-symbols-outlined !text-lg">delete</span>
              </el-button>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label class="block text-xs text-ink-500 mb-1">套餐ID</label>
                <el-input v-model="plan.id" size="small" :disabled="plan.id === 'free'" />
              </div>
              <div>
                <label class="block text-xs text-ink-500 mb-1">套餐名称</label>
                <el-input v-model="plan.name" size="small" />
              </div>
              <div>
                <label class="block text-xs text-ink-500 mb-1">月价(元)</label>
                <el-input-number v-model="plan.monthly_price_yuan" :min="0" size="small" class="!w-full"
                  @change="v => { plan.monthly_price = Math.round(v * 100) }" />
              </div>
              <div>
                <label class="block text-xs text-ink-500 mb-1">年价(元)</label>
                <el-input-number v-model="plan.yearly_price_yuan" :min="0" size="small" class="!w-full"
                  @change="v => { plan.yearly_price = Math.round(v * 100) }" />
              </div>
              <div>
                <label class="block text-xs text-ink-500 mb-1">每月积分</label>
                <el-input-number v-model="plan.points_per_month" :min="0" size="small" class="!w-full" />
              </div>
              <div>
                <label class="block text-xs text-ink-500 mb-1">角标文字</label>
                <el-input v-model="plan.badge" size="small" placeholder="如: 最受欢迎" />
              </div>
              <div class="col-span-2">
                <label class="block text-xs text-ink-500 mb-1">功能特性 (每行一条)</label>
                <el-input
                  type="textarea"
                  :rows="2"
                  :model-value="plan.features?.join('\n')"
                  @update:model-value="v => plan.features = v.split('\n').filter(s => s.trim())"
                  size="small"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 模型定价 -->
      <div class="bg-white rounded-2xl shadow-sm border border-border-dark p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-ink-950 flex items-center gap-2">
            <span class="material-symbols-outlined !text-xl text-primary">auto_awesome</span>
            模型定价
          </h3>
          <el-button size="small" @click="addModelPricing">
            <span class="material-symbols-outlined !text-sm mr-1">add</span>
            添加模型
          </el-button>
        </div>

        <el-table :data="modelPricingList" border stripe>
          <el-table-column label="模型KEY" min-width="130">
            <template #default="{ row }">
              <el-input v-model="row.key" size="small" :disabled="row.key === 'default'" />
            </template>
          </el-table-column>
          <el-table-column label="显示名称" min-width="120">
            <template #default="{ row }">
              <el-input v-model="row.name" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="积分" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.points" :min="0" size="small" class="!w-full" />
            </template>
          </el-table-column>
          <el-table-column label="金额(分)" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.amount" :min="0" size="small" class="!w-full" />
            </template>
          </el-table-column>
          <el-table-column label="≈元" width="70" align="center">
            <template #default="{ row }">
              <span class="text-xs text-ink-500">¥{{ (row.amount / 100).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" align="center">
            <template #default="{ row, $index }">
              <el-button v-if="row.key !== 'default'" type="danger" size="small" text @click="removeModelPricing($index)">
                <span class="material-symbols-outlined !text-lg">delete</span>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分销配置 -->
      <div class="bg-white rounded-2xl shadow-sm border border-border-dark p-6">
        <h3 class="text-lg font-semibold text-ink-950 mb-4 flex items-center gap-2">
          <span class="material-symbols-outlined !text-xl text-primary">share</span>
          分销与限制
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1">邀请注册奖励积分</label>
            <el-input-number
              v-model="config.referral_config.register_reward_points"
              :min="0" :max="100000"
              class="!w-full"
            />
            <p class="text-xs text-ink-400 mt-1">双方各得此积分</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1">佣金比例(%)</label>
            <el-input-number
              v-model="config.referral_config.commission_rate"
              :min="0" :max="100"
              class="!w-full"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1">游客每日生成限制</label>
            <el-input-number
              v-model="config.limits.guest.daily_limit"
              :min="0" :max="1000"
              class="!w-full"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1">免费用户每日限制</label>
            <el-input-number
              v-model="config.limits.free_user.daily_limit"
              :min="0" :max="10000"
              class="!w-full"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1">订单超时(分钟)</label>
            <el-input-number
              v-model="config.limits.order_expire_minutes"
              :min="1" :max="1440"
              class="!w-full"
            />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/api'
import { ElMessage } from 'element-plus'

const config = ref(null)
const loading = ref(false)
const saving = ref(false)
const saveSuccess = ref(false)

// 模型定价转为列表方便编辑
const modelPricingList = computed({
  get() {
    if (!config.value?.model_pricing?.models) return []
    return Object.entries(config.value.model_pricing.models).map(([key, val]) => ({
      key,
      name: val.name || key,
      points: val.points || 0,
      amount: val.amount || 0,
      description: val.description || ''
    }))
  },
  set() {}
})

async function loadConfig() {
  loading.value = true
  try {
    const data = await api.getAdminBillingConfig()
    // 为订阅套餐添加元级别字段方便编辑
    if (data.subscription_plans?.plans) {
      data.subscription_plans.plans.forEach(p => {
        p.monthly_price_yuan = (p.monthly_price || 0) / 100
        p.yearly_price_yuan = (p.yearly_price || 0) / 100
      })
    }
    config.value = data
  } catch (err) {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  if (!config.value) return

  // 将模型定价列表写回到config
  const models = {}
  modelPricingList.value.forEach(m => {
    models[m.key] = {
      name: m.name,
      points: m.points,
      amount: m.amount,
      description: `${m.name}，消耗${m.points}积分或${(m.amount / 100).toFixed(2)}元`
    }
  })
  config.value.model_pricing.models = models

  // 确保订阅套餐价格是分
  config.value.subscription_plans.plans.forEach(p => {
    p.monthly_price = Math.round((p.monthly_price_yuan || 0) * 100)
    p.yearly_price = Math.round((p.yearly_price_yuan || 0) * 100)
    // 清理临时字段
    delete p.monthly_price_yuan
    delete p.yearly_price_yuan
  })

  saving.value = true
  try {
    await api.updateAdminBillingConfig(config.value)
    saveSuccess.value = true
    ElMessage.success('配置保存成功')
    // 重新加载以恢复编辑字段
    await loadConfig()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

function addRechargeOption() {
  const opts = config.value.recharge_options.options
  const nextId = `recharge_${opts.length + 1}`
  opts.push({
    id: nextId,
    name: '新充值选项',
    amount: 1000,
    amount_yuan: 10,
    points: 1000,
    bonus: 0,
    popular: false,
    description: ''
  })
}

function removeRechargeOption(idx) {
  config.value.recharge_options.options.splice(idx, 1)
}

function addSubscriptionPlan() {
  config.value.subscription_plans.plans.push({
    id: `plan_${Date.now()}`,
    name: '新套餐',
    icon: 'star',
    badge: '',
    monthly_price: 0,
    yearly_price: 0,
    monthly_price_yuan: 0,
    yearly_price_yuan: 0,
    points_per_month: 0,
    features: [],
    color: 'blue'
  })
}

function removeSubscriptionPlan(idx) {
  config.value.subscription_plans.plans.splice(idx, 1)
}

function addModelPricing() {
  const key = `model_${Date.now()}`
  config.value.model_pricing.models[key] = {
    name: '新模型',
    points: 10,
    amount: 10,
    description: ''
  }
  // 触发响应式更新
  config.value.model_pricing = { ...config.value.model_pricing }
}

function removeModelPricing(idx) {
  const item = modelPricingList.value[idx]
  if (item) {
    delete config.value.model_pricing.models[item.key]
    config.value.model_pricing = { ...config.value.model_pricing }
  }
}

onMounted(() => {
  loadConfig()
})
</script>
