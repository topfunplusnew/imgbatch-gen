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
      <div class="flex gap-4 overflow-x-auto pb-4 snap-x snap-mandatory md:grid md:grid-cols-4 md:overflow-visible md:pb-0 scrollbar-hide">
        <div
          v-if="plans.length === 0"
          class="w-full rounded-3xl border border-dashed border-border-dark bg-white/70 px-6 py-10 text-center text-sm text-ink-500 md:col-span-4"
        >
          {{ pricingLoadFailed ? pricingErrorMessage : (pricingDataLoaded ? '暂无订阅套餐配置' : '正在加载套餐配置...') }}
        </div>
        <div
          v-for="plan in plans"
          :key="plan.id"
          :class="[
            'group relative flex min-w-[260px] flex-shrink-0 snap-center flex-col overflow-hidden rounded-3xl border-2 p-6 transition-all md:min-w-0',
            plan.badge
              ? 'border-primary bg-white shadow-xl -translate-y-1'
              : 'border-border-dark bg-white/90 shadow-sm hover:shadow-xl hover:-translate-y-1'
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

    <!-- Model pricing -->
    <div class="mx-auto w-full max-w-[1000px] px-4 pb-8 xs:px-6 md:px-8">
      <div class="mb-4 text-center">
        <h2 class="text-xl font-bold text-ink-950">模型定价</h2>
        <p class="mt-1 text-sm text-ink-500">以下价格来自后台产品定价配置，按模型实际消耗展示</p>
      </div>

      <div class="overflow-hidden rounded-3xl border border-border-dark bg-white/90 shadow-sm">
        <div class="hidden grid-cols-[minmax(0,2fr)_100px_120px] gap-4 border-b border-border-dark bg-background-dark/40 px-5 py-3 text-xs font-semibold text-ink-500 md:grid">
          <span>模型</span>
          <span>积分</span>
          <span>金额</span>
        </div>

        <div
          v-if="modelPrices.length === 0"
          class="px-6 py-10 text-center text-sm text-ink-500"
        >
          {{ modelPricingLoadFailed ? modelPricingErrorMessage : (modelPricingLoaded ? '暂无模型定价配置' : '正在加载模型定价...') }}
        </div>

        <div
          v-for="model in modelPrices"
          :key="model.model_name"
          class="border-b border-border-dark/70 px-5 py-4 last:border-b-0"
        >
          <div class="grid gap-3 md:grid-cols-[minmax(0,2fr)_100px_120px] md:items-center">
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-ink-950">{{ model.display_name }}</p>
              <p class="mt-1 break-all text-xs text-ink-500">{{ model.model_name }}</p>
            </div>
            <div class="text-sm font-medium text-primary">
              {{ model.points }} 积分
            </div>
            <div class="text-sm text-ink-700">
              ¥{{ model.amount_yuan.toFixed(2) }}
            </div>
          </div>
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
          v-if="rechargeOptions.length === 0"
          type="button"
          disabled
          class="col-span-2 rounded-2xl border border-dashed border-border-dark bg-white/70 px-4 py-8 text-center text-sm text-ink-500 md:col-span-4"
        >
          {{ pricingLoadFailed ? pricingErrorMessage : (pricingDataLoaded ? '暂无积分充值配置' : '正在加载充值选项...') }}
        </button>
        <button
          v-for="opt in rechargeOptions"
          :key="opt.id"
          @click="selectRecharge(opt)"
          :class="[
            'relative rounded-2xl border-2 p-4 text-center transition hover:shadow-md',
            opt.popular
              ? 'border-primary bg-primary/5 shadow-md'
              : 'border-border-dark bg-white/90 shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:border-primary/30'
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
    <el-dialog v-model="showPayment" :title="paymentDialogTitle" width="min(420px, 90vw)" align-center @close="stopPolling">
      <div v-if="paymentOrder" class="space-y-4 text-center">
        <p class="text-sm font-medium text-primary">
          {{ paymentOrder.subject }}
        </p>
        <p class="text-lg font-bold text-ink-950">
          支付 ¥{{ paymentOrder.amount_yuan }}
        </p>
        <p class="text-sm text-ink-500">{{ paymentOrder.display_description }}</p>

        <!-- PC: QR code -->
        <div v-if="!isMobile" class="flex flex-col items-center gap-3 py-4">
          <div v-if="qrCodeDataUrl" class="rounded-xl border border-border-dark p-2 bg-white">
            <img :src="qrCodeDataUrl" class="h-48 w-48" />
          </div>
          <p v-else class="py-8 text-ink-500">正在生成支付二维码...</p>
          <p class="text-xs text-ink-500">请使用微信扫码支付，支付成功后系统会自动刷新结果</p>
        </div>

        <!-- Mobile: redirect button -->
        <div v-else class="py-6">
          <p v-if="paymentOrder.pay_url" class="mb-4 text-sm text-ink-500">点击下方按钮跳转微信支付</p>
          <p v-else class="mb-4 text-sm text-ink-500">正在创建支付订单...</p>
          <el-button
            v-if="paymentOrder.pay_url"
            type="primary"
            size="large"
            round
            @click="goToH5Pay"
          >
            <span class="material-symbols-outlined !text-lg mr-1">payment</span>
            去微信支付
          </el-button>
        </div>

        <div class="flex items-center justify-center gap-2 text-xs text-ink-500">
          <span class="material-symbols-outlined !text-sm">shield</span>
          安全支付 · 即时到账
        </div>

        <div class="flex justify-center gap-3">
          <el-button @click="checkPaymentStatus" :loading="checkingPayment">
            我已支付
          </el-button>
          <el-button @click="showPayment = false">取消</el-button>
        </div>

        <p v-if="pollingActive" class="text-xs text-ink-400">正在自动查询支付结果...</p>
      </div>
    </el-dialog>
  </main>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/useAuthStore'
