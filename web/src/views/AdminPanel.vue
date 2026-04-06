<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm sticky top-0 z-10 border-b">
      <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <h1 class="text-xl font-bold text-ink-950">管理后台</h1>
        <button @click="goHome" class="text-sm text-primary font-medium">
          返回首页
        </button>
      </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 py-8">
      <!-- 移动端菜单标题和折叠按钮 -->
      <div class="md:hidden flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-ink-950">菜单</h2>
        <button
          @click="toggleSidebar"
          class="inline-flex items-center gap-2 px-4 py-2 bg-white border border-border-dark rounded-xl hover:bg-gray-50 transition-colors"
        >
          <span class="material-symbols-outlined !text-xl">
            {{ sidebarCollapsed ? 'menu_open' : 'menu' }}
          </span>
          {{ sidebarCollapsed ? '展开' : '收起' }}
        </button>
      </div>

      <div class="flex flex-col md:flex-row gap-6">
        <!-- 桌面端折叠按钮（侧边栏外） -->
        <div v-if="sidebarCollapsed" class="hidden md:block">
          <button
            @click="toggleSidebar"
            class="sticky top-24 inline-flex items-center justify-center w-12 h-12 bg-white border border-border-dark rounded-xl hover:bg-gray-50 transition-colors shadow-sm"
            title="展开菜单"
          >
            <span class="material-symbols-outlined !text-xl">menu_open</span>
          </button>
        </div>

        <!-- 侧边栏 -->
        <aside v-if="!sidebarCollapsed" class="w-full md:w-56 shrink-0">
          <!-- 桌面端折叠按钮（侧边栏内） -->
          <div class="hidden md:flex justify-end mb-4">
            <button
              @click="toggleSidebar"
              class="inline-flex items-center gap-2 px-3 py-2 bg-white border border-border-dark rounded-lg hover:bg-gray-50 transition-colors text-sm"
              title="收起菜单"
            >
              <span class="material-symbols-outlined !text-lg">menu</span>
              收起菜单
            </button>
          </div>

          <nav class="bg-white rounded-2xl shadow-sm p-2 space-y-1 sticky top-24">
            <button
              @click="activeTab = 'overview'"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium flex items-center gap-3',
                activeTab === 'overview' ? 'bg-primary text-white' : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">dashboard</span>
              数据概览
            </button>
            <button
              @click="activeTab = 'users'"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium flex items-center gap-3',
                activeTab === 'users' ? 'bg-primary text-white' : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">people</span>
              用户管理
            </button>
            <button
              @click="activeTab = 'withdrawals'"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium flex items-center gap-3',
                activeTab === 'withdrawals' ? 'bg-primary text-white' : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">request_quote</span>
              提现审核
            </button>
            <button
              @click="activeTab = 'cases'"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium flex items-center gap-3',
                activeTab === 'cases' ? 'bg-primary text-white' : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">folder_special</span>
              案例管理
            </button>
            <button
              @click="activeTab = 'scenes'"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium flex items-center gap-3',
                activeTab === 'scenes' ? 'bg-primary text-white' : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">grid_view</span>
              场景库管理
            </button>
            <button
              @click="activeTab = 'pricing'"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium flex items-center gap-3',
                activeTab === 'pricing' ? 'bg-primary text-white' : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">sell</span>
              产品定价
            </button>
            <button
              @click="activeTab = 'config'"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium flex items-center gap-3',
                activeTab === 'config' ? 'bg-primary text-white' : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">settings</span>
              系统配置
            </button>
            <button
              @click="activeTab = 'announcements'"
              :class="[
                'w-full px-4 py-3 rounded-xl text-left font-medium flex items-center gap-3',
                activeTab === 'announcements' ? 'bg-primary text-white' : 'text-ink-700 hover:bg-gray-50'
              ]"
            >
              <span class="material-symbols-outlined !text-xl">campaign</span>
              公告管理
            </button>
          </nav>
        </aside>

        <main class="flex-1 min-w-0">
          <div v-if="activeTab === 'overview'" class="space-y-6">
            <h2 class="text-xl xs:text-2xl font-bold text-ink-950">平台数据概览</h2>

            <div class="grid grid-cols-2 xs:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 xs:gap-4">
              <div class="bg-white rounded-2xl shadow-sm p-4 xs:p-6 border border-border-dark">
                <div class="flex items-center justify-between mb-3 xs:mb-4">
                  <span class="material-symbols-outlined !text-2xl xs:!text-3xl text-primary">groups</span>
                  <span class="text-[10px] xs:text-xs text-ink-500 bg-primary-soft px-2 py-0.5 rounded-full">总用户数</span>
                </div>
                <p class="text-2xl xs:text-3xl font-bold text-ink-950 mb-1">{{ statistics.total_users || 0 }}</p>
                <p class="text-xs xs:text-sm text-ink-500">今日新增: {{ statistics.today_users || 0 }}</p>
              </div>

              <div class="bg-white rounded-2xl shadow-sm p-4 xs:p-6 border border-border-dark">
                <div class="flex items-center justify-between mb-3 xs:mb-4">
                  <span class="material-symbols-outlined !text-2xl xs:!text-3xl text-primary">person_check</span>
                  <span class="text-[10px] xs:text-xs text-ink-500 bg-primary-soft px-2 py-0.5 rounded-full">活跃用户</span>
                </div>
                <p class="text-2xl xs:text-3xl font-bold text-ink-950 mb-1">{{ statistics.active_users || 0 }}</p>
                <p class="text-xs xs:text-sm text-ink-500">近7天活跃</p>
              </div>

              <div class="bg-white rounded-2xl shadow-sm p-4 xs:p-6 border border-border-dark">
                <div class="flex items-center justify-between mb-3 xs:mb-4">
                  <span class="material-symbols-outlined !text-2xl xs:!text-3xl text-primary">image</span>
                  <span class="text-[10px] xs:text-xs text-ink-500 bg-primary-soft px-2 py-0.5 rounded-full">总生成数</span>
                </div>
                <p class="text-2xl xs:text-3xl font-bold text-ink-950 mb-1">{{ statistics.total_generated || 0 }}</p>
                <p class="text-xs xs:text-sm text-ink-500">今日: {{ statistics.today_generated || 0 }}</p>
              </div>

              <div class="bg-white rounded-2xl shadow-sm p-4 xs:p-6 border border-border-dark">
                <div class="flex items-center justify-between mb-3 xs:mb-4">
                  <span class="material-symbols-outlined !text-2xl xs:!text-3xl text-primary">payments</span>
                  <span class="text-[10px] xs:text-xs text-ink-500 bg-primary-soft px-2 py-0.5 rounded-full">总收入</span>
                </div>
                <p class="text-2xl xs:text-3xl font-bold text-ink-950 mb-1">¥{{ (statistics.total_revenue || 0) / 100 }}</p>
                <p class="text-xs xs:text-sm text-ink-500">今日: ¥{{ (statistics.today_revenue || 0) / 100 }}</p>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'users'" class="space-y-6">
            <div class="flex items-center justify-between">
              <h2 class="text-2xl font-bold text-ink-950">用户管理</h2>
              <button @click="loadUsers" :disabled="loading" class="px-4 py-2 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 disabled:opacity-50">
                <span v-if="loading">刷新中...</span>
                <span v-else>刷新</span>
              </button>
            </div>

            <!-- 搜索和筛选 -->
            <div class="bg-white rounded-2xl shadow-sm p-4 border border-border-dark space-y-4">
              <input
                v-model="searchKeyword"
                @keyup.enter="handleSearch"
                type="text"
                placeholder="搜索手机号或用户名..."
                class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <div class="flex gap-3">
                <select
                  v-model="filterStatus"
                  @change="handleSearch"
                  class="flex-1 px-4 py-2.5 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">全部状态</option>
                  <option value="active">活跃</option>
                  <option value="suspended">已封禁</option>
                </select>
                <select
                  v-model="filterRole"
                  @change="handleSearch"
                  class="flex-1 px-4 py-2.5 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">全部角色</option>
                  <option value="user">普通用户</option>
                  <option value="admin">管理员</option>
                </select>
              </div>
            </div>

            <!-- 用户统计 -->
            <div class="text-sm text-ink-500">
              共 {{ totalCount }} 位用户，当前显示第 {{ currentPage }} 页
            </div>

            <!-- 用户列表 -->
            <div class="bg-white rounded-2xl shadow-sm overflow-hidden border border-border-dark">
              <!-- 加载状态 -->
              <div v-if="loading" class="flex items-center justify-center py-12">
                <div class="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
              </div>

              <!-- 空状态 -->
              <div v-else-if="users.length === 0" class="text-center py-12">
                <span class="material-symbols-outlined !text-5xl text-gray-300 mb-3 block">group_off</span>
                <p class="text-sm text-gray-500">暂无用户数据</p>
              </div>

              <!-- 桌面端表格 -->
              <table v-if="!loading && users.length > 0" class="w-full hidden md:table">
                <thead class="bg-background-dark border-b border-border-dark">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">用户信息</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">积分</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">临时积分</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">余额</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">统计</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">状态</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">注册时间</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-border-dark">
                  <tr v-for="user in users" :key="user.id" class="hover:bg-primary-soft transition-colors">
                    <td class="px-4 py-3">
                      <p class="font-medium text-ink-950">{{ user.username || '未设置' }}</p>
                      <p class="text-sm text-ink-500">{{ user.phone || '-' }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-sm font-medium text-ink-950">{{ user.points.toLocaleString() }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-sm font-medium text-accent-purple-dark">{{ (user.gift_points || 0).toLocaleString() }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-sm font-medium text-ink-950">¥{{ (user.balance / 100).toFixed(2) }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-sm text-ink-700">生成: {{ user.total_generated }}</p>
                      <p class="text-sm text-ink-500">邀请: {{ user.invite_count }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <div class="flex flex-col gap-1">
                        <span :class="[
                          'px-2 py-0.5 text-xs font-medium rounded-full inline-flex items-center gap-1 w-fit',
                          user.status === 'active' ? 'bg-primary/10 text-primary' : 'bg-red-100 text-red-600'
                        ]">
                          <span class="material-symbols-outlined !text-sm">
                            {{ user.status === 'active' ? 'check_circle' : 'block' }}
                          </span>
                          {{ user.status === 'active' ? '活跃' : '已封禁' }}
                        </span>
                        <span v-if="user.role === 'admin'" class="px-2 py-0.5 text-xs font-medium rounded-full bg-accent-purple/10 text-accent-purple-dark inline-flex items-center gap-1 w-fit">
                          <span class="material-symbols-outlined !text-sm">admin_panel_settings</span>
                          管理员
                        </span>
                      </div>
                    </td>
                    <td class="px-4 py-3 text-sm text-ink-500">
                      {{ formatDate(user.created_at) }}
                    </td>
                    <td class="px-4 py-3">
                      <div class="flex items-center gap-1 flex-wrap">
                        <button
                          @click="openPointsModalForUser(user)"
                          class="text-xs px-2 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors"
                        >
                          调整积分
                        </button>
                        <button
                          @click="openBalanceModalForUser(user)"
                          class="text-xs px-2 py-1 bg-primary/10 text-ink-700 rounded hover:bg-primary/20 transition-colors"
                        >
                          调整余额
                        </button>
                        <button
                          v-if="user.status === 'active'"
                          @click="openBanModalForUser(user)"
                          class="text-xs px-2 py-1 bg-red-100 text-red-600 rounded hover:bg-red-200 transition-colors"
                        >
                          封禁
                        </button>
                        <button
                          v-else
                          @click="unbanUserDirect(user)"
                          class="text-xs px-2 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors"
                        >
                          解封
                        </button>
                        <button
                          v-if="user.role !== 'admin'"
                          @click="setAdminDirect(user)"
                          class="text-xs px-2 py-1 bg-accent-purple/10 text-accent-purple-dark rounded hover:bg-accent-purple/20 transition-colors"
                        >
                          设为管理员
                        </button>
                        <button
                          v-else
                          @click="removeAdminDirect(user)"
                          class="text-xs px-2 py-1 bg-primary/10 text-ink-500 rounded hover:bg-primary/20 transition-colors"
                        >
                          取消管理员
                        </button>
                        <button
                          @click="viewUserDetail(user)"
                          class="text-xs px-2 py-1 text-primary hover:underline"
                        >
                          详情
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>

              <!-- 移动端卡片布局 -->
              <div v-if="!loading && users.length > 0" class="space-y-3 md:hidden">
                <div
                  v-for="user in users"
                  :key="user.id"
                  class="bg-white rounded-2xl border border-border-dark overflow-hidden"
                >
                  <!-- 用户头部 -->
                  <div class="p-4 bg-gradient-to-r from-background-dark to-white">
                    <div class="flex items-center gap-3">
                      <div class="w-11 h-11 rounded-full bg-primary flex items-center justify-center text-white font-bold text-base shrink-0 shadow-sm">
                        {{ (user.username || 'U').charAt(0).toUpperCase() }}
                      </div>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center flex-wrap gap-1.5">
                          <p class="font-semibold text-ink-950 text-sm">{{ user.username || '未设置' }}</p>
                          <span
                            :class="[
                              'px-1.5 py-0.5 text-[10px] font-medium rounded',
                              user.status === 'active' ? 'bg-primary/10 text-primary' : 'bg-red-100 text-red-600'
                            ]"
                          >
                            {{ user.status === 'active' ? '活跃' : '已封禁' }}
                          </span>
                          <span
                            v-if="user.role === 'admin'"
                            class="px-1.5 py-0.5 text-[10px] font-medium rounded bg-accent-purple/10 text-accent-purple-dark"
                          >
                            管理员
                          </span>
                        </div>
                        <p class="text-xs text-ink-500 mt-0.5">{{ user.phone || '-' }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- 账户数据网格 -->
                  <div class="grid grid-cols-2 sm:grid-cols-3 gap-px bg-border-dark">
                    <div class="bg-white p-3 text-center">
                      <p class="text-[10px] text-ink-500 mb-0.5">积分</p>
                      <p class="text-base font-semibold text-ink-950">{{ user.points.toLocaleString() }}</p>
                    </div>
                    <div class="bg-white p-3 text-center">
                      <p class="text-[10px] text-accent-purple mb-0.5">临时积分</p>
                      <p class="text-base font-semibold text-accent-purple-dark">{{ (user.gift_points || 0).toLocaleString() }}</p>
                    </div>
                    <div class="bg-white p-3 text-center col-span-2 sm:col-span-1">
                      <p class="text-[10px] text-ink-500 mb-0.5">余额</p>
                      <p class="text-base font-semibold text-ink-950">¥{{ (user.balance / 100).toFixed(0) }}</p>
                    </div>
                  </div>

                  <!-- 统计信息 -->
                  <div class="px-4 py-2.5 bg-background-dark flex items-center justify-between text-xs text-ink-500">
                    <div class="flex items-center gap-3">
                      <span class="flex items-center gap-1">
                        <span class="material-symbols-outlined !text-sm">auto_awesome</span>
                        {{ user.total_generated }}
                      </span>
                      <span class="flex items-center gap-1">
                        <span class="material-symbols-outlined !text-sm">group</span>
                        {{ user.invite_count }}
                      </span>
                    </div>
                    <span>{{ formatDate(user.created_at) }}</span>
                  </div>

                  <!-- 操作按钮 -->
                  <div class="p-3 border-t border-border-dark">
                    <div class="grid grid-cols-3 gap-2">
                      <button
                        @click="openPointsModalForUser(user)"
                        class="px-2 py-2 text-xs font-medium text-primary bg-primary/5 hover:bg-primary/10 rounded-lg transition-colors"
                      >
                        调整积分
                      </button>
                      <button
                        @click="openBalanceModalForUser(user)"
                        class="px-2 py-2 text-xs font-medium text-ink-700 bg-primary/5 hover:bg-primary/10 rounded-lg transition-colors"
                      >
                        调整余额
                      </button>
                      <button
                        v-if="user.status === 'active'"
                        @click="openBanModalForUser(user)"
                        class="px-2 py-2 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                      >
                        封禁
                      </button>
                      <button
                        v-else
                        @click="unbanUserDirect(user)"
                        class="px-2 py-2 text-xs font-medium text-primary bg-primary/5 hover:bg-primary/10 rounded-lg transition-colors"
                      >
                        解封
                      </button>
                    </div>
                    <div class="grid grid-cols-2 gap-2 mt-2">
                      <button
                        v-if="user.role !== 'admin'"
                        @click="setAdminDirect(user)"
                        class="px-2 py-2 text-xs font-medium text-accent-purple-dark bg-accent-purple/10 hover:bg-accent-purple/20 rounded-lg transition-colors"
                      >
                        设为管理员
                      </button>
                      <button
                        v-else
                        @click="removeAdminDirect(user)"
                        class="px-2 py-2 text-xs font-medium text-ink-500 bg-primary/5 hover:bg-primary/10 rounded-lg transition-colors"
                      >
                        取消管理员
                      </button>
                      <button
                        @click="viewUserDetail(user)"
                        class="px-2 py-2 text-xs font-medium text-primary hover:underline rounded-lg"
                      >
                        查看详情
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 分页 -->
            <div v-if="totalCount > pageSize" class="flex items-center justify-between">
              <button
                @click="goToPage(currentPage - 1)"
                :disabled="currentPage === 1"
                class="px-4 py-2 border border-border-dark rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                上一页
              </button>
              <div class="flex items-center gap-2">
                <span>第</span>
                <input
                  :value="currentPage"
                  @keyup.enter="goToPage($event.target.value)"
                  @blur="goToPage($event.target.value)"
                  type="number"
                  min="1"
                  :max="totalPages"
                  class="w-16 px-2 py-1 border border-border-dark rounded-lg text-center"
                />
                <span>页 / 共 {{ totalPages }} 页</span>
              </div>
              <button
                @click="goToPage(currentPage + 1)"
                :disabled="currentPage >= totalPages"
                class="px-4 py-2 border border-border-dark rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                下一页
              </button>
            </div>
          </div>

          <div v-if="activeTab === 'withdrawals'" class="space-y-6">
            <div class="flex items-center justify-between">
              <h2 class="text-2xl font-bold text-ink-950">提现审核</h2>
              <div class="flex items-center gap-3">
                <select
                  v-model="withdrawalFilter"
                  @change="loadWithdrawals"
                  class="px-4 py-2 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">全部状态</option>
                  <option value="pending">待审核</option>
                  <option value="approved">已通过待打款</option>
                  <option value="completed">已完成</option>
                  <option value="rejected">已拒绝</option>
                </select>
                <button
                  @click="exportWithdrawals"
                  :disabled="loadingWithdrawals"
                  class="px-4 py-2 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                >
                  <span class="material-symbols-outlined !text-xl">download</span>
                  导出Excel
                </button>
                <button @click="loadWithdrawals" :disabled="loadingWithdrawals" class="px-4 py-2 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 disabled:opacity-50">
                  <span v-if="loadingWithdrawals">刷新中...</span>
                  <span v-else>刷新</span>
                </button>
              </div>
            </div>

            <!-- 提现统计 -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div class="bg-white rounded-2xl shadow-sm p-4 border border-border-dark">
                <p class="text-sm text-ink-500">待审核</p>
                <p class="text-2xl font-bold text-yellow-600">{{ withdrawalStats.pending || 0 }}</p>
              </div>
              <div class="bg-white rounded-2xl shadow-sm p-4 border border-border-dark">
                <p class="text-sm text-ink-500">已通过待打款</p>
                <p class="text-2xl font-bold text-blue-600">{{ withdrawalStats.approved || 0 }}</p>
              </div>
              <div class="bg-white rounded-2xl shadow-sm p-4 border border-border-dark">
                <p class="text-sm text-ink-500">已完成</p>
                <p class="text-2xl font-bold text-green-600">{{ withdrawalStats.completed || 0 }}</p>
              </div>
              <div class="bg-white rounded-2xl shadow-sm p-4 border border-border-dark">
                <p class="text-sm text-ink-500">已拒绝</p>
                <p class="text-2xl font-bold text-red-600">{{ withdrawalStats.rejected || 0 }}</p>
              </div>
            </div>

            <!-- 提现列表 -->
            <div class="text-sm text-ink-500">
              共 {{ withdrawalsTotalCount }} 条记录，当前显示第 {{ withdrawalsCurrentPage }} 页
            </div>

            <div class="bg-white rounded-2xl shadow-sm overflow-hidden border border-border-dark">
              <table class="w-full">
                <thead class="bg-background-dark border-b border-border-dark">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">提现单号</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">用户信息</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">收款信息</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">金额</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">状态</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">申请时间</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-ink-700">操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-border-dark">
                  <tr v-if="loadingWithdrawals">
                    <td colspan="7" class="px-6 py-12 text-center text-ink-500">加载中...</td>
                  </tr>
                  <tr v-else-if="withdrawals.length === 0">
                    <td colspan="7" class="px-6 py-12 text-center text-ink-500">暂无提现记录</td>
                  </tr>
                  <tr v-else v-for="withdrawal in withdrawals" :key="withdrawal.id" class="hover:bg-primary-soft transition-colors">
                    <td class="px-4 py-3">
                      <p class="text-sm font-medium text-ink-950">{{ withdrawal.withdrawal_id }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-sm font-medium text-ink-950">{{ withdrawal.username || '未知' }}</p>
                      <p class="text-sm text-ink-500">{{ withdrawal.phone || '-' }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-sm text-ink-700">{{ withdrawal.withdrawal_name || '-' }}</p>
                      <p class="text-sm text-ink-500">{{ getWithdrawalMethodText(withdrawal.withdrawal_method) }}</p>
                      <p class="text-sm text-ink-500 truncate max-w-[200px]">{{ withdrawal.withdrawal_account || '-' }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-sm font-bold text-green-600">¥{{ withdrawal.amount_yuan.toFixed(2) }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <span :class="[
                        'px-2 py-0.5 text-xs font-medium rounded-full inline-flex items-center gap-1 w-fit',
                        withdrawal.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                        withdrawal.status === 'approved' ? 'bg-blue-100 text-blue-700' :
                        withdrawal.status === 'completed' ? 'bg-green-100 text-green-700' :
                        'bg-red-100 text-red-700'
                      ]">
                        <span class="material-symbols-outlined !text-sm">
                          {{ withdrawal.status === 'pending' ? 'pending' :
                             withdrawal.status === 'approved' ? 'check_circle' :
                             withdrawal.status === 'completed' ? 'done' : 'cancel' }}
                        </span>
                        {{ getWithdrawalStatusText(withdrawal.status) }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-sm text-ink-500">
                      {{ formatDate(withdrawal.created_at) }}
                    </td>
                    <td class="px-4 py-3">
                      <div class="flex items-center gap-2">
                        <template v-if="withdrawal.status === 'pending'">
                          <button
                            @click="showApproveModal(withdrawal)"
                            class="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                          >
                            通过
                          </button>
                          <button
                            @click="showRejectModal(withdrawal)"
                            class="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
                          >
                            拒绝
                          </button>
                        </template>
                        <template v-else-if="withdrawal.status === 'approved'">
                          <button
                            @click="markAsPaid(withdrawal.withdrawal_id)"
                            class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                          >
                            标记已打款
                          </button>
                        </template>
                        <span v-else class="text-sm text-ink-500">-</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 分页 -->
            <div v-if="withdrawalsTotalCount > 20" class="flex justify-center gap-2">
              <button
                @click="prevWithdrawalsPage"
                :disabled="withdrawalsCurrentPage <= 1"
                class="px-4 py-2 border border-border-dark rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                上一页
              </button>
              <button
                @click="nextWithdrawalsPage"
                :disabled="withdrawalsCurrentPage * 20 >= withdrawalsTotalCount"
                class="px-4 py-2 border border-border-dark rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                下一页
              </button>
            </div>
          </div>

          <div v-if="activeTab === 'pricing'">
            <BillingConfigManagement />
          </div>

          <div v-if="activeTab === 'config'" class="space-y-6">
            <div class="flex items-center justify-between">
              <h2 class="text-2xl font-bold text-ink-950">系统配置</h2>
              <button @click="loadConfigs" :disabled="loadingConfigs" class="px-4 py-2 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 disabled:opacity-50">
                <span v-if="loadingConfigs">刷新中...</span>
                <span v-else>刷新</span>
              </button>
            </div>

            <!-- API配置 -->
            <div class="bg-white rounded-2xl shadow-sm p-6 border border-border-dark">
              <h3 class="text-lg font-bold text-ink-950 mb-4">API配置</h3>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-ink-700 mb-2">中转站API Key</label>
                  <input
                    v-model="configForm['relay.api_key']"
                    type="password"
                    placeholder="请输入中转站API Key"
                    class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <p class="mt-2 text-sm text-ink-500">服务端已有配置时会显示掩码；未配置时这里会保持为空。</p>
                </div>
              </div>
            </div>

            <!-- 保存按钮 -->
            <div class="flex justify-end gap-3">
              <button
                @click="resetConfigs"
                class="px-6 py-2.5 border border-border-dark rounded-xl hover:bg-gray-50 font-medium"
              >
                重置
              </button>
              <button
                @click="saveConfigs"
                :disabled="savingConfigs"
                class="px-6 py-2.5 bg-primary text-white rounded-xl hover:bg-primary/90 disabled:opacity-50 font-medium"
              >
                <span v-if="savingConfigs">保存中...</span>
                <span v-else>保存配置</span>
              </button>
            </div>
          </div>

          <!-- 案例管理 -->
          <div v-if="activeTab === 'cases'" class="space-y-6">
            <CaseManagement />
          </div>

          <!-- 场景库管理 -->
          <div v-if="activeTab === 'scenes'" class="space-y-6">
            <div class="flex items-center justify-between">
              <h2 class="text-2xl font-bold text-ink-950">场景库管理</h2>
              <button
                @click="showSceneForm = true; editingScene = null"
                class="px-4 py-2 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
              >
                <span class="material-symbols-outlined !text-lg">add</span>
                添加场景
              </button>
            </div>

            <!-- Scene list -->
            <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div v-for="scene in sceneList" :key="scene.id"
                class="rounded-2xl border border-border-dark bg-white p-4 shadow-sm">
                <div class="flex items-start gap-3">
                  <div class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-primary-soft text-2xl">
                    {{ scene.icon || '📁' }}
                  </div>
                  <div class="min-w-0 flex-1">
                    <h4 class="font-semibold text-ink-950">{{ scene.name }}</h4>
                    <p class="mt-0.5 text-xs text-ink-500">{{ scene.category }} · {{ scene.templates?.length || 0 }}个模版</p>
                    <p class="mt-1 text-xs text-ink-700 line-clamp-2">{{ scene.description }}</p>
                  </div>
                </div>
                <div v-if="scene.coverImage" class="mt-3 aspect-video overflow-hidden rounded-xl">
                  <img :src="scene.coverImage" class="h-full w-full object-cover" />
                </div>
                <div class="mt-3 flex gap-2">
                  <el-button size="small" @click="editScene(scene)">
                    <span class="material-symbols-outlined !text-sm">edit</span>编辑
                  </el-button>
                  <el-button size="small" @click="editSceneTemplates(scene)">
                    <span class="material-symbols-outlined !text-sm">list</span>模版
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteScene(scene)">
                    <span class="material-symbols-outlined !text-sm">delete</span>
                  </el-button>
                </div>
              </div>
            </div>

            <!-- Scene form dialog -->
            <el-dialog v-model="showSceneForm" :title="editingScene ? '编辑场景' : '添加场景'" width="min(520px, 90vw)">
              <el-form label-position="top" class="space-y-4">
                <el-form-item label="名称">
                  <el-input v-model="sceneForm.name" placeholder="场景名称" />
                </el-form-item>
                <el-form-item label="图标 (emoji)">
                  <el-input v-model="sceneForm.icon" placeholder="如：📚" />
                </el-form-item>
                <el-form-item label="分类">
                  <el-select v-model="sceneForm.category" placeholder="选择分类" filterable allow-create>
                    <el-option
                      v-for="cat in sceneCategories"
                      :key="cat.id"
                      :label="`${cat.icon || ''} ${cat.name}`"
                      :value="cat.id"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="描述">
                  <el-input v-model="sceneForm.description" type="textarea" :rows="3" placeholder="场景描述" />
                </el-form-item>
                <el-form-item label="封面图片">
                  <el-upload
                    :auto-upload="false"
                    :show-file-list="false"
                    accept="image/*"
                    :on-change="handleSceneCoverUpload"
                  >
                    <el-button>上传封面</el-button>
                  </el-upload>
                  <img v-if="sceneForm.coverImage" :src="sceneForm.coverImage" class="mt-2 h-24 rounded-xl object-cover" />
                </el-form-item>
              </el-form>
              <template #footer>
                <el-button @click="showSceneForm = false">取消</el-button>
                <el-button type="primary" @click="saveScene">保存</el-button>
              </template>
            </el-dialog>

            <!-- Template management dialog -->
            <el-dialog v-model="showTemplateManager" :title="`${editingScene?.name} - 模版管理`" width="min(700px, 95vw)">
              <div class="mb-4 flex items-center justify-between">
                <span class="text-sm text-ink-500">共 {{ editingScene?.templates?.length || 0 }} 个模版</span>
                <el-button size="small" type="primary" @click="addTemplate">
                  <span class="material-symbols-outlined !text-sm">add</span>添加模版
                </el-button>
              </div>
              <div class="space-y-3 max-h-[60vh] overflow-y-auto">
                <div v-for="(tpl, i) in editingScene?.templates || []" :key="i"
                  class="rounded-xl border border-border-dark p-3">
                  <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
                    <el-input v-model="tpl.title" placeholder="模版标题" />
                    <el-input v-model="tpl.type" placeholder="类型（如：海报设计）" />
                    <el-input v-model="tpl.style" placeholder="风格（如：手绘）" />
                    <el-input v-model="tpl.prompt" type="textarea" :rows="2" placeholder="提示词模版" class="md:col-span-2" />
                  </div>
                  <div class="mt-2 flex justify-end">
                    <el-button size="small" type="danger" text @click="removeTemplate(i)">删除</el-button>
                  </div>
                </div>
              </div>
              <template #footer>
                <el-button @click="showTemplateManager = false">关闭</el-button>
                <el-button type="primary" @click="saveSceneTemplates">保存</el-button>
              </template>
            </el-dialog>
          </div>

          <!-- 公告管理 -->
          <div v-if="activeTab === 'announcements'" class="space-y-6">
            <div class="flex items-center justify-between">
              <h2 class="text-2xl font-bold text-ink-950">公告管理</h2>
              <button
                @click="openAnnouncementForm()"
                class="px-4 py-2 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
              >
                <span class="material-symbols-outlined !text-lg">add</span>
                新建公告
              </button>
            </div>

            <!-- 公告列表 -->
            <div class="bg-white rounded-2xl shadow-sm p-6">
              <div v-if="loadingAnnouncements" class="flex items-center justify-center py-12">
                <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
              </div>

              <div v-else-if="announcements.length === 0" class="text-center py-12 text-gray-500">
                <span class="material-symbols-outlined !text-5xl mb-3">campaign</span>
                <p class="text-lg">暂无公告</p>
                <p class="text-sm mt-1">点击上方按钮创建第一个公告</p>
              </div>

              <div v-else class="space-y-4">
                <div
                  v-for="announcement in announcements"
                  :key="announcement.id"
                  class="p-4 border border-gray-200 dark:border-gray-700 rounded-xl hover:shadow-md transition-shadow"
                >
                  <div class="flex items-start justify-between">
                    <div class="flex-1">
                      <div class="flex items-center gap-2 mb-2">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                          {{ announcement.title }}
                        </h3>
                        <span
                          class="text-xs px-2 py-0.5 rounded-full"
                          :class="priorityBadgeClasses[announcement.priority]"
                        >
                          {{ priorityLabels[announcement.priority] }}
                        </span>
                        <span
                          v-if="announcement.is_pinned"
                          class="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
                        >
                          置顶
                        </span>
                        <span
                          :class="[
                            'text-xs px-2 py-0.5 rounded-full',
                            announcement.is_published
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                              : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                          ]"
                        >
                          {{ announcement.is_published ? '已发布' : '草稿' }}
                        </span>
                      </div>

                      <p
                        class="text-sm text-gray-600 dark:text-gray-300 mb-2 line-clamp-2"
                        v-html="stripHtml(announcement.content)"
                      ></p>

                      <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                        <span>浏览: {{ announcement.view_count }}</span>
                        <span>点击: {{ announcement.click_count }}</span>
                        <span>{{ formatTime(announcement.published_at) }}</span>
                      </div>
                    </div>

                    <div class="flex items-center gap-2 ml-4">
                      <button
                        @click="editAnnouncement(announcement.id)"
                        class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        title="编辑"
                      >
                        <span class="material-symbols-outlined !text-lg text-gray-600 dark:text-gray-400">edit</span>
                      </button>
                      <button
                        v-if="!announcement.is_published"
                        @click="publishAnnouncement(announcement.id)"
                        class="p-2 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                        title="发布"
                      >
                        <span class="material-symbols-outlined !text-lg text-green-600 dark:text-green-400">send</span>
                      </button>
                      <button
                        @click="deleteAnnouncement(announcement.id)"
                        class="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                        title="删除"
                      >
                        <span class="material-symbols-outlined !text-lg text-red-600 dark:text-red-400">delete</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>

    <!-- 用户详情弹窗 -->
    <div v-if="showDetailModal && selectedUserDetail" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div @click="showDetailModal = false; selectedUserDetail = null" class="absolute inset-0 bg-black/50"></div>
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        <div class="p-6 border-b border-border-dark flex items-center justify-between">
          <h2 class="text-xl font-bold text-ink-950">用户详情</h2>
          <button @click="showDetailModal = false; selectedUserDetail = null" class="text-ink-500 hover:text-ink-700">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[calc(90vh-80px)] space-y-6">
          <!-- 基本信息 -->
          <section>
            <h3 class="text-sm font-semibold text-ink-500 uppercase tracking-wider mb-3">基本信息</h3>
            <div class="grid grid-cols-2 gap-4 bg-gray-50 rounded-xl p-4">
              <div>
                <p class="text-xs text-ink-500 mb-1">用户ID</p>
                <p class="text-sm font-mono text-ink-700">{{ selectedUserDetail.id?.slice(0, 12) }}...</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">用户名</p>
                <p class="text-sm text-ink-700">{{ selectedUserDetail.username || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">手机号</p>
                <p class="text-sm text-ink-700">{{ selectedUserDetail.phone || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">手机验证</p>
                <p class="text-sm">
                  <span :class="selectedUserDetail.phone_verified ? 'text-green-600' : 'text-red-600'">
                    {{ selectedUserDetail.phone_verified ? '已验证' : '未验证' }}
                  </span>
                </p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">状态</p>
                <span :class="[
                  'px-2 py-0.5 text-xs font-medium rounded-full',
                  selectedUserDetail.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                ]">
                  {{ selectedUserDetail.status === 'active' ? '活跃' : '已封禁' }}
                </span>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">角色</p>
                <span :class="[
                  'px-2 py-0.5 text-xs font-medium rounded-full',
                  selectedUserDetail.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'
                ]">
                  {{ selectedUserDetail.role === 'admin' ? '管理员' : '普通用户' }}
                </span>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">注册时间</p>
                <p class="text-sm text-ink-700">{{ formatDate(selectedUserDetail.created_at) }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">最后登录</p>
                <p class="text-sm text-ink-700">{{ formatDate(selectedUserDetail.last_login_at) }}</p>
              </div>
            </div>
          </section>

          <!-- 账户信息 -->
          <section>
            <h3 class="text-sm font-semibold text-ink-500 uppercase tracking-wider mb-3">账户信息</h3>
            <div class="grid grid-cols-3 gap-4 bg-gray-50 rounded-xl p-4">
              <div>
                <p class="text-xs text-ink-500 mb-1">积分</p>
                <p class="text-lg font-bold text-ink-950">{{ selectedUserDetail.points.toLocaleString() }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">余额</p>
                <p class="text-lg font-bold text-green-600">¥{{ (selectedUserDetail.balance / 100).toFixed(2) }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">赠送积分</p>
                <p class="text-lg font-bold text-purple-600">{{ selectedUserDetail.gift_points.toLocaleString() }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">总生成数</p>
                <p class="text-sm text-ink-700">{{ selectedUserDetail.total_generated }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">总消费</p>
                <p class="text-sm text-ink-700">¥{{ (selectedUserDetail.total_spent / 100).toFixed(2) }}</p>
              </div>
            </div>
          </section>

          <!-- 邀请信息 -->
          <section>
            <h3 class="text-sm font-semibold text-ink-500 uppercase tracking-wider mb-3">邀请信息</h3>
            <div class="grid grid-cols-2 gap-4 bg-gray-50 rounded-xl p-4">
              <div>
                <p class="text-xs text-ink-500 mb-1">我的邀请码</p>
                <p class="text-sm font-mono text-ink-700">{{ selectedUserDetail.invite_code || '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">邀请人数</p>
                <p class="text-sm text-ink-700">{{ selectedUserDetail.invite_count }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">邀请人ID</p>
                <p class="text-sm font-mono text-ink-700">{{ selectedUserDetail.inviter_id ? selectedUserDetail.inviter_id.slice(0, 12) + '...' : '-' }}</p>
              </div>
            </div>
          </section>

          <!-- 签到信息 -->
          <section>
            <h3 class="text-sm font-semibold text-ink-500 uppercase tracking-wider mb-3">签到信息</h3>
            <div class="grid grid-cols-2 gap-4 bg-gray-50 rounded-xl p-4">
              <div>
                <p class="text-xs text-ink-500 mb-1">最后签到</p>
                <p class="text-sm text-ink-700">{{ formatDate(selectedUserDetail.last_checkin_date) }}</p>
              </div>
              <div>
                <p class="text-xs text-ink-500 mb-1">连续签到</p>
                <p class="text-sm text-ink-700">{{ selectedUserDetail.consecutive_checkin_days }} 天</p>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>

    <!-- 积分调整弹窗 -->
    <div v-if="showPointsModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div @click="showPointsModal = false" class="absolute inset-0 bg-black/50"></div>
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <h3 class="text-xl font-bold text-ink-950 mb-4">调整积分</h3>
        <div class="space-y-4">
          <div>
            <p class="text-sm text-ink-500 mb-1">当前积分</p>
            <p class="text-lg font-bold text-ink-950">{{ selectedUserDetail?.points?.toLocaleString() || 0 }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-2">调整数量</label>
            <input
              v-model.number="pointsForm.amount"
              type="number"
              placeholder="正数增加，负数减少"
              class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <p class="text-xs text-ink-500 mt-1">
              调整后: <span class="font-semibold">{{ adjustedPoints.toLocaleString() }}</span> 积分
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-2">调整原因</label>
            <textarea
              v-model="pointsForm.reason"
              rows="3"
              placeholder="请输入调整原因"
              class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
            ></textarea>
          </div>
          <div class="flex gap-3">
            <button
              @click="showPointsModal = false"
              class="flex-1 px-4 py-2.5 border border-border-dark rounded-xl hover:bg-gray-50"
            >
              取消
            </button>
            <button
              @click="adjustPoints"
              :disabled="!pointsForm.amount || !pointsForm.reason"
              class="flex-1 px-4 py-2.5 bg-primary text-white rounded-xl hover:bg-primary/90 disabled:opacity-50"
            >
              确认
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 余额调整弹窗 -->
    <div v-if="showBalanceModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div @click="showBalanceModal = false" class="absolute inset-0 bg-black/50"></div>
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <h3 class="text-xl font-bold text-ink-950 mb-4">调整余额</h3>
        <div class="space-y-4">
          <div>
            <p class="text-sm text-ink-500 mb-1">当前余额</p>
            <p class="text-lg font-bold text-green-600">¥{{ ((selectedUserDetail?.balance || 0) / 100).toFixed(2) }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-2">调整金额（元）</label>
            <input
              v-model.number="balanceForm.amount"
              type="number"
              step="0.01"
              placeholder="正数增加，负数减少"
              class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <p class="text-xs text-ink-500 mt-1">
              调整后: <span class="font-semibold">¥{{ adjustedBalanceYuan }}</span>
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-2">调整原因</label>
            <textarea
              v-model="balanceForm.reason"
              rows="3"
              placeholder="请输入调整原因"
              class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
            ></textarea>
          </div>
          <div class="flex gap-3">
            <button
              @click="showBalanceModal = false"
              class="flex-1 px-4 py-2.5 border border-border-dark rounded-xl hover:bg-gray-50"
            >
              取消
            </button>
            <button
              @click="adjustBalance"
              :disabled="!balanceForm.amount || !balanceForm.reason"
              class="flex-1 px-4 py-2.5 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50"
            >
              确认
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 封禁用户弹窗 -->
    <div v-if="showBanModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div @click="showBanModal = false" class="absolute inset-0 bg-black/50"></div>
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <h3 class="text-xl font-bold text-ink-950 mb-4">封禁用户</h3>
        <div class="space-y-4">
          <div class="bg-red-50 border border-red-200 rounded-xl p-4">
            <p class="text-sm text-red-700">确定要封禁用户 <strong>{{ selectedUserDetail?.username || selectedUserDetail?.phone }}</strong> 吗？</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-ink-700 mb-2">封禁原因</label>
            <textarea
              v-model="banForm.reason"
              rows="3"
              placeholder="请输入封禁原因"
              class="w-full px-4 py-2.5 border border-border-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
            ></textarea>
          </div>
          <div class="flex gap-3">
            <button
              @click="showBanModal = false"
              class="flex-1 px-4 py-2.5 border border-border-dark rounded-xl hover:bg-gray-50"
            >
              取消
            </button>
            <button
              @click="banUser"
              :disabled="!banForm.reason"
              class="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 disabled:opacity-50"
            >
              确认封禁
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 成功提示弹窗 -->
    <div v-if="showSuccessModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div @click="showSuccessModal = false" class="absolute inset-0 bg-black/50"></div>
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span class="material-symbols-outlined !text-3xl text-green-600">check_circle</span>
        </div>
        <h3 class="text-xl font-bold text-ink-950 mb-2">操作成功</h3>
        <p class="text-ink-700 text-base mb-6">{{ successMessage }}</p>
        <button
          @click="showSuccessModal = false"
          class="w-full px-4 py-2.5 bg-primary text-white rounded-xl hover:bg-primary/90 font-medium"
        >
          确定
        </button>
      </div>
    </div>

    <!-- 公告表单弹窗 -->
    <div
      v-if="showAnnouncementForm"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- 头部 -->
        <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">
            {{ editingAnnouncementId ? '编辑公告' : '新建公告' }}
          </h2>
          <button
            @click="handleAnnouncementFormCancel"
            class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <span class="material-symbols-outlined !text-2xl text-gray-500">close</span>
          </button>
        </div>

        <!-- 内容 -->
        <div class="flex-1 overflow-y-auto p-6">
          <AnnouncementForm
            :announcement-id="editingAnnouncementId"
            @submit="handleAnnouncementFormSubmit"
            @cancel="handleAnnouncementFormCancel"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/store/useAppStore'
import { useAuthStore } from '@/store/useAuthStore'
import { api, type SystemConfigItem } from '@/services/api'
import CaseManagement from '@/components/admin/CaseManagement.vue'
import AnnouncementForm from '@/components/admin/AnnouncementForm.vue'
import BillingConfigManagement from '@/components/admin/BillingConfigManagement.vue'

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

const activeTab = ref('overview')
const loading = ref(false)

// 场景库管理状态
const sceneList = ref<any[]>([])
const showSceneForm = ref(false)
const showTemplateManager = ref(false)
const editingScene = ref<any>(null)
const sceneForm = ref({ name: '', icon: '', category: 'education', description: '', coverImage: '' })

function editScene(scene: any) {
  editingScene.value = scene
  sceneForm.value = { name: scene.name, icon: scene.icon, category: scene.category, description: scene.description, coverImage: scene.coverImage || '' }
  showSceneForm.value = true
}

function editSceneTemplates(scene: any) {
  editingScene.value = scene
  showTemplateManager.value = true
}

async function syncScenesToServer() {
  try {
    const categories = sceneCategories.value.length > 0 ? sceneCategories.value : []
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/v1/admin/system-config/scenes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ categories, scenes: sceneList.value })
    })
    if (res.ok) {
      const data = await res.json()
      console.log('场景库同步成功:', data.message)
    } else {
      console.error('场景库同步失败:', res.status)
    }
  } catch (e) {
    console.error('Failed to sync scenes to server:', e)
  }
}

function saveScene() {
  const data = { ...sceneForm.value, id: editingScene.value?.id || `scene_${Date.now()}`, templates: editingScene.value?.templates || [], templateCount: editingScene.value?.templates?.length || 0 }
  if (editingScene.value) {
    const idx = sceneList.value.findIndex(s => s.id === editingScene.value.id)
    if (idx >= 0) sceneList.value[idx] = { ...sceneList.value[idx], ...data }
    else sceneList.value.push(data)
  } else {
    sceneList.value.push(data)
  }
  showSceneForm.value = false
  syncScenesToServer()
}

function deleteScene(scene: any) {
  sceneList.value = sceneList.value.filter(s => s.id !== scene.id)
  syncScenesToServer()
}

function addTemplate() {
  if (!editingScene.value) return
  if (!editingScene.value.templates) editingScene.value.templates = []
  editingScene.value.templates.push({ id: `tpl_${Date.now()}`, title: '', type: '', style: '', prompt: '', exampleImage: '' })
}

function removeTemplate(index: number) {
  editingScene.value?.templates?.splice(index, 1)
}

function saveSceneTemplates() {
  if (!editingScene.value) return
  editingScene.value.templateCount = editingScene.value.templates?.length || 0
  const idx = sceneList.value.findIndex(s => s.id === editingScene.value.id)
  if (idx >= 0) sceneList.value[idx] = { ...editingScene.value }
  showTemplateManager.value = false
  syncScenesToServer()
}

function handleSceneCoverUpload(uploadFile: any) {
  const file = uploadFile?.raw || uploadFile
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => { sceneForm.value.coverImage = e.target?.result as string }
  reader.readAsDataURL(file)
}

const sceneCategories = ref([])

// Load ALL scenes from API (including defaults)
async function loadScenesFromServer() {
  try {
    const res = await fetch('/api/v1/admin/system-config/scenes')
    const data = await res.json()
    if (data.scenes?.length) {
      sceneList.value = data.scenes
    }
    if (data.categories?.length) sceneCategories.value = data.categories
    // 如果没有分类数据，从场景中自动提取
    if (!sceneCategories.value.length && sceneList.value.length) {
      const catMap = new Map()
      sceneList.value.forEach((s: any) => {
        if (s.category && !catMap.has(s.category)) {
          catMap.set(s.category, { id: s.category, name: s.category, icon: '' })
        }
      })
      sceneCategories.value = Array.from(catMap.values())
    }
  } catch {
    // Fallback: load from static JSON
    try {
      const res = await fetch('/data/scenes.json')
      const data = await res.json()
      if (data.scenes?.length) sceneList.value = data.scenes
      if (data.categories?.length) sceneCategories.value = data.categories
    } catch {}
  }
}
loadScenesFromServer()

// 公告管理状态
const showAnnouncementForm = ref(false)
const editingAnnouncementId = ref<string | null>(null)
const announcements = ref<any[]>([])
const loadingAnnouncements = ref(false)

// 优先级样式
const priorityBadgeClasses = {
  urgent: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  low: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
}

const priorityLabels = {
  urgent: '紧急',
  high: '重要',
  normal: '普通',
  low: '低',
}

// 侧边栏折叠状态
const sidebarCollapsed = ref(localStorage.getItem('adminSidebarCollapsed') === 'true')

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('adminSidebarCollapsed', sidebarCollapsed.value.toString())
}

const users = ref([])
const statistics = ref({
  total_users: 0,
  active_users: 0,
  total_generated: 0,
  total_revenue: 0,
  today_users: 0,
  today_generated: 0,
  today_revenue: 0,
})

// 搜索和筛选
const searchKeyword = ref('')
const filterStatus = ref('')
const filterRole = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)

// 计算总页数
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

// 系统配置
const SYSTEM_CONFIG_MASK = '••••••••'
const configs = ref<SystemConfigItem[]>([])
const configForm = ref<Record<string, string>>({
  'relay.api_key': '',
})
const originalConfigs = ref<Record<string, string>>({})
const loadingConfigs = ref(false)
const savingConfigs = ref(false)

// 提现相关
const withdrawals = ref([])
const withdrawalFilter = ref('')
const withdrawalStats = ref({
  pending: 0,
  approved: 0,
  completed: 0,
  rejected: 0
})
const withdrawalsCurrentPage = ref(1)
const withdrawalsTotalCount = ref(0)
const loadingWithdrawals = ref(false)

// 用户详情
const showDetailModal = ref(false)
const showPointsModal = ref(false)
const showBalanceModal = ref(false)
const showBanModal = ref(false)
const showSuccessModal = ref(false)
const successMessage = ref('')
const selectedUser = ref(null)
const selectedUserDetail = ref(null)

// 表单
const pointsForm = ref({
  amount: 0,
  reason: ''
})
const balanceForm = ref({
  amount: 0,
  reason: ''
})
const banForm = ref({
  reason: ''
})

// 计算调整后的积分
const adjustedPoints = computed(() => {
  return ((selectedUserDetail.value?.points || 0) + (pointsForm.value.amount || 0))
})

// 计算调整后的余额（分）- 输入是元，需要转换为分
const adjustedBalance = computed(() => {
  const amountInFen = Math.round((balanceForm.value.amount || 0) * 100) // 元转分
  return ((selectedUserDetail.value?.balance || 0) + amountInFen)
})

// 计算调整后的余额（元）- 用于显示
const adjustedBalanceYuan = computed(() => {
  return (adjustedBalance.value / 100).toFixed(2)
})

function goHome() {
  router.push('/')
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function loadStatistics() {
  try {
    const stats = await api.getAdminStatistics()
    statistics.value = stats
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

async function loadUsers() {
  loading.value = true
  try {
    const params: any = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterRole.value) params.role = filterRole.value

    const data = await api.getAdminUsers(params)
    users.value = data

    // 加载总数
    const countData = await api.getAdminUsersCount({
      keyword: searchKeyword.value || undefined,
      status: filterStatus.value || undefined,
      role: filterRole.value || undefined,
    })
    totalCount.value = countData.count
  } catch (error) {
    console.error('加载用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadUsers()
}

function goToPage(page) {
  const pageNum = typeof page === 'string' ? parseInt(page) : page
  if (pageNum >= 1 && pageNum <= totalPages.value) {
    currentPage.value = pageNum
    loadUsers()
  }
}

async function viewUserDetail(user) {
  try {
    const detail = await api.getAdminUserDetail(user.id)
    selectedUserDetail.value = detail
    selectedUser.value = user
    showDetailModal.value = true
  } catch (error) {
    console.error('加载用户详情失败:', error)
  }
}

// 打开积分调整弹窗
function openPointsModal() {
  pointsForm.value = { amount: 0, reason: '' }
  showPointsModal.value = true
}

// 打开余额调整弹窗
function openBalanceModal() {
  balanceForm.value = { amount: 0, reason: '' }
  showBalanceModal.value = true
}

// 打开封禁弹窗
function openBanModal() {
  banForm.value = { reason: '' }
  showBanModal.value = true
}

// 从列表直接打开积分调整弹窗
async function openPointsModalForUser(user) {
  try {
    const detail = await api.getAdminUserDetail(user.id)
    selectedUserDetail.value = detail
    selectedUser.value = user
    pointsForm.value = { amount: 0, reason: '' }
    showPointsModal.value = true
  } catch (error) {
    console.error('加载用户详情失败:', error)
  }
}

// 从列表直接打开余额调整弹窗
async function openBalanceModalForUser(user) {
  try {
    const detail = await api.getAdminUserDetail(user.id)
    selectedUserDetail.value = detail
    selectedUser.value = user
    balanceForm.value = { amount: 0, reason: '' }
    showBalanceModal.value = true
  } catch (error) {
    console.error('加载用户详情失败:', error)
  }
}

// 从列表直接打开封禁弹窗
async function openBanModalForUser(user) {
  try {
    const detail = await api.getAdminUserDetail(user.id)
    selectedUserDetail.value = detail
    selectedUser.value = user
    banForm.value = { reason: '' }
    showBanModal.value = true
  } catch (error) {
    console.error('加载用户详情失败:', error)
  }
}

// 从列表直接解封用户
async function unbanUserDirect(user) {
  if (!confirm('确定要解封该用户吗？')) return

  try {
    await api.unbanUser(user.id)
    showSuccess('用户已解封')
    await loadUsers()
  } catch (error) {
    console.error('解封用户失败:', error)
    alert('解封用户失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 从列表直接设置管理员
async function setAdminDirect(user) {
  if (!confirm('确定要将该用户设置为管理员吗？')) return

  try {
    await api.setAdmin(user.id)
    showSuccess('已设置为管理员')
    await loadUsers()
  } catch (error) {
    console.error('设置管理员失败:', error)
    alert('设置管理员失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 从列表直接取消管理员
async function removeAdminDirect(user) {
  if (!confirm('确定要取消该用户的管理员权限吗？')) return

  try {
    await api.removeAdmin(user.id)
    showSuccess('已取消管理员权限')
    await loadUsers()
  } catch (error) {
    console.error('取消管理员失败:', error)
    alert('取消管理员失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 显示成功提示
function showSuccess(message: string) {
  successMessage.value = message
  showSuccessModal.value = true
}

// 调整积分
async function adjustPoints() {
  if (!selectedUserDetail.value) return
  try {
    await api.adjustUserPoints(selectedUserDetail.value.id, {
      points_change: pointsForm.value.amount,
      reason: pointsForm.value.reason
    })
    showSuccessModal.value = false
    showPointsModal.value = false
    showSuccess(`积分调整成功！调整 ${pointsForm.value.amount > 0 ? '+' : ''}${pointsForm.value.amount} 分`)
    // 重新加载用户详情
    await viewUserDetail(selectedUser.value)
    // 重新加载列表
    await loadUsers()
  } catch (error) {
    console.error('调整积分失败:', error)
    alert('调整积分失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 调整余额
async function adjustBalance() {
  if (!selectedUserDetail.value) return
  try {
    // 将元转换为分（后端使用分作为单位）
    const amountInFen = Math.round(balanceForm.value.amount * 100)
    await api.adjustUserBalance(selectedUserDetail.value.id, {
      points_change: amountInFen,
      reason: balanceForm.value.reason
    })
    showBalanceModal.value = false
    showSuccess(`余额调整成功！调整 ${balanceForm.value.amount > 0 ? '+' : ''}¥${balanceForm.value.amount.toFixed(2)}`)
    // 重新加载用户详情
    await viewUserDetail(selectedUser.value)
    // 重新加载列表
    await loadUsers()
  } catch (error) {
    console.error('调整余额失败:', error)
    alert('调整余额失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 封禁用户
async function banUser() {
  if (!selectedUserDetail.value) return
  try {
    await api.banUser(selectedUserDetail.value.id, {
      reason: banForm.value.reason
    })
    showBanModal.value = false
    showDetailModal.value = false
    showSuccess('用户已封禁')
    await loadUsers()
  } catch (error) {
    console.error('封禁用户失败:', error)
    alert('封禁用户失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 解封用户
async function unbanUser() {
  if (!selectedUserDetail.value) return
  if (!confirm('确定要解封该用户吗？')) return

  try {
    await api.unbanUser(selectedUserDetail.value.id)
    showDetailModal.value = false
    showSuccess('用户已解封')
    await loadUsers()
  } catch (error) {
    console.error('解封用户失败:', error)
    alert('解封用户失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 设置管理员
async function setAdmin() {
  if (!selectedUserDetail.value) return
  if (!confirm('确定要将该用户设置为管理员吗？')) return

  try {
    await api.setAdmin(selectedUserDetail.value.id)
    showDetailModal.value = false
    showSuccess('已设置为管理员')
    await loadUsers()
  } catch (error) {
    console.error('设置管理员失败:', error)
    alert('设置管理员失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 取消管理员
async function removeAdmin() {
  if (!selectedUserDetail.value) return
  if (!confirm('确定要取消该用户的管理员权限吗？')) return

  try {
    await api.removeAdmin(selectedUserDetail.value.id)
    showDetailModal.value = false
    showSuccess('已取消管理员权限')
    await loadUsers()
  } catch (error) {
    console.error('取消管理员失败:', error)
    alert('取消管理员失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 加载系统配置
async function loadConfigs() {
  loadingConfigs.value = true
  try {
    configs.value = await api.getSystemConfigs()
    const relayApiKeyConfig = configs.value.find(config => config.config_key === 'relay.api_key')
    const relayApiKeyValue = relayApiKeyConfig?.config_value || ''

    configForm.value['relay.api_key'] = relayApiKeyValue
    originalConfigs.value = {
      'relay.api_key': relayApiKeyValue,
    }
  } catch (error) {
    console.error('加载系统配置失败:', error)
    alert('加载系统配置失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loadingConfigs.value = false
  }
}

// 保存系统配置
async function saveConfigs() {
  savingConfigs.value = true
  try {
    const changedConfigs: Record<string, string> = {}
    const currentApiKey = configForm.value['relay.api_key'] || ''
    const originalApiKey = originalConfigs.value['relay.api_key'] || ''

    if (currentApiKey !== originalApiKey && currentApiKey !== SYSTEM_CONFIG_MASK) {
      changedConfigs['relay.api_key'] = currentApiKey
    }

    if (Object.keys(changedConfigs).length === 0) {
      alert('没有修改任何配置')
      return
    }

    await api.batchUpdateSystemConfigs(changedConfigs)

    // 更新原始配置
    originalConfigs.value = { ...configForm.value }

    alert('配置保存成功！部分配置需要重启服务器后才能生效。')
    await loadConfigs()
  } catch (error) {
    console.error('保存系统配置失败:', error)
    alert('保存系统配置失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    savingConfigs.value = false
  }
}

// 重置配置
function resetConfigs() {
  configForm.value['relay.api_key'] = originalConfigs.value['relay.api_key'] || ''
}

// 加载提现记录
async function loadWithdrawals() {
  loadingWithdrawals.value = true
  try {
    const offset = (withdrawalsCurrentPage.value - 1) * 20
    withdrawals.value = await api.getWithdrawalsList({
      status: withdrawalFilter.value || undefined,
      limit: 20,
      offset
    })

    // 获取总数
    const countResult = await api.getWithdrawalsCount({
      status: withdrawalFilter.value || undefined
    })
    withdrawalsTotalCount.value = countResult.count

    // 获取各状态统计
    const [pendingResult, approvedResult, completedResult, rejectedResult] = await Promise.all([
      api.getWithdrawalsCount({ status: 'pending' }),
      api.getWithdrawalsCount({ status: 'approved' }),
      api.getWithdrawalsCount({ status: 'completed' }),
      api.getWithdrawalsCount({ status: 'rejected' })
    ])

    withdrawalStats.value = {
      pending: pendingResult.count,
      approved: approvedResult.count,
      completed: completedResult.count,
      rejected: rejectedResult.count
    }
  } catch (error) {
    console.error('加载提现记录失败:', error)
    alert('加载提现记录失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loadingWithdrawals.value = false
  }
}

// 审核通过提现
async function approveWithdrawal(withdrawalId: string, note?: string) {
  if (!confirm('确定要通过此提现申请吗？通过后将扣除用户余额。')) {
    return
  }

  try {
    await api.approveWithdrawal(withdrawalId, { note })
    alert('提现申请已通过')
    await loadWithdrawals()
  } catch (error) {
    console.error('审核通过失败:', error)
    alert('审核通过失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 审核拒绝提现
async function rejectWithdrawal(withdrawalId: string, reason: string) {
  if (!reason) {
    alert('请输入拒绝原因')
    return
  }

  try {
    await api.rejectWithdrawal(withdrawalId, { reason })
    alert('提现申请已拒绝')
    await loadWithdrawals()
  } catch (error) {
    console.error('审核拒绝失败:', error)
    alert('审核拒绝失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 标记已打款
async function markAsPaid(withdrawalId: string) {
  const proof = prompt('请输入支付凭证（可选）')
  try {
    await api.markWithdrawalPaid(withdrawalId, { payment_proof: proof || undefined })
    alert('已标记为已打款')
    await loadWithdrawals()
  } catch (error) {
    console.error('标记已打款失败:', error)
    alert('标记已打款失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 导出提现记录
async function exportWithdrawals() {
  try {
    const blob = await api.exportWithdrawals()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `withdrawals_${new Date().getTime()}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出失败:', error)
    alert('导出失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 显示审核通过弹窗
function showApproveModal(withdrawal: any) {
  const note = prompt('审核备注（可选）')
  if (note !== null) {
    approveWithdrawal(withdrawal.withdrawal_id, note || undefined)
  }
}

// 显示审核拒绝弹窗
function showRejectModal(withdrawal: any) {
  const reason = prompt('请输入拒绝原因')
  if (reason) {
    rejectWithdrawal(withdrawal.withdrawal_id, reason)
  }
}

// 提现记录分页
function prevWithdrawalsPage() {
  if (withdrawalsCurrentPage.value > 1) {
    withdrawalsCurrentPage.value--
    loadWithdrawals()
  }
}

function nextWithdrawalsPage() {
  if (withdrawalsCurrentPage.value * 20 < withdrawalsTotalCount.value) {
    withdrawalsCurrentPage.value++
    loadWithdrawals()
  }
}

// 获取提现状态文本
function getWithdrawalStatusText(status: string) {
  const statusMap: Record<string, string> = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 获取提现方式文本
function getWithdrawalMethodText(method: string) {
  const methodMap: Record<string, string> = {
    'wechat': '微信',
    'alipay': '支付宝',
    'bank': '银行卡'
  }
  return methodMap[method] || method
}

// 公告管理功能
async function loadAnnouncements() {
  loadingAnnouncements.value = true
  try {
    const result = await api.getAdminAnnouncements()
    announcements.value = result.items
  } catch (error) {
    console.error('加载公告失败:', error)
  } finally {
    loadingAnnouncements.value = false
  }
}

// 在打开表单前检查权限
function openAnnouncementForm(announcementId?: string) {
  // 从authStore获取当前用户角色
  const currentRole = authStore.userRole

  if (currentRole !== 'admin') {
    alert('您需要管理员权限才能管理公告')
    return
  }

  editingAnnouncementId.value = announcementId || null
  showAnnouncementForm.value = true
}

function editAnnouncement(id: string) {
  openAnnouncementForm(id)
}

async function publishAnnouncement(id: string) {
  if (!confirm('确定要发布此公告吗？')) return

  try {
    await api.publishAnnouncement(id)
    alert('公告已发布')
    await loadAnnouncements()
  } catch (error) {
    console.error('发布公告失败:', error)
    alert('发布失败，请重试')
  }
}

async function deleteAnnouncement(id: string) {
  if (!confirm('确定要删除此公告吗？')) return

  try {
    await api.deleteAnnouncement(id)
    alert('公告已删除')
    await loadAnnouncements()
  } catch (error) {
    console.error('删除公告失败:', error)
    alert('删除失败，请重试')
  }
}

function handleAnnouncementFormSubmit() {
  showAnnouncementForm.value = false
  editingAnnouncementId.value = null
  loadAnnouncements()
}

function handleAnnouncementFormCancel() {
  showAnnouncementForm.value = false
  editingAnnouncementId.value = null
}

function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

function formatTime(dateString: string | null): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 监听标签页切换，加载公告数据
watch(activeTab, (newTab) => {
  if (newTab === 'announcements' && announcements.value.length === 0) {
    loadAnnouncements()
  }
})

onMounted(() => {
  loadStatistics()
  loadUsers()
})

// 监听标签页切换
watch(activeTab, (newTab) => {
  if (newTab === 'config' && configs.value.length === 0) {
    loadConfigs()
  } else if (newTab === 'withdrawals' && withdrawals.value.length === 0) {
    loadWithdrawals()
  }
})
</script>
