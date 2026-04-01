<template>
  <main class="flex h-full min-h-0 flex-1 flex-col overflow-y-auto bg-background-dark">
    <!-- Header -->
    <div class="px-4 pt-8 pb-4 text-center xs:px-6 md:px-8 md:pt-12">
      <h1 class="text-2xl font-bold text-ink-950 md:text-3xl">选择适合你的套餐</h1>
      <p class="mt-2 text-sm text-ink-500">灵活的定价方案，满足不同创作需求</p>
    </div>

    <!-- Billing toggle -->
    <div class="flex items-center justify-center gap-2 pb-6">
      <button
        @click="billingCycle = 'monthly'"
        :class="[
          'rounded-full px-5 py-2 text-sm font-medium transition',
          billingCycle === 'monthly' ? 'bg-primary text-white shadow' : 'bg-white/80 text-ink-700 hover:bg-white'
        ]"
      >
        按月
      </button>
      <button
        @click="billingCycle = 'yearly'"
        :class="[
          'rounded-full px-5 py-2 text-sm font-medium transition',
          billingCycle === 'yearly' ? 'bg-primary text-white shadow' : 'bg-white/80 text-ink-700 hover:bg-white'
        ]"
      >
        按年
        <span class="ml-1 rounded-full bg-green-500 px-1.5 py-0.5 text-[10px] text-white">省钱</span>
      </button>
    </div>

    <!-- Plans grid -->
    <div class="mx-auto w-full max-w-[1000px] px-4 pb-8 xs:px-6 md:px-8">
      <!-- Mobile: horizontal scroll -->
      <div class="flex gap-4 overflow-x-auto pb-4 snap-x snap-mandatory md:grid md:grid-cols-4 md:overflow-visible md:pb-0 scrollbar-hide">
        <div
          v-for="plan in plans"
          :key="plan.id"
          :class="[
            'group relative flex min-w-[260px] flex-shrink-0 snap-center flex-col overflow-hidden rounded-3xl border-2 p-6 transition-all md:min-w-0',
            plan.badge
              ? 'border-primary bg-white shadow-xl'
              : 'border-border-dark bg-white/80 hover:shadow-lg'
          ]"
        >
          <!-- Badge -->
          <div v-if="plan.badge" class="absolute -top-0 left-1/2 -translate-x-1/2">
            <span class="rounded-b-xl bg-primary px-4 py-1 text-xs font-bold text-white shadow">
              {{ plan.badge }}
            </span>
          </div>

          <!-- Decorative circle -->
          <div :class="['absolute -top-8 -right-8 h-24 w-24 rounded-full opacity-10', colorBg(plan.color)]"></div>

          <!-- Icon -->
          <div :class="['mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl', colorBg(plan.color)]">
            <span class="material-symbols-outlined !text-2xl text-white">{{ plan.icon }}</span>
          </div>

          <!-- Name -->
          <h3 class="text-center text-lg font-bold text-ink-950">{{ plan.name }}</h3>

          <!-- Price -->
          <div class="mt-4 text-center">
            <template v-if="plan.monthly_price === 0">
              <span class="text-4xl font-extrabold text-ink-950">免费</span>
            </template>
            <template v-else>
              <span class="text-sm text-ink-500">¥</span>
              <span class="text-4xl font-extrabold text-ink-950">
                {{ billingCycle === 'monthly' ? (plan.monthly_price / 100) : (plan.yearly_price / 100) }}
              </span>
              <span class="text-sm text-ink-500">/{{ billingCycle === 'monthly' ? '月' : '年' }}</span>
            </template>
          </div>

          <!-- Beans per month -->
          <div class="mt-2 text-center text-sm text-ink-500">
            {{ plan.points_per_month }} 积分/月
          </div>

          <!-- Yearly savings -->
          <div v-if="billingCycle === 'yearly' && plan.monthly_price > 0" class="mt-1 text-center text-xs text-green-600">
            相当于 ¥{{ (plan.yearly_price / 1200).toFixed(0) }}/月，节省 ¥{{ ((plan.monthly_price * 12 - plan.yearly_price) / 100).toFixed(0) }}
          </div>

          <!-- Divider -->
          <div class="my-5 border-t border-border-dark"></div>

          <!-- Features -->
          <ul class="flex-1 space-y-2.5">
            <li v-for="(feat, i) in plan.features" :key="i" class="flex items-start gap-2 text-sm text-ink-700">
              <span :class="['material-symbols-outlined !text-base mt-0.5', colorText(plan.color)]">check_circle</span>
              <span>{{ feat }}</span>
            </li>
          </ul>

          <!-- CTA -->
          <button
            @click="selectPlan(plan)"
            :class="[
              'mt-6 w-full rounded-2xl py-3 text-sm font-semibold transition',
              plan.badge
                ? 'bg-primary text-white hover:bg-primary-strong shadow-md'
                : 'border border-border-dark bg-white text-ink-950 hover:border-primary/30 hover:shadow'
            ]"
          >
            {{ plan.monthly_price === 0 ? '免费开始' : '立即订阅' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Recharge options -->
    <div class="mx-auto w-full max-w-[800px] px-4 pb-8 xs:px-6 md:px-8">
      <div class="mb-4 text-center">
        <h2 class="text-xl font-bold text-ink-950">积分充值</h2>
        <p class="mt-1 text-sm text-ink-500">直接购买积分，按需使用</p>
      </div>

      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <button
          v-for="opt in rechargeOptions"
          :key="opt.id"
          @click="selectRecharge(opt)"
          :class="[
            'relative rounded-2xl border-2 p-4 text-center transition hover:shadow-md',
            opt.popular
              ? 'border-primary bg-primary/5'
              : 'border-border-dark bg-white/80 hover:border-primary/30'
          ]"
        >
          <div v-if="opt.popular" class="absolute -top-2.5 left-1/2 -translate-x-1/2">
            <span class="rounded-full bg-primary px-2.5 py-0.5 text-[10px] font-bold text-white">热门</span>
          </div>
          <div class="text-2xl font-bold text-ink-950">¥{{ opt.amount_yuan }}</div>
          <div class="mt-1 text-sm text-primary font-semibold">{{ opt.points }} 积分</div>
          <div v-if="opt.bonus > 0" class="mt-0.5 text-xs text-green-600">赠送 {{ opt.bonus }}</div>
        </button>
      </div>
    </div>

    <!-- Info section -->
    <div class="mx-auto w-full max-w-[600px] px-4 pb-12 xs:px-6">
      <div class="rounded-2xl border border-border-dark bg-white/80 p-5">
        <h3 class="mb-3 text-sm font-bold text-ink-950">计费说明</h3>
        <ul class="space-y-2 text-xs text-ink-700">
          <li class="flex items-start gap-2">
            <span class="material-symbols-outlined !text-sm text-primary mt-0.5">info</span>
            <span>积分仅用于生图，对话不消耗积分，1元 = 100积分</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="material-symbols-outlined !text-sm text-primary mt-0.5">info</span>
            <span>不同模型消耗不同积分，仅在生成成功时扣费，失败自动退还</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="material-symbols-outlined !text-sm text-primary mt-0.5">info</span>
            <span>新用户赠送100临时积分，每日签到获得40永久积分</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="material-symbols-outlined !text-sm text-primary mt-0.5">info</span>
            <span>邀请好友注册，双方各得50积分；好友消费，您获得15%佣金</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Payment dialog -->
    <el-dialog v-model="showPayment" title="充值支付" width="min(420px, 90vw)" align-center>
      <div v-if="paymentOrder" class="space-y-4 text-center">
        <p class="text-lg font-bold text-ink-950">
          支付 ¥{{ paymentOrder.amount_yuan }}
        </p>
        <p class="text-sm text-ink-500">获得 {{ paymentOrder.points }} 积分</p>

        <div v-if="paymentOrder.qr_code_url" class="flex justify-center py-4">
          <img :src="paymentOrder.qr_code_url" class="h-48 w-48 rounded-xl border" />
        </div>
        <p v-else class="py-8 text-ink-500">正在生成支付二维码...</p>

        <div class="flex items-center justify-center gap-2 text-xs text-ink-500">
          <span class="material-symbols-outlined !text-sm">shield</span>
          安全支付 · 即时到账
        </div>

        <el-button @click="checkPaymentStatus" :loading="checkingPayment">
          我已支付
        </el-button>
      </div>
    </el-dialog>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/useAuthStore'
import api from '@/services/api'
import { notification } from '@/utils/notification'

const router = useRouter()
const authStore = useAuthStore()

const billingCycle = ref('monthly')
const showPayment = ref(false)
const paymentOrder = ref(null)
const checkingPayment = ref(false)

const plans = ref([
  {
    id: 'free', name: '免费版', icon: 'gift', badge: '',
    monthly_price: 0, yearly_price: 0, points_per_month: 3, color: 'emerald',
    features: ['多种图片类型', '多种图片风格', '多种图片尺寸', '支持1K/2K/4K清晰度']
  },
  {
    id: 'plus', name: 'Plus', icon: 'bolt', badge: '最受欢迎',
    monthly_price: 9900, yearly_price: 99900, points_per_month: 150, color: 'amber',
    features: ['免费版全部功能', '高峰期稳定通道', '专属用户社群', '优先客服支持']
  },
  {
    id: 'pro', name: 'Pro', icon: 'workspace_premium', badge: '畅用首选',
    monthly_price: 29900, yearly_price: 299900, points_per_month: 500, color: 'rose',
    features: ['Plus全部功能', '更多每月积分', '批量生成优先', '高级模型优先']
  },
  {
    id: 'max', name: 'Max', icon: 'diamond', badge: '超值推荐',
    monthly_price: 49900, yearly_price: 499900, points_per_month: 1000, color: 'red',
    features: ['Pro全部功能', '最多每月积分', '全部模型无限制', '1对1专属服务']
  }
])

const rechargeOptions = ref([
  { id: 'recharge_1', amount_yuan: 20, points: 2000, bonus: 0, popular: false },
  { id: 'recharge_2', amount_yuan: 50, points: 5500, bonus: 500, popular: true },
  { id: 'recharge_3', amount_yuan: 100, points: 12000, bonus: 2000, popular: false },
  { id: 'recharge_4', amount_yuan: 200, points: 26000, bonus: 6000, popular: false },
])

const colorBg = (color) => {
  const map = { emerald: 'bg-emerald-500', amber: 'bg-amber-500', rose: 'bg-rose-500', red: 'bg-primary' }
  return map[color] || 'bg-primary'
}

const colorText = (color) => {
  const map = { emerald: 'text-emerald-500', amber: 'text-amber-500', rose: 'text-rose-500', red: 'text-primary' }
  return map[color] || 'text-primary'
}

const selectPlan = (plan) => {
  if (plan.monthly_price === 0) {
    router.push('/')
    return
  }
  if (!authStore.isAuthenticated) {
    router.push('/login')
    notification.warning('请先登录', '登录后即可订阅套餐')
    return
  }
  // TODO: Create subscription order via API
  notification.info('即将上线', '套餐订阅功能即将上线，敬请期待')
}

const selectRecharge = async (opt) => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    notification.warning('请先登录', '登录后即可充值')
    return
  }
  try {
    const order = await api.createRechargeOrder(opt.id, 'wechat')
    paymentOrder.value = { ...opt, ...order }
    showPayment.value = true
  } catch (err) {
    notification.error('创建订单失败', err?.response?.data?.detail || '请稍后重试')
  }
}

const checkPaymentStatus = async () => {
  if (!paymentOrder.value?.order_id) return
  checkingPayment.value = true
  try {
    const status = await api.getPaymentOrderStatus(paymentOrder.value.order_id)
    if (status.status === 'paid') {
      notification.success('充值成功', `${paymentOrder.value.points} 积分已到账`)
      showPayment.value = false
      paymentOrder.value = null
    } else {
      notification.warning('暂未到账', '请稍等片刻后再试')
    }
  } catch {
    notification.error('查询失败', '请稍后重试')
  } finally {
    checkingPayment.value = false
  }
}

onMounted(async () => {
  // Load plans and recharge options from API if available
  try {
    const config = await api.getBillingConfig()
    if (config?.subscription_plans?.plans?.length > 0) {
      plans.value = config.subscription_plans.plans
    }
    if (config?.recharge_options?.options?.length > 0) {
      rechargeOptions.value = config.recharge_options.options
    }
  } catch {
    // Use defaults
  }
})
</script>

<style scoped>
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