import QRCode from 'qrcode'
import { api } from '@/services/api'
import { notification } from '@/utils/notification'

const router = useRouter()
const authStore = useAuthStore()

const billingCycle = ref('monthly')
const showPayment = ref(false)
const paymentOrder = ref(null)
const checkingPayment = ref(false)
const qrCodeDataUrl = ref('')
const pollingTimer = ref(null)
const pollingActive = ref(false)
const pricingDataLoaded = ref(false)
const pricingLoadFailed = ref(false)
const pricingErrorMessage = ref('暂未加载到定价数据')
const modelPricingLoaded = ref(false)
const modelPricingLoadFailed = ref(false)
const modelPricingErrorMessage = ref('暂未加载到模型定价')

const isMobile = computed(() => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
})

const plans = ref([])
const modelPrices = ref([])
const rechargeOptions = ref([])
const paymentDialogTitle = computed(() => (
  paymentOrder.value?.order_type === 'subscription' ? '套餐订阅支付' : '充值支付'
))

const getErrorMessage = (error, fallback = '请稍后刷新重试') => {
  return error?.response?.data?.detail || error?.message || fallback
}

const colorBg = (color) => {
  const map = { emerald: 'bg-emerald-500', amber: 'bg-amber-500', rose: 'bg-rose-500', red: 'bg-primary' }
  return map[color] || 'bg-primary'
}

const colorText = (color) => {
  const map = { emerald: 'text-emerald-500', amber: 'text-amber-500', rose: 'text-rose-500', red: 'text-primary' }
  return map[color] || 'text-primary'
}

const buildRechargePaymentMeta = (opt) => {
  const totalPoints = Number(opt.points || 0) + Number(opt.bonus || 0)
  const bonusText = opt.bonus > 0 ? `，含赠送 ${opt.bonus} 积分` : ''
  return {
    display_description: `支付成功后到账 ${totalPoints} 积分${bonusText}`,
    success_title: '充值成功',
    success_message: `${totalPoints} 积分已到账`
  }
}

const buildSubscriptionPaymentMeta = (plan) => {
  const cycle = billingCycle.value === 'yearly' ? 'yearly' : 'monthly'
  const cycleLabel = cycle === 'yearly' ? '年付' : '月付'
  const selectedAmount = cycle === 'yearly'
    ? Number(plan.yearly_price || 0)
    : Number(plan.monthly_price || 0)
  const pointsIncluded = cycle === 'yearly'
    ? Number(plan.points_per_month || 0) * 12
    : Number(plan.points_per_month || 0)

  return {
    cycle,
    cycle_label: cycleLabel,
    selected_amount: selectedAmount,
    points_included: pointsIncluded,
    display_description: pointsIncluded > 0
      ? `支付成功后开通 ${plan.name}${cycleLabel}，赠送 ${pointsIncluded} 积分`
      : `支付成功后开通 ${plan.name}${cycleLabel}`,
    success_title: '订阅成功',
    success_message: `${plan.name}${cycleLabel}已开通`
  }
}

const handlePaymentSuccess = async () => {
  const currentOrder = paymentOrder.value
  if (!currentOrder) return

  stopPolling()
  showPayment.value = false
  paymentOrder.value = null
  qrCodeDataUrl.value = ''

  if (authStore.isAuthenticated) {
    try {
      await authStore.fetchAccountInfo()
    } catch (error) {
      console.error('刷新账户信息失败:', error)
    }
  }

  notification.success(
    currentOrder.success_title || '支付成功',
    currentOrder.success_message || '订单支付成功'
  )
}

const openPaymentFlow = async ({ createNativeOrder, createH5Order, meta }) => {
  try {
    qrCodeDataUrl.value = ''

    const order = isMobile.value
      ? await createH5Order(await getClientIp())
      : await createNativeOrder()

    paymentOrder.value = { ...order, ...meta }
    showPayment.value = true

    if (!isMobile.value && order.qr_code_url) {
      try {
        qrCodeDataUrl.value = await QRCode.toDataURL(order.qr_code_url, {
          width: 256,
          margin: 2,
          color: { dark: '#000000', light: '#ffffff' }
        })
      } catch (error) {
        console.error('QR code generation failed:', error)
      }
    }

    startPolling()
  } catch (error) {
    notification.error('创建订单失败', getErrorMessage(error))
  }
}

