<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航 -->
    <header class="bg-white/80 backdrop-blur-xl shadow-sm border-b border-border-dark sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <h1 class="text-xl font-bold text-ink-950">账户中心</h1>
        <button
          @click="goHome"
          class="text-sm text-primary hover:text-primary-strong font-medium"
        >
          返回首页
        </button>
      </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 py-8">
      <div class="flex flex-col md:flex-row gap-6">
        <!-- 左侧导航栏 -->
        <aside class="w-full md:w-56 lg:w-64 shrink-0">
          <nav class="bg-white rounded-2xl shadow-sm p-2 space-y-1 md:sticky md:top-24">
            <button
              @click="appStore.setUserCenterTab('account')"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium transition-colors flex items-center gap-3',
                activeTab === 'account'
                  ? 'bg-primary text-white'
                  : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">account_circle</span>
              账户
            </button>
            <button
              @click="appStore.setUserCenterTab('balance')"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium transition-colors flex items-center gap-3',
                activeTab === 'balance'
                  ? 'bg-primary text-white'
                  : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">account_balance_wallet</span>
              余额与充值
            </button>
            <button
              @click="appStore.setUserCenterTab('recharge')"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium transition-colors flex items-center gap-3',
                activeTab === 'recharge'
                  ? 'bg-primary text-white'
                  : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">receipt_long</span>
              充值记录
            </button>
            <button
              @click="appStore.setUserCenterTab('generation')"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium transition-colors flex items-center gap-3',
                activeTab === 'generation'
                  ? 'bg-primary text-white'
                  : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">image</span>
              生成历史
            </button>
            <button
              @click="appStore.setUserCenterTab('download')"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium transition-colors flex items-center gap-3',
                activeTab === 'download'
                  ? 'bg-primary text-white'
                  : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">download</span>
              下载记录
            </button>
            <button
              @click="appStore.setUserCenterTab('consumption')"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium transition-colors flex items-center gap-3',
                activeTab === 'consumption'
                  ? 'bg-primary text-white'
                  : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">receipt</span>
              消费记录
            </button>
            <button
              @click="appStore.setUserCenterTab('withdrawal')"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium transition-colors flex items-center gap-3',
                activeTab === 'withdrawal'
                  ? 'bg-primary text-white'
                  : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">payments</span>
              提现管理
            </button>
            <button
              @click="appStore.setUserCenterTab('invite')"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium transition-colors flex items-center gap-3',
                activeTab === 'invite'
                  ? 'bg-primary text-white'
                  : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">card_giftcard</span>
              邀请码
            </button>
            <button
              @click="appStore.setUserCenterTab('notifications')"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium transition-colors flex items-center gap-3',
                activeTab === 'notifications'
                  ? 'bg-primary text-white'
                  : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">notifications</span>
              通知中心
              <span
                v-if="notificationStore.unreadCount > 0"
                class="ml-auto bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center"
              >
                {{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}
              </span>
            </button>
          </nav>
        </aside>

        <!-- 右侧内容区 -->
        <main class="flex-1 min-w-0">
          <!-- 账户标签页 -->
          <div v-if="activeTab === 'account'" class="space-y-6">
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-lg font-bold text-ink-950">个人资料</h2>
                <div class="flex gap-3">
                  <button
                    @click="showUsernameModal = true"
                    class="text-sm text-primary hover:text-primary-strong font-medium"
                  >
                    修改用户名
                  </button>
                  <button
                    @click="showPasswordModal = true"
                    class="text-sm text-primary hover:text-primary-strong font-medium"
                  >
                    修改密码
                  </button>
                </div>
              </div>

              <div class="space-y-4">
                <div class="flex items-center gap-4">
                  <div class="w-16 h-16 bg-gradient-to-br from-primary to-primary-deep rounded-full flex items-center justify-center">
                    <span class="text-2xl font-bold text-white">{{ authStore.user?.username?.[0]?.toUpperCase() || 'U' }}</span>
                  </div>
                  <div>
                    <p class="font-semibold text-gray-900">{{ authStore.user?.username || '未设置' }}</p>
                  </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                  <div class="p-4 bg-gray-50 rounded-xl">
                    <p class="text-sm text-gray-500 mb-1">手机号</p>
                    <p class="font-medium text-gray-900">{{ authStore.user?.phone || '未绑定' }}</p>
                  </div>
                  <div class="p-4 bg-gray-50 rounded-xl">
                    <p class="text-sm text-gray-500 mb-1">邮箱</p>
                    <p class="font-medium text-gray-900">{{ authStore.user?.email || '未绑定' }}</p>
                  </div>
                  <div class="p-4 bg-gray-50 rounded-xl">
                    <p class="text-sm text-gray-500 mb-1">账户状态</p>
                    <p class="font-medium text-gray-900">{{ getStatusDisplay(authStore.user?.status) }}</p>
                  </div>
                  <div class="p-4 bg-gray-50 rounded-xl">
                    <p class="text-sm text-gray-500 mb-1">注册时间</p>
                    <p class="font-medium text-gray-900">{{ formatDate(authStore.user?.created_at) }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 每日签到 -->
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-lg font-bold text-ink-950">每日签到</h3>
                  <p class="text-sm text-gray-500 mt-1">签到可获得积分奖励</p>
                </div>
                <button
                  @click="handleDailyCheckin"
                  :disabled="!canCheckin || checkinLoading"
                  class="px-6 py-3 bg-gradient-to-r from-primary to-primary-deep text-white rounded-xl font-medium hover:from-primary-strong hover:to-primary-deep disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {{ checkinLoading ? '签到中...' : canCheckin ? '立即签到' : '今日已签到' }}
                </button>
              </div>
              <div v-if="checkinInfo.consecutive_days > 0" class="mt-4 flex items-center gap-2 text-sm text-gray-600">
                <span class="material-symbols-outlined !text-xl text-amber-500">local_fire_department</span>
                已连续签到 {{ checkinInfo.consecutive_days }} 天
              </div>
            </div>

            <!-- 消费统计 -->
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <h3 class="text-lg font-bold text-ink-950 mb-4">消费统计</h3>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="text-center">
                  <p class="text-3xl font-bold text-primary">{{ accountInfo?.total_generated || 0 }}</p>
                  <p class="text-sm text-gray-500 mt-1">生成图片数</p>
                </div>
                <div class="text-center">
                  <p class="text-3xl font-bold text-primary">¥{{ ((accountInfo?.total_spent || 0) / 100).toFixed(2) }}</p>
                  <p class="text-sm text-gray-500 mt-1">累计消费</p>
                </div>
                <div class="text-center">
                  <p class="text-3xl font-bold text-primary">{{ accountInfo?.total_points_earned || 0 }}</p>
                  <p class="text-sm text-gray-500 mt-1">累计获得积分</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 余额与充值标签页 -->
          <div v-if="activeTab === 'balance'" class="space-y-6">
            <!-- 余额卡片 -->
            <div class="bg-gradient-to-br from-primary to-primary-deep rounded-2xl shadow-lg p-6 text-white">
              <h2 class="text-lg font-semibold mb-6">账户余额</h2>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p class="text-sm opacity-80 mb-1">账户余额</p>
                  <p class="text-3xl font-bold">¥{{ ((accountInfo?.balance || 0) / 100).toFixed(2) }}</p>
                </div>
                <div>
                  <p class="text-sm opacity-80 mb-1">永久积分</p>
                  <p class="text-3xl font-bold">{{ accountInfo?.points || 0 }}</p>
                  <p class="text-xs opacity-70 mt-1">签到、邀请获得</p>
                </div>
                <div>
                  <p class="text-sm opacity-80 mb-1">临时积分</p>
                  <p class="text-3xl font-bold">{{ accountInfo?.gift_points || 0 }}</p>
                  <p v-if="accountInfo?.gift_points_expiry" class="text-xs opacity-70 mt-1">
                    {{ formatExpiryTime(accountInfo.gift_points_expiry) }} 过期
                  </p>
                  <p class="text-xs opacity-70">新用户赠送，每日清零</p>
                </div>
              </div>
            </div>

            <!-- 充值选项 -->
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <h2 class="text-lg font-bold text-ink-950 mb-6">充值</h2>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <button
                  v-for="option in rechargeOptions"
                  :key="option.id"
                  @click="selectedOption = option; showRechargeModal = true"
                  :class="[
                    'p-6 rounded-xl border-2 text-center transition-all relative',
                    'border-gray-200 hover:border-primary hover:bg-primary-soft'
                  ]"
                >
                  <p class="text-2xl font-bold text-gray-900 mb-2">¥{{ option.amount_yuan }}</p>
                  <p class="text-sm text-gray-600">
                    获得 {{ option.points }} 积分
                    <span v-if="option.bonus" class="text-green-600">+{{ option.bonus }} 赠送</span>
                  </p>
                  <span
                    v-if="option.popular"
                    class="absolute -top-2 -right-2 px-2 py-0.5 bg-gradient-to-r from-primary to-primary-deep text-white text-xs rounded-full"
                  >
                    热门
                  </span>
                </button>
              </div>
            </div>
          </div>

          <!-- 充值记录标签页 -->
          <div v-if="activeTab === 'recharge'" class="space-y-6">
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-lg font-bold text-ink-950">充值记录</h2>
                <span class="text-sm text-gray-500">共 {{ orders.length }} 条记录</span>
              </div>

              <div v-if="orders.length === 0" class="text-center py-12">
                <span class="material-symbols-outlined !text-6xl text-gray-300">receipt_long</span>
                <p class="text-gray-500 mt-4">暂无充值记录</p>
                <button
                  @click="activeTab = 'balance'"
                  class="mt-4 px-6 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-strong"
                >
                  立即充值
                </button>
              </div>

              <div v-else class="space-y-4">
                <div
                  v-for="order in orders"
                  :key="order.order_id"
                  class="p-4 border border-gray-200 rounded-xl hover:border-gray-300 transition-colors"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex-1">
                      <div class="flex items-center gap-3">
                        <p class="font-semibold text-gray-900">¥{{ order.amount_yuan }}</p>
                        <span
                          :class="[
                            'px-2 py-0.5 text-xs rounded-full',
                            order.status === 'paid' ? 'bg-green-100 text-green-700' :
                            order.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                            order.status === 'cancelled' ? 'bg-gray-100 text-gray-700' :
                            'bg-red-100 text-red-700'
                          ]"
                        >
                          {{ getStatusText(order.status) }}
                        </span>
                      </div>
                      <p class="text-sm text-gray-500 mt-1">
                        {{ order.payment_method === 'wechat' ? '微信支付' : '支付宝' }} · {{ formatDate(order.created_at) }}
                      </p>
                    </div>
                    <div class="flex items-center gap-2">
                      <button
                        v-if="order.status === 'pending'"
                        @click="continuePay(order)"
                        class="px-4 py-2 text-sm text-primary hover:bg-primary-soft rounded-lg font-medium"
                      >
                        继续支付
                      </button>
                      <button
                        v-if="order.status === 'pending'"
                        @click="cancelOrder(order.order_id)"
                        class="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg font-medium"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 生成历史标签页 -->
          <div v-if="activeTab === 'generation'" class="space-y-6">
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-lg font-bold text-ink-950">生成历史</h2>
                <div class="flex items-center gap-3">
                  <select
                    v-model="generationFilter.status"
                    @change="currentPage = 0; loadGenerationHistory()"
                    class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary"
                  >
                    <option value="">全部状态</option>
                    <option value="completed">成功</option>
                    <option value="failed">失败</option>
                  </select>
                </div>
              </div>

              <div v-if="generationRecords.length === 0" class="text-center py-12">
                <span class="material-symbols-outlined !text-6xl text-gray-300">image</span>
                <p class="text-gray-500 mt-4">暂无生成记录</p>
                <button
                  @click="goHome"
                  class="mt-4 px-6 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-strong"
                >
                  开始生成
                </button>
              </div>

              <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div
                  v-for="record in generationRecords"
                  :key="record.id"
                  class="bg-gray-50 rounded-xl overflow-hidden hover:shadow-md transition-shadow relative"
                >
                  <!-- 类型徽章 -->
                  <div class="absolute top-2 left-2 z-10">
                    <span
                      v-if="record.type === 'async'"
                      class="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full"
                    >
                      异步
                    </span>
                    <span
                      v-else-if="record.type === 'chat'"
                      class="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full"
                    >
                      对话
                    </span>
                    <span
                      v-else
                      class="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full"
                    >
                      历史记录
                    </span>
                  </div>

                  <!-- 图片预览 -->
                  <div class="aspect-square bg-gray-200 relative group">
                    <img
                      v-if="record.image_urls && record.image_urls.length > 0"
                      :src="resolveImageSrc(record.image_urls[0])"
                      :alt="record.prompt"
                      class="w-full h-full object-cover"
                      @error="handleImageFallback"
                    />
                    <div v-else class="w-full h-full flex items-center justify-center">
                      <span class="material-symbols-outlined !text-6xl text-gray-400">image_not_supported</span>
                    </div>
                    <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <button
                        @click="viewGenerationDetail(record)"
                        class="px-4 py-2 bg-white text-gray-900 rounded-lg font-medium"
                      >
                        查看详情
                      </button>
                    </div>
                  </div>

                  <!-- 信息 -->
                  <div class="p-4">
                    <p class="text-sm text-gray-600 line-clamp-2 mb-2">{{ record.prompt }}</p>
                    <div class="flex items-center justify-between">
                      <span class="text-xs text-gray-500">{{ record.model }}</span>
                      <span class="text-xs text-gray-500">{{ formatDate(record.created_at) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 分页控制 -->
              <div v-if="totalCount > pageSize" class="mt-6 flex items-center justify-between">
                <span class="text-sm text-gray-600">共 {{ totalCount }} 条记录</span>
                <div class="flex items-center gap-2">
                  <button
                    @click="currentPage--; loadGenerationHistory()"
                    :disabled="currentPage === 0"
                    class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    上一页
                  </button>
                  <span class="text-sm text-gray-600">
                    第 {{ currentPage + 1 }} 页，共 {{ Math.ceil(totalCount / pageSize) }} 页
                  </span>
                  <button
                    @click="currentPage++; loadGenerationHistory()"
                    :disabled="currentPage >= Math.ceil(totalCount / pageSize) - 1"
                    class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    下一页
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 下载记录标签页 -->
          <div v-if="activeTab === 'download'" class="space-y-6">
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-lg font-bold text-ink-950">下载记录</h2>
                <span class="text-sm text-gray-500">共 {{ downloadRecords.length }} 条记录</span>
              </div>

              <div v-if="downloadRecords.length === 0" class="text-center py-12">
                <span class="material-symbols-outlined !text-6xl text-gray-300">download</span>
                <p class="text-gray-500 mt-4">暂无下载记录</p>
              </div>

              <div v-else class="space-y-4">
                <div
                  v-for="record in downloadRecords"
                  :key="record.id"
                  class="flex items-center gap-4 p-4 border border-gray-200 rounded-xl hover:border-gray-300 transition-colors"
                >
                  <div class="w-16 h-16 bg-gray-200 rounded-lg overflow-hidden shrink-0">
                    <img
                      :src="resolveImageSrc(record.image_url)"
                      :alt="record.file_name"
                      class="w-full h-full object-cover"
                      @error="handleImageFallback"
                    />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="font-medium text-gray-900 truncate">{{ record.file_name }}</p>
                    <p class="text-sm text-gray-500">{{ formatFileSize(record.file_size) }}</p>
                  </div>
                  <div class="text-right shrink-0">
                    <p class="text-sm text-gray-500">{{ formatDate(record.created_at) }}</p>
                    <a
                      :href="record.image_url"
                      :download="record.file_name"
                      class="text-sm text-primary hover:text-primary-strong font-medium"
                    >
                      重新下载
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 消费记录标签页 -->
          <div v-if="activeTab === 'consumption'" class="space-y-6">
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-lg font-bold text-ink-950">消费记录</h2>
                <div class="flex items-center gap-2">
                  <select
                    v-model="consumptionFilter"
                    class="px-3 py-2 border border-border-dark rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="all">全部记录</option>
                    <option value="success">成功</option>
                    <option value="failed">失败</option>
                    <option value="points">积分扣费</option>
                    <option value="balance">余额扣费</option>
                  </select>
                </div>
              </div>

              <!-- 加载状态 -->
              <div v-if="authStore.consumptionLoading && authStore.consumptionRecords.length === 0" class="text-center py-12">
                <span class="material-symbols-outlined animate-spin text-4xl text-primary">loading</span>
                <p class="text-gray-500 mt-2">加载中...</p>
              </div>

              <!-- 错误状态 -->
              <div v-else-if="authStore.consumptionError && authStore.consumptionRecords.length === 0" class="text-center py-12">
                <span class="material-symbols-outlined text-4xl text-red-500">error</span>
                <p class="text-red-500 mt-2">{{ authStore.consumptionError }}</p>
                <button
                  @click="loadConsumptionRecords"
                  class="mt-4 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-deep"
                >
                  重试
                </button>
              </div>

              <!-- 空状态 -->
              <div v-else-if="filteredConsumptionRecords.length === 0" class="text-center py-12">
                <span class="material-symbols-outlined text-4xl text-gray-300">receipt</span>
                <p class="text-gray-400 mt-2">暂无消费记录</p>
              </div>

              <!-- 消费记录列表 -->
              <div v-else class="space-y-3">
                <div
                  v-for="record in filteredConsumptionRecords"
                  :key="record.id"
                  class="border border-border-dark rounded-xl p-4 hover:border-primary transition-colors"
                  :class="{
                    'border-l-4 border-l-red-500': record.status === 'failed',
                    'border-l-4 border-l-green-500': record.status === 'success'
                  }"
                >
                  <!-- 头部：模型和时间 -->
                  <div class="flex items-start justify-between mb-3">
                    <div class="flex-1">
                      <div class="flex items-center gap-2">
                        <h3 class="font-semibold text-ink-950">{{ record.model_name }}</h3>
                        <span
                          class="px-2 py-0.5 text-xs rounded-full"
                          :class="{
                            'bg-green-100 text-green-700': record.status === 'success',
                            'bg-red-100 text-red-700': record.status === 'failed'
                          }"
                        >
                          {{ record.status === 'success' ? '成功' : '失败' }}
                        </span>
                        <span class="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                          {{ getCostTypeDisplay(record.cost_type) }}
                        </span>
                      </div>
                      <p class="text-xs text-gray-500 mt-1">
                        {{ formatDateTime(record.created_at) }}
                      </p>
                    </div>
                  </div>

                  <!-- 中部：提示词 -->
                  <div v-if="record.prompt" class="mb-3">
                    <p class="text-sm text-gray-700 line-clamp-2">{{ record.prompt }}</p>
                  </div>

                  <!-- 底部：扣费信息和失败原因 -->
                  <div class="flex items-center justify-between text-sm">
                    <div class="flex items-center gap-4">
                      <!-- 扣费信息 -->
                      <div v-if="record.status === 'success'" class="flex items-center gap-3">
                        <div v-if="record.points_used > 0" class="text-gray-700">
                          <span class="font-semibold text-primary">{{ record.points_used }}</span> 积分
                        </div>
                        <div v-if="record.amount > 0" class="text-gray-700">
                          <span class="font-semibold text-primary">¥{{ (record.amount / 100).toFixed(2) }}</span>
                        </div>
                        <div class="text-gray-500">
                          {{ record.image_count }} 张图片
                        </div>
                      </div>

                      <!-- 失败原因 -->
                      <div v-else class="text-red-600">
                        <span class="material-symbols-outlined !text-sm align-middle">error</span>
                        <span class="ml-1">{{ record.error_reason || '生成失败' }}</span>
                      </div>
                    </div>

                    <!-- 图片预览（仅成功且有图片） -->
                    <div v-if="record.status === 'success' && record.image_urls && record.image_urls.length > 0" class="flex items-center gap-2">
                      <img
                        v-for="(url, idx) in record.image_urls.slice(0, 3)"
                        :key="idx"
                        :src="resolveImageSrc(getImageUrl(url))"
                        class="w-12 h-12 object-cover rounded-lg border border-border-dark"
                        @error="handleImageFallback"
                      >
                      <span v-if="record.image_urls.length > 3" class="text-xs text-gray-500">
                        +{{ record.image_urls.length - 3 }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div v-if="authStore.consumptionRecords.length >= consumptionLimit" class="mt-6 text-center">
                <button
                  @click="loadMoreConsumption"
                  :disabled="authStore.consumptionLoading"
                  class="px-6 py-2 bg-white border border-border-dark text-ink-700 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
                >
                  {{ authStore.consumptionLoading ? '加载中...' : '加载更多' }}
                </button>
              </div>
            </div>
          </div>

          <!-- 提现管理标签页 -->
          <div v-if="activeTab === 'withdrawal'" class="space-y-6">
            <!-- 可提现余额 -->
            <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl shadow-lg p-6 text-white">
              <h2 class="text-lg font-semibold mb-4">可提现余额</h2>
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-4xl font-bold">¥{{ ((accountInfo?.balance || 0) / 100).toFixed(2) }}</p>
                  <p class="text-sm opacity-80 mt-1">可提现金额</p>
                </div>
                <button
                  @click="showWithdrawalModal = true"
                  class="px-6 py-3 bg-white/20 hover:bg-white/30 rounded-xl font-medium transition-colors"
                >
                  申请提现
                </button>
              </div>
            </div>

            <!-- 提现规则 -->
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <h3 class="text-lg font-bold text-ink-950 mb-4">提现规则</h3>
              <ul class="space-y-2 text-sm text-gray-600">
                <li class="flex items-start gap-2">
                  <span class="material-symbols-outlined !text-lg text-green-500">check_circle</span>
                  <span>提现无手续费，申请金额 = 实际到账金额</span>
                </li>
                <li class="flex items-start gap-2">
                  <span class="material-symbols-outlined !text-lg text-green-500">check_circle</span>
                  <span>支持微信、支付宝、银行卡提现</span>
                </li>
                <li class="flex items-start gap-2">
                  <span class="material-symbols-outlined !text-lg text-green-500">check_circle</span>
                  <span>提现申请提交后，管理员审核通过后会线下打款</span>
                </li>
                <li class="flex items-start gap-2">
                  <span class="material-symbols-outlined !text-lg text-green-500">check_circle</span>
                  <span>待审核状态的提现申请可以取消</span>
                </li>
              </ul>
            </div>

            <!-- 提现记录 -->
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-lg font-bold text-ink-950">提现记录</h2>
                <span class="text-sm text-gray-500">共 {{ withdrawals.length }} 条记录</span>
              </div>

              <div v-if="withdrawals.length === 0" class="text-center py-12">
                <span class="material-symbols-outlined !text-6xl text-gray-300">payments</span>
                <p class="text-gray-500 mt-4">暂无提现记录</p>
                <button
                  @click="showWithdrawalModal = true"
                  class="mt-4 px-6 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-strong"
                >
                  申请提现
                </button>
              </div>

              <div v-else class="space-y-4">
                <div
                  v-for="withdrawal in withdrawals"
                  :key="withdrawal.id"
                  class="p-4 border border-gray-200 rounded-xl hover:border-gray-300 transition-colors"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex-1">
                      <div class="flex items-center gap-3">
                        <p class="text-lg font-bold text-gray-900">¥{{ withdrawal.amount_yuan.toFixed(2) }}</p>
                        <span
                          :class="[
                            'px-2 py-0.5 text-xs rounded-full',
                            withdrawal.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                            withdrawal.status === 'approved' ? 'bg-blue-100 text-blue-700' :
                            withdrawal.status === 'completed' ? 'bg-green-100 text-green-700' :
                            'bg-red-100 text-red-700'
                          ]"
                        >
                          {{ getWithdrawalStatusText(withdrawal.status) }}
                        </span>
                      </div>
                      <p class="text-sm text-gray-500 mt-1">
                        {{ getWithdrawalMethodText(withdrawal.withdrawal_method) }} · {{ withdrawal.withdrawal_account }}
                      </p>
                      <p class="text-sm text-gray-500">申请时间: {{ formatDate(withdrawal.created_at) }}</p>
                      <p v-if="withdrawal.review_note" class="text-sm text-gray-600 mt-1">备注: {{ withdrawal.review_note }}</p>
                    </div>
                    <div class="flex items-center gap-2">
                      <button
                        v-if="withdrawal.status === 'pending'"
                        @click="handleCancelWithdrawal(withdrawal.withdrawal_id)"
                        class="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg font-medium"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 邀请码标签页 -->
          <div v-if="activeTab === 'invite'" class="space-y-6">
            <!-- 邀请码卡片 -->
            <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl shadow-lg p-6 text-white">
              <h2 class="text-lg font-semibold mb-4">我的邀请码</h2>
              <div class="flex items-center justify-between">
                <p class="text-4xl font-bold tracking-wider">{{ inviteInfo.invite_code || '加载中...' }}</p>
                <button
                  @click="copyInviteCode"
                  class="px-6 py-3 bg-white/20 hover:bg-white/30 rounded-xl font-medium transition-colors"
                >
                  复制邀请码
                </button>
              </div>
              <div class="grid grid-cols-2 gap-6 mt-6">
                <div>
                  <p class="text-3xl font-bold">{{ inviteInfo.total_invite_count || 0 }}</p>
                  <p class="text-sm opacity-80">邀请人数</p>
                </div>
                <div>
                  <p class="text-3xl font-bold">{{ inviteInfo.total_reward_points || 0 }}</p>
                  <p class="text-sm opacity-80">累计奖励积分</p>
                </div>
              </div>
            </div>

            <!-- 邀请记录 -->
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <h2 class="text-lg font-bold text-ink-950 mb-6">邀请记录</h2>

              <div v-if="inviteRecords.length === 0" class="text-center py-12">
                <span class="material-symbols-outlined !text-6xl text-gray-300">person_add</span>
                <p class="text-gray-500 mt-4">暂无邀请记录</p>
                <p class="text-sm text-gray-400 mt-2">分享邀请码给朋友，双方都能获得积分奖励</p>
              </div>

              <div v-else class="space-y-4">
                <div
                  v-for="record in inviteRecords"
                  :key="record.user_id"
                  class="flex items-center justify-between p-4 bg-gray-50 rounded-xl"
                >
                  <div>
                    <p class="font-medium text-gray-900">{{ maskUsername(record.username) }}</p>
                    <p class="text-sm text-gray-500">{{ formatDate(record.created_at) }}</p>
                  </div>
                  <span class="text-sm text-green-600 font-medium">+50 积分</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 通知中心标签页 -->
          <div v-if="activeTab === 'notifications'" class="space-y-6">
            <AnnouncementList />
          </div>
        </main>
      </div>
    </div>

    <!-- 充值弹窗 -->
    <div v-if="showRechargeModal && selectedOption" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-ink-950">确认充值</h2>
          <button @click="showRechargeModal = false" class="text-gray-400 hover:text-gray-600">
            <span class="material-symbols-outlined !text-2xl">close</span>
          </button>
        </div>

        <div class="space-y-4">
          <div class="p-4 bg-gray-50 rounded-xl">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-semibold text-gray-900">{{ selectedOption.name }}</p>
                <p class="text-sm text-gray-600">
                  充值 ¥{{ selectedOption.amount_yuan }}，获得 {{ selectedOption.points }} 积分
                  <span v-if="selectedOption.bonus" class="text-green-600">+{{ selectedOption.bonus }} 赠送</span>
                </p>
              </div>
              <span class="text-2xl font-bold text-gray-900">¥{{ selectedOption.amount_yuan }}</span>
            </div>
          </div>

          <!-- 支付方式选择 -->
          <div class="space-y-3">
            <p class="text-sm font-medium text-gray-700">选择支付方式</p>
            <div class="flex gap-3">
              <button
                @click="paymentMethod = 'wechat'"
                :class="[
                  'flex-1 py-3 px-4 rounded-lg border-2 transition-all flex items-center justify-center gap-2',
                  paymentMethod === 'wechat'
                    ? 'border-primary bg-primary-soft'
                    : 'border-gray-200 hover:border-gray-300'
                ]"
              >
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="#07C160">
                  <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a31.429 31.429 0 0 0 4.76 2.895c1.597 1.118 3.658 1.693 5.758 1.693h.07c2.1 0 4.16-.575 5.758-1.693a31.429 31.429 0 0 0 4.76-2.895C23.83 13.733 25 11.742 25 9.53c0-4.054-3.891-7.342-8.691-7.342zM8.31 17.409a1.686 1.686 0 0 1-1.026-.398 1.66 1.66 0 0 1-.398-1.026c.013-.016 1.17-1.438 4.204-4.472 3.035-3.034 4.457-4.19 4.472-4.204a1.66 1.66 0 0 1 .398 1.026 1.686 1.686 0 0 1 1.026.398c-.016.013-1.438 1.17-4.472 4.204-3.034 3.035-4.19 4.457-4.204 4.472z"/>
                </svg>
                微信支付
              </button>
            </div>

            <button
              @click="createOrder"
              :disabled="!paymentMethod || creatingOrder"
              class="w-full mt-4 py-3 bg-gradient-to-r from-primary to-primary-deep text-white rounded-lg font-medium hover:from-primary-strong hover:to-primary-deep disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {{ creatingOrder ? '创建订单中...' : '确认支付' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 支付二维码弹窗 -->
    <div v-if="showPaymentModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl max-w-sm w-full p-6">
        <div class="text-center">
          <h3 class="text-lg font-bold text-ink-950 mb-2">请扫码支付</h3>
          <p class="text-gray-600 mb-4">¥{{ currentOrderAmount }}</p>

          <div class="bg-gray-100 p-4 rounded-xl inline-block mb-4">
            <img v-if="qrCodeUrl" :src="qrCodeUrl" alt="支付二维码" class="w-48 h-48" />
            <div v-else class="w-48 h-48 flex items-center justify-center">
              <span class="material-symbols-outlined !text-6xl text-gray-300 animate-spin">refresh</span>
            </div>
          </div>

          <p class="text-sm text-gray-500 mb-4">请使用微信扫码支付</p>

          <div class="flex gap-3">
            <button
              @click="showPaymentModal = false; stopPolling()"
              class="flex-1 py-2.5 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
            >
              取消
            </button>
            <button
              @click="checkPaymentStatus"
              class="flex-1 py-2.5 bg-primary text-white rounded-lg hover:bg-primary-strong font-medium"
            >
              已完成支付
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 提现申请弹窗 -->
    <div v-if="showWithdrawalModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-ink-950">申请提现</h2>
          <button @click="showWithdrawalModal = false" class="text-gray-400 hover:text-gray-600">
            <span class="material-symbols-outlined !text-2xl">close</span>
          </button>
        </div>

        <form @submit.prevent="handleCreateWithdrawal" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">提现金额（元）</label>
            <input
              v-model.number="withdrawalForm.amount"
              type="number"
              step="0.01"
              min="0.01"
              :max="(accountInfo?.balance || 0) / 100"
              placeholder="请输入提现金额"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary"
            />
            <p class="text-xs text-gray-500 mt-1">可提现余额: ¥{{ ((accountInfo?.balance || 0) / 100).toFixed(2) }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">提现方式</label>
            <select
              v-model="withdrawalForm.withdrawal_method"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary"
            >
              <option value="alipay">支付宝</option>
              <option value="wechat">微信</option>
              <option value="bank">银行卡</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">
              {{ withdrawalForm.withdrawal_method === 'alipay' ? '支付宝账号' :
                 withdrawalForm.withdrawal_method === 'wechat' ? '微信号' : '银行卡号' }}
            </label>
            <input
              v-model="withdrawalForm.withdrawal_account"
              type="text"
              :placeholder="withdrawalForm.withdrawal_method === 'alipay' ? '请输入支付宝账号' :
                          withdrawalForm.withdrawal_method === 'wechat' ? '请输入微信号' : '请输入银行卡号'"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">收款人姓名</label>
            <input
              v-model="withdrawalForm.withdrawal_name"
              type="text"
              placeholder="请输入收款人姓名"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">备注（可选）</label>
            <textarea
              v-model="withdrawalForm.user_note"
              rows="2"
              placeholder="如有特殊要求请备注"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary"
            ></textarea>
          </div>

          <div class="flex gap-3 pt-2">
            <button
              type="button"
              @click="showWithdrawalModal = false"
              :disabled="withdrawalSubmitting"
              class="flex-1 py-2.5 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50 font-medium disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="withdrawalSubmitting"
              class="flex-1 py-2.5 bg-primary text-white rounded-xl hover:bg-primary-strong font-medium disabled:opacity-50"
            >
              {{ withdrawalSubmitting ? '提交中...' : '提交申请' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 用户名修改弹窗 -->
    <div v-if="showUsernameModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-ink-950">修改用户名</h2>
          <button @click="showUsernameModal = false" class="text-gray-400 hover:text-gray-600">
            <span class="material-symbols-outlined !text-2xl">close</span>
          </button>
        </div>

        <form @submit.prevent="handleUpdateUsername" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">用户名</label>
            <input
              v-model="usernameForm.username"
              type="text"
              placeholder="2-20位字符"
              minlength="2"
              maxlength="20"
              class="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>
          <div class="flex gap-3">
            <button
              type="button"
              @click="showUsernameModal = false"
              class="flex-1 py-2.5 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50 font-medium"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="usernameUpdating"
              class="flex-1 py-2.5 bg-gradient-to-r from-primary to-primary-deep text-white rounded-xl hover:from-primary-strong hover:to-primary-deep disabled:opacity-50 font-medium"
            >
              {{ usernameUpdating ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 密码修改弹窗 -->
    <div v-if="showPasswordModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-ink-950">修改密码</h2>
          <button @click="showPasswordModal = false" class="text-gray-400 hover:text-gray-600">
            <span class="material-symbols-outlined !text-2xl">close</span>
          </button>
        </div>

        <form @submit.prevent="handleUpdatePassword" class="space-y-4">
          <!-- Current Password -->
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1.5">当前密码</label>
            <input
              v-model="passwordForm.old_password"
              type="password"
              required
              minlength="6"
              placeholder="请输入当前密码"
              class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
            />
          </div>

          <!-- New Password -->
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1.5">新密码</label>
            <input
              v-model="passwordForm.new_password"
              type="password"
              required
              minlength="6"
              maxlength="50"
              placeholder="至少6位字符"
              class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
            />
          </div>

          <!-- Confirm New Password -->
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-1.5">确认新密码</label>
            <input
              v-model="passwordForm.confirm_password"
              type="password"
              required
              minlength="6"
              placeholder="再次输入新密码"
              class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
            />
          </div>

          <!-- Buttons -->
          <div class="flex gap-3">
            <button
              type="button"
              @click="showPasswordModal = false"
              class="flex-1 py-2.5 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50 font-medium"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="passwordUpdating"
              class="flex-1 py-2.5 bg-gradient-to-r from-primary to-primary-deep text-white rounded-xl hover:from-primary-strong hover:to-primary-deep disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-lg"
            >
              {{ passwordUpdating ? '修改中...' : '确认修改' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 生成详情弹窗 -->
    <div v-if="showGenerationDetail" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-ink-950">生成详情</h2>
          <button @click="showGenerationDetail = false" class="text-gray-400 hover:text-gray-600">
            <span class="material-symbols-outlined !text-2xl">close</span>
          </button>
        </div>

        <div v-if="selectedGeneration" class="space-y-6">
          <!-- 图片网格 -->
          <div class="grid grid-cols-2 gap-4">
            <div
              v-for="(url, index) in selectedGeneration.image_urls"
              :key="index"
              class="aspect-square bg-gray-100 rounded-xl overflow-hidden"
            >
              <img :src="url" :alt="`生成图片 ${index + 1}`" class="w-full h-full object-cover" />
            </div>
          </div>

          <!-- 详情信息 -->
          <div class="space-y-4">
            <div>
              <label class="text-sm font-medium text-gray-700">提示词</label>
              <p class="mt-1 p-3 bg-gray-50 rounded-lg text-gray-900">{{ selectedGeneration.prompt }}</p>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label class="text-sm font-medium text-gray-700">模型</label>
                <p class="mt-1 text-gray-900">{{ selectedGeneration.model }}</p>
              </div>
              <div>
                <label class="text-sm font-medium text-gray-700">尺寸</label>
                <p class="mt-1 text-gray-900">{{ selectedGeneration.width }} × {{ selectedGeneration.height }}</p>
              </div>
              <div>
                <label class="text-sm font-medium text-gray-700">状态</label>
                <p class="mt-1 text-gray-900">{{ getStatusText(selectedGeneration.status) }}</p>
              </div>
              <div>
                <label class="text-sm font-medium text-gray-700">生成时间</label>
                <p class="mt-1 text-gray-900">{{ formatDate(selectedGeneration.created_at) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '@/store/useAuthStore'
import { useAppStore } from '@/store/useAppStore'
import { useNotificationStore } from '@/store/useNotificationStore'
import { api } from '@/services/api'
import { handleImageFallback, resolveImageSrc } from '@/utils/imageFallback'
import { notification } from '@/utils/notification'
import AnnouncementList from '@/components/AnnouncementList.vue'

const authStore = useAuthStore()
const appStore = useAppStore()
const notificationStore = useNotificationStore()

// 状态
const activeTab = computed(() => appStore.userCenterTab)
const accountInfo = ref(null)
const rechargeOptions = ref([])
const orders = ref([])
const generationRecords = ref([])
const totalCount = ref(0)
const currentPage = ref(0)
const pageSize = 20
const downloadRecords = ref([])
const inviteInfo = ref({})
const inviteRecords = ref([])
const checkinInfo = ref({})

// 提现相关
const withdrawals = ref([])
const showWithdrawalModal = ref(false)
const withdrawalForm = ref({
  amount: 0,
  withdrawal_method: 'alipay',
  withdrawal_account: '',
  withdrawal_name: '',
  user_note: ''
})
const withdrawalSubmitting = ref(false)

// 充值相关
const showRechargeModal = ref(false)
const showPaymentModal = ref(false)
const selectedOption = ref(null)
const paymentMethod = ref(null)
const creatingOrder = ref(false)
const currentOrderId = ref(null)
const currentOrderAmount = ref(0)
const qrCodeUrl = ref('')
const pollingTimer = ref(null)
const refreshInterval = ref(null)

// 签到相关
const canCheckin = ref(true)
const checkinLoading = ref(false)

// 用户名修改
const showUsernameModal = ref(false)
const usernameUpdating = ref(false)
const usernameForm = ref({ username: '' })

// 密码修改
const showPasswordModal = ref(false)
const passwordUpdating = ref(false)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 生成详情
const showGenerationDetail = ref(false)
const selectedGeneration = ref(null)

// 生成筛选
const generationFilter = ref({ status: '' })

// 消费记录相关
const consumptionFilter = ref('all')
const consumptionLimit = ref(20)
const consumptionOffset = ref(0)

// 初始化
onMounted(async () => {
  // 自动刷新用户信息
  try {
    await authStore.fetchCurrentUser()
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }

  // 加载账户信息和其他数据
  await loadAccountInfo()
  await loadRechargeOptions()
  await loadCheckinStatus()
})

onUnmounted(() => {
  stopPolling()
  stopAutoRefresh()
})

// 根据标签页启动/停止自动刷新
watch(activeTab, (newTab) => {
  if (newTab === 'generation') {
    currentPage.value = 0
    loadGenerationHistory()
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }

  // 切换到消费记录标签时，加载数据
  if (newTab === 'consumption' && authStore.consumptionRecords.length === 0) {
    loadConsumptionRecords()
  }
})

// 过滤后的消费记录
const filteredConsumptionRecords = computed(() => {
  const records = authStore.consumptionRecords
  switch (consumptionFilter.value) {
    case 'success':
      return records.filter(r => r.status === 'success')
    case 'failed':
      return records.filter(r => r.status === 'failed')
    case 'points':
      return records.filter(r => r.cost_type === 'points' || r.cost_type === 'gift_points')
    case 'balance':
      return records.filter(r => r.cost_type === 'balance')
    default:
      return records
  }
})

// 加载账户信息
async function loadAccountInfo() {
  try {
    accountInfo.value = await api.getAccountInfo()
  } catch (error) {
    console.error('加载账户信息失败:', error)
  }
}

// 加载充值选项
async function loadRechargeOptions() {
  try {
    rechargeOptions.value = await api.getRechargeOptions()
  } catch (error) {
    console.error('加载充值选项失败:', error)
  }
}

// 加载签到状态
async function loadCheckinStatus() {
  try {
    const status = await api.getCheckinStatus()
    canCheckin.value = status.can_checkin
    checkinInfo.value = status
  } catch (error) {
    console.error('加载签到状态失败:', error)
  }
}

// 加载消费记录
async function loadConsumptionRecords() {
  consumptionOffset.value = 0
  await authStore.fetchConsumptionRecords(consumptionLimit.value, 0)
}

// 加载更多消费记录
async function loadMoreConsumption() {
  consumptionOffset.value += consumptionLimit.value
  await authStore.fetchConsumptionRecords(consumptionLimit.value, consumptionOffset.value)
}

// 获取计费类型显示文本
function getCostTypeDisplay(costType) {
  const typeMap = {
    'free': '免费',
    'subscription': '订阅',
    'points': '积分',
    'gift_points': '临时积分',
    'balance': '余额'
  }
  return typeMap[costType] || costType
}

// 获取图片URL（处理相对路径）
function getImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `/api/v1${url.startsWith('/') ? '' : '/'}${url}`
}

// 格式化日期时间
function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return minutes <= 1 ? '刚刚' : `${minutes}分钟前`
    }
    return `${hours}小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  }
}

// 加载订单列表
async function loadOrders() {
  try {
    orders.value = await api.getOrders(50, 0)
  } catch (error) {
    console.error('加载订单列表失败:', error)
  }
}

// 加载生成历史
async function loadGenerationHistory() {
  try {
    const status = generationFilter.value.status || undefined
    const offset = currentPage.value * pageSize

    // 调用统一API
    generationRecords.value = await api.getUnifiedGenerationHistory(
      pageSize,
      offset,
      status
    )

    // 获取总数
    const countResult = await api.getUnifiedGenerationHistoryCount(status)
    totalCount.value = countResult.count
  } catch (error) {
    console.error('加载生成历史失败:', error)
  }
}

// 加载下载记录
async function loadDownloadRecords() {
  try {
    downloadRecords.value = await api.getDownloadRecords(50, 0)
  } catch (error) {
    console.error('加载下载记录失败:', error)
  }
}

// 加载邀请信息
async function loadInviteInfo() {
  try {
    inviteInfo.value = await api.getInviteStats()
    inviteRecords.value = await api.getInviteRecords()
  } catch (error) {
    console.error('加载邀请信息失败:', error)
  }
}

// 标签页切换
async function handleTabChange(tab) {
  // 按需加载数据
  if (tab === 'recharge' && orders.value.length === 0) {
    await loadOrders()
  } else if (tab === 'generation' && generationRecords.value.length === 0) {
    await loadGenerationHistory()
  } else if (tab === 'download' && downloadRecords.value.length === 0) {
    await loadDownloadRecords()
  } else if (tab === 'withdrawal' && withdrawals.value.length === 0) {
    await loadWithdrawals()
  } else if (tab === 'invite' && !inviteInfo.value.invite_code) {
    await loadInviteInfo()
  }
}

// 每日签到
async function handleDailyCheckin() {
  checkinLoading.value = true
  try {
    const result = await api.dailyCheckin()
    canCheckin.value = false
    checkinInfo.value = {
      consecutive_days: result.consecutive_days,
      gift_points: result.gift_points
    }
    notification.success(`签到成功！获得 ${result.reward_points} 积分`)
    await loadAccountInfo()
  } catch (error) {
    notification.error(error.message || '签到失败')
  } finally {
    checkinLoading.value = false
  }
}

// 创建订单
async function createOrder() {
  if (!selectedOption.value || !paymentMethod.value) return

  creatingOrder.value = true
  try {
    const order = await api.createRechargeOrder(selectedOption.value.id, paymentMethod.value)
    currentOrderId.value = order.order_id
    currentOrderAmount.value = order.amount_yuan
    qrCodeUrl.value = order.qr_code_url

    showRechargeModal.value = false
    showPaymentModal.value = true

    // 开始轮询订单状态
    startPolling()
  } catch (error) {
    notification.error(error.message || '创建订单失败')
  } finally {
    creatingOrder.value = false
  }
}

// 继续支付
async function continuePay(order) {
  try {
    const qrcode = await api.getPaymentQrcode(order.order_id)
    currentOrderId.value = order.order_id
    currentOrderAmount.value = order.amount_yuan
    qrCodeUrl.value = qrcode.qr_code_url
    paymentMethod.value = order.payment_method

    showPaymentModal.value = true
    startPolling()
  } catch (error) {
    notification.error(error.message || '获取支付信息失败')
  }
}

// 开始轮询
function startPolling() {
  stopPolling()
  pollingTimer.value = window.setInterval(async () => {
    await checkPaymentStatus()
  }, 3000)
}

// 停止轮询
function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

// 开始自动刷新（针对进行中的任务）
function startAutoRefresh() {
  if (refreshInterval.value) clearInterval(refreshInterval.value)

  refreshInterval.value = window.setInterval(async () => {
    // 仅当有待处理或处理中的记录时刷新
    const hasPending = generationRecords.value.some(
      r => r.status === 'pending' || r.status === 'processing'
    )

    if (hasPending) {
      await loadGenerationHistory()
    }
  }, 5000) // 每5秒刷新
}

// 停止自动刷新
function stopAutoRefresh() {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// 检查支付状态
async function checkPaymentStatus() {
  if (!currentOrderId.value) return

  try {
    const status = await api.getOrderStatus(currentOrderId.value)
    if (status.status === 'paid') {
      stopPolling()
      showPaymentModal.value = false
      notification.success('支付成功！')
      await loadAccountInfo()
      await loadOrders()
    }
  } catch (error) {
    console.error('检查支付状态失败:', error)
  }
}

// 取消订单
async function cancelOrder(orderId) {
  try {
    await api.cancelOrder(orderId)
    notification.success('订单已取消')
    await loadOrders()
  } catch (error) {
    notification.error(error.message || '取消订单失败')
  }
}

// 修改用户名
async function handleUpdateUsername() {
  if (!usernameForm.value.username) return

  usernameUpdating.value = true
  try {
    await api.updateProfile({ username: usernameForm.value.username })
    notification.success('用户名修改成功')
    showUsernameModal.value = false
    await authStore.fetchCurrentUser()
  } catch (error) {
    notification.error(error.message || '修改用户名失败')
  } finally {
    usernameUpdating.value = false
  }
}

// 修改密码
async function handleUpdatePassword() {
  // Client-side validation
  if (passwordForm.value.new_password.length < 6) {
    notification.error('密码长度至少6位')
    return
  }

  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    notification.error('两次输入的密码不一致')
    return
  }

  if (passwordForm.value.old_password === passwordForm.value.new_password) {
    notification.error('新密码不能与当前密码相同')
    return
  }

  passwordUpdating.value = true
  try {
    await api.changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })

    notification.success('密码修改成功，请重新登录')
    showPasswordModal.value = false

    // Clear form
    passwordForm.value = {
      old_password: '',
      new_password: '',
      confirm_password: ''
    }

    // Logout and redirect to login
    setTimeout(async () => {
      await authStore.logout()
      appStore.setCurrentPage('login')
    }, 1500)

  } catch (error) {
    const errorMessage = error?.response?.data?.detail || error?.message || '修改密码失败'
    notification.error(errorMessage)
  } finally {
    passwordUpdating.value = false
  }
}

// 查看生成详情
function viewGenerationDetail(record) {
  selectedGeneration.value = record
  showGenerationDetail.value = true
}

// 复制邀请码
async function copyInviteCode() {
  try {
    await navigator.clipboard.writeText(inviteInfo.value.invite_code)
    notification.success('邀请码已复制到剪贴板')
  } catch (error) {
    notification.error('复制失败，请手动复制')
  }
}

// 加载提现记录
async function loadWithdrawals() {
  try {
    withdrawals.value = await api.getMyWithdrawals()
  } catch (error) {
    console.error('加载提现记录失败:', error)
  }
}

// 创建提现申请
async function handleCreateWithdrawal() {
  if (!withdrawalForm.value.amount || withdrawalForm.value.amount <= 0) {
    notification.error('请输入有效的提现金额')
    return
  }

  if (!withdrawalForm.value.withdrawal_account) {
    notification.error('请输入提现账号')
    return
  }

  if (!withdrawalForm.value.withdrawal_name) {
    notification.error('请输入收款人姓名')
    return
  }

  // 检查余额是否充足
  if ((accountInfo.value?.balance || 0) < withdrawalForm.value.amount) {
    notification.error('余额不足，无法提现')
    return
  }

  withdrawalSubmitting.value = true
  try {
    await api.createWithdrawal({
      amount: withdrawalForm.value.amount,
      withdrawal_method: withdrawalForm.value.withdrawal_method,
      withdrawal_account: withdrawalForm.value.withdrawal_account,
      withdrawal_name: withdrawalForm.value.withdrawal_name,
      user_note: withdrawalForm.value.user_note
    })

    notification.success('提现申请已提交，等待审核')
    showWithdrawalModal.value = false

    // 重置表单
    withdrawalForm.value = {
      amount: 0,
      withdrawal_method: 'alipay',
      withdrawal_account: '',
      withdrawal_name: '',
      user_note: ''
    }

    // 重新加载账户信息和提现记录
    await loadAccountInfo()
    await loadWithdrawals()
  } catch (error) {
    console.error('创建提现申请失败:', error)
    notification.error(error.response?.data?.detail || '创建提现申请失败')
  } finally {
    withdrawalSubmitting.value = false
  }
}

// 取消提现申请
async function handleCancelWithdrawal(withdrawalId) {
  if (!confirm('确定要取消此提现申请吗？')) {
    return
  }

  try {
    await api.cancelWithdrawal(withdrawalId)
    notification.success('提现申请已取消')
    await loadWithdrawals()
  } catch (error) {
    console.error('取消提现申请失败:', error)
    notification.error(error.response?.data?.detail || '取消提现申请失败')
  }
}

// 获取提现状态文本
function getWithdrawalStatusText(status) {
  const statusMap = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 获取提现方式文本
function getWithdrawalMethodText(method) {
  const methodMap = {
    'wechat': '微信',
    'alipay': '支付宝',
    'bank': '银行卡'
  }
  return methodMap[method] || method
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return minutes === 0 ? '刚刚' : `${minutes} 分钟前`
    }
    return `${hours} 小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days} 天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 格式化过期时间为"XX时XX分"
function formatExpiryTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')

  return `${month}月${day}日 ${hours}时${minutes}分`
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 获取状态文本
function getStatusText(status) {
  const statusMap = {
    'pending': '待支付',
    'paid': '已完成',
    'cancelled': '已取消',
    'expired': '已过期',
    'completed': '成功',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 获取账户状态显示文本
function getStatusDisplay(status) {
  // 转换为小写进行比较
  const statusLower = (status || '').toLowerCase()

  if (statusLower === 'active' || statusLower === '正常') {
    return '正常'
  } else if (statusLower === 'banned' || statusLower === 'disabled' || statusLower === '已禁用') {
    return '已禁用'
  }

  // 默认情况下，如果是 active 相关的都显示正常
  return status === 'active' ? '正常' : (status || '未知')
}

// 脱敏用户名
function maskUsername(username) {
  if (!username) return '***'
  if (username.length <= 3) return username[0] + '**'
  return username[0] + '*'.repeat(username.length - 2) + username[username.length - 1]
}

// 返回首页
function goHome() {
  appStore.setCurrentPage('agent')
}

// 监听标签页切换
watch(activeTab, (newTab) => {
  handleTabChange(newTab)
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