const selectPlan = async (plan) => {
  if (Number(plan.monthly_price || 0) === 0 && Number(plan.yearly_price || 0) === 0) {
    router.push('/')
    return
  }
  if (!authStore.isAuthenticated) {
    router.push('/login')
    notification.warning('请先登录', '登录后即可订阅套餐')
    return
  }

  const meta = buildSubscriptionPaymentMeta(plan)
  if (meta.selected_amount <= 0) {
    notification.info('暂不可用', `${plan.name}暂未配置${meta.cycle_label}价格`)
    return
  }

  await openPaymentFlow({
    meta,
    createNativeOrder: () => api.createSubscriptionOrder(plan.id, meta.cycle, 'wechat'),
    createH5Order: (clientIp) => api.createH5SubscriptionOrder(plan.id, meta.cycle, clientIp)
  })
}

const selectRecharge = async (opt) => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    notification.warning('请先登录', '登录后即可充值')
    return
  }

  await openPaymentFlow({
    meta: buildRechargePaymentMeta(opt),
    createNativeOrder: () => api.createRechargeOrder(opt.id, 'wechat'),
    createH5Order: (clientIp) => api.createH5RechargeOrder(opt.id, clientIp)
  })
}

const getClientIp = async () => {
  try {
    const resp = await fetch('https://api.ipify.org?format=json')
    const data = await resp.json()
    return data.ip
  } catch {
    return '127.0.0.1'
  }
}

const goToH5Pay = () => {
  if (paymentOrder.value?.pay_url) {
    window.location.href = paymentOrder.value.pay_url
  }
}

const startPolling = () => {
  stopPolling()
  pollingActive.value = true
  pollingTimer.value = setInterval(async () => {
    if (!paymentOrder.value?.order_id) return
    try {
      const status = await api.getOrderStatus(paymentOrder.value.order_id)
      if (status.status === 'paid') {
        await handlePaymentSuccess()
      }
    } catch {
      // ignore polling errors
    }
  }, 3000)
}

const stopPolling = () => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
  pollingActive.value = false
}

const checkPaymentStatus = async () => {
  if (!paymentOrder.value?.order_id) return
  checkingPayment.value = true
  try {
    const status = await api.getOrderStatus(paymentOrder.value.order_id)
    if (status.status === 'paid') {
      await handlePaymentSuccess()
    } else {
      notification.warning('暂未到账', '如已支付请稍等片刻，系统会自动确认')
    }
  } catch {
    notification.error('查询失败', '请稍后重试')
  } finally {
    checkingPayment.value = false
  }
}

onUnmounted(() => {
  stopPolling()
})

const loadPricingData = async () => {
  pricingDataLoaded.value = false
  pricingLoadFailed.value = false
  pricingErrorMessage.value = '暂未加载到定价数据'
  modelPricingLoaded.value = false
  modelPricingLoadFailed.value = false
  modelPricingErrorMessage.value = '暂未加载到模型定价'

  let nextPlans = []
  let nextModelPrices = []
  let nextRechargeOptions = []
  let lastError = null

  try {
    const config = await api.getBillingConfig()
    nextPlans = config?.subscription_plans?.plans || []
    nextRechargeOptions = config?.recharge_options?.options || []
  } catch (error) {
    console.error('加载计费配置失败:', error)
    lastError = error
  }

  const [plansResult, modelPricingResult, rechargeResult] = await Promise.allSettled([
    nextPlans.length > 0 ? Promise.resolve(nextPlans) : api.getSubscriptionPlans(),
    api.getModelPricing(),
    nextRechargeOptions.length > 0 ? Promise.resolve(nextRechargeOptions) : api.getRechargeOptions()
  ])

  if (plansResult.status === 'fulfilled') {
    nextPlans = plansResult.value || []
  } else {
    console.error('加载订阅套餐失败:', plansResult.reason)
    lastError = plansResult.reason
  }

  if (modelPricingResult.status === 'fulfilled') {
    nextModelPrices = modelPricingResult.value || []
  } else {
    console.error('加载模型定价失败:', modelPricingResult.reason)
    modelPricingLoadFailed.value = true
    modelPricingErrorMessage.value = `模型定价加载失败：${getErrorMessage(modelPricingResult.reason, '请稍后刷新重试')}`
  }

  if (rechargeResult.status === 'fulfilled') {
    nextRechargeOptions = rechargeResult.value || []
  } else {
    console.error('加载充值选项失败:', rechargeResult.reason)
    lastError = rechargeResult.reason
  }

  plans.value = nextPlans
  modelPrices.value = nextModelPrices
  rechargeOptions.value = nextRechargeOptions
  pricingDataLoaded.value = true
  modelPricingLoaded.value = true

  if (plans.value.length === 0 && rechargeOptions.value.length === 0) {
    pricingLoadFailed.value = true
    pricingErrorMessage.value = `定价数据加载失败：${getErrorMessage(lastError, '请检查 API 地址或后端服务是否已更新')}`
    notification.error('定价数据加载失败', getErrorMessage(lastError, '请检查接口地址配置'))
  }
}

onMounted(async () => {
  await loadPricingData()
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
