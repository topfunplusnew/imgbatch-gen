<template>
  <main class="multi-guide-view flex h-full min-h-0 flex-1 flex-col overflow-y-auto">
    <div class="mx-auto flex w-full max-w-[1380px] flex-1 flex-col gap-6 px-4 pb-10 pt-6 xs:px-6 md:px-8 md:gap-8 md:pt-8">
      <section class="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_340px]">
        <div class="space-y-6">
          <section class="glass-panel rounded-[30px] p-5 md:p-7">
            <div class="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/6 px-3 py-1 text-xs font-semibold tracking-[0.18em] text-primary">
              <span class="material-symbols-outlined !text-sm">school</span>
              上手教程
            </div>
            <h1 class="mt-4 text-3xl font-bold tracking-tight text-ink-950 md:text-[2.7rem] md:leading-[1.1]">
              多图创作指南
            </h1>
            <p class="mt-3 max-w-3xl text-sm leading-6 text-ink-500 md:text-base">
              把原来 `/multi` 右侧的教程、适合人群和积分信息单独收到了这里。先挑一个示例，系统会自动带你回到多图创作页并填好内容。
            </p>

            <div class="mt-5 flex flex-wrap gap-2.5">
              <span class="hero-chip">
                <span class="material-symbols-outlined !text-sm">bolt</span>
                一键带入示例
              </span>
              <span class="hero-chip">
                <span class="material-symbols-outlined !text-sm">view_carousel</span>
                支持多张连续生成
              </span>
              <span class="hero-chip">
                <span class="material-symbols-outlined !text-sm">history</span>
                历史结果可回看放大
              </span>
            </div>

            <div class="mt-6 flex flex-wrap gap-3">
              <button class="primary-action-button" @click="router.push('/multi')">
                <span class="material-symbols-outlined !text-base">auto_awesome</span>
                去多图创作
              </button>
              <button class="secondary-ghost-button" @click="router.push('/scenes')">
                <span class="material-symbols-outlined !text-sm">grid_view</span>
                打开场景库
              </button>
            </div>
          </section>

          <section class="glass-panel rounded-[28px] p-5 md:p-6">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined !text-xl text-primary">school</span>
              <h2 class="text-lg font-bold text-ink-950">上手教程</h2>
            </div>
            <p class="mt-2 text-sm leading-6 text-ink-500">
              第一次使用可以直接套用示例。系统会自动把内容拆成多张图，再到下方历史里回看与放大。
            </p>

            <div class="mt-4 grid gap-3 md:grid-cols-3">
              <div v-for="step in quickStartSteps" :key="step.title" class="quick-step-card">
                <div class="quick-step__index">{{ step.index }}</div>
                <div>
                  <p class="text-sm font-semibold text-ink-900">{{ step.title }}</p>
                  <p class="mt-1 text-xs leading-5 text-ink-500">{{ step.description }}</p>
                </div>
              </div>
            </div>

            <div class="mt-5 grid gap-3">
              <button
                v-for="example in tutorialExamples"
                :key="example.id"
                class="tutorial-example"
                @click="openComposerWithExample(example)"
              >
                <div>
                  <p class="text-sm font-semibold text-ink-900">{{ example.title }}</p>
                  <p class="mt-1 text-xs leading-5 text-ink-500">{{ example.description }}</p>
                </div>
                <span class="material-symbols-outlined !text-lg text-primary">north_east</span>
              </button>
            </div>

            <div class="mt-4 flex flex-wrap gap-2">
              <button class="secondary-ghost-button" @click="router.push('/scenes')">
                <span class="material-symbols-outlined !text-sm">grid_view</span>
                打开场景库
              </button>
              <button class="secondary-ghost-button" @click="openComposerWithExample(tutorialExamples[0])">
                <span class="material-symbols-outlined !text-sm">play_circle</span>
                一键填入示例
              </button>
            </div>
          </section>

          <section class="glass-panel rounded-[28px] p-5 md:p-6">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined !text-xl text-primary">groups</span>
              <h2 class="text-lg font-bold text-ink-950">适合这些人群</h2>
            </div>
            <p class="mt-2 text-sm leading-6 text-ink-500">
              我把人群提示做成了更醒目的标签，方便用户快速判断自己适合做哪类图。
            </p>

            <div class="mt-4 flex flex-wrap gap-2.5">
              <span v-for="audience in audienceChips" :key="audience" class="audience-chip">
                <span class="material-symbols-outlined !text-sm">arrow_outward</span>
                {{ audience }}
              </span>
            </div>

            <div class="mt-5 rounded-[22px] border border-primary/10 bg-primary/6 p-4">
              <p class="text-sm font-semibold text-ink-900">推荐使用方式</p>
              <p class="mt-2 text-xs leading-5 text-ink-500">
                教程指南适合做步骤拆解，海报设计适合做招生宣传，信息图表适合做知识总结。先选类型，再调整风格，成功率会更高。
              </p>
            </div>
          </section>
        </div>

        <aside class="space-y-5 xl:sticky xl:top-6 xl:self-start">
          <section class="glass-panel rounded-[28px] p-5">
            <div class="flex items-center justify-between gap-2">
              <div>
                <h2 class="text-lg font-bold text-ink-950">积分与状态</h2>
                <p class="mt-1 text-xs text-ink-500">生成提交后会立即同步余额显示</p>
              </div>
              <span class="material-symbols-outlined !text-xl text-primary">account_balance_wallet</span>
            </div>

            <div class="mt-4 rounded-[22px] border border-border-dark/70 bg-white/90 p-4">
              <p class="text-xs uppercase tracking-[0.18em] text-ink-400">可用积分</p>
              <p class="mt-2 text-3xl font-bold text-ink-950">{{ accountPointsDisplay }}</p>
              <p class="mt-1 text-xs text-ink-500">{{ accountPointsHint }}</p>
            </div>

            <div class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <button class="secondary-ghost-button justify-between" @click="router.push('/pricing')">
                <span class="inline-flex items-center gap-1">
                  <span class="material-symbols-outlined !text-sm">payments</span>
                  去充值
                </span>
                <span class="material-symbols-outlined !text-sm">arrow_forward</span>
              </button>
              <button class="secondary-ghost-button justify-between" @click="reloadAccountInfo">
                <span class="inline-flex items-center gap-1">
                  <span class="material-symbols-outlined !text-sm">refresh</span>
                  刷新积分
                </span>
                <span class="material-symbols-outlined !text-sm">sync</span>
              </button>
            </div>
          </section>

          <section class="glass-panel rounded-[28px] p-5">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined !text-xl text-primary">rocket_launch</span>
              <h2 class="text-lg font-bold text-ink-950">下一步怎么用</h2>
            </div>
            <p class="mt-2 text-sm leading-6 text-ink-500">
              如果你已经有现成主题，直接去多图创作页输入即可；如果还在找方向，可以先去场景库挑结构。
            </p>

            <div class="mt-4 space-y-2.5">
              <button class="tutorial-example" @click="router.push('/multi')">
                <div>
                  <p class="text-sm font-semibold text-ink-900">直接开始创作</p>
                  <p class="mt-1 text-xs leading-5 text-ink-500">打开多图创作页，自己输入主题和张数</p>
                </div>
                <span class="material-symbols-outlined !text-lg text-primary">auto_awesome</span>
              </button>
              <button class="tutorial-example" @click="router.push('/scenes')">
                <div>
                  <p class="text-sm font-semibold text-ink-900">先看场景库</p>
                  <p class="mt-1 text-xs leading-5 text-ink-500">挑一个适合的拆图结构，再回到多图创作</p>
                </div>
                <span class="material-symbols-outlined !text-lg text-primary">grid_view</span>
              </button>
            </div>
          </section>
        </aside>
      </section>
    </div>
  </main>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/useAuthStore'
import { notification } from '@/utils/notification'
import { audienceChips, quickStartSteps, tutorialExamples } from '@/constants/multiGuide'

const router = useRouter()
const authStore = useAuthStore()

const accountPointsDisplay = computed(() => {
  if (!authStore.isAuthenticated) return '登录后查看'
  const total = (authStore.accountInfo?.points || 0) + (authStore.accountInfo?.gift_points || 0)
  return `${total}`
})

const accountPointsHint = computed(() => {
  if (!authStore.isAuthenticated) return '登录后可看到实时积分变化'
  const gift = authStore.accountInfo?.gift_points || 0
  return gift > 0 ? `其中临时积分 ${gift}，会一起实时刷新` : '生成提交后会自动同步余额'
})

function openComposerWithExample(example) {
  if (!example) return
  router.push({ path: '/multi', query: { example: example.id } })
}

async function reloadAccountInfo() {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  try {
    await authStore.fetchAccountInfo()
    notification.success('已刷新', '积分信息已更新')
  } catch (error) {
    notification.error('刷新失败', error?.message || '请稍后重试')
  }
}

onMounted(() => {
  if (authStore.isAuthenticated && !authStore.accountInfo) {
    void authStore.fetchAccountInfo().catch(() => {})
  }
})
</script>

<style scoped>
.multi-guide-view {
  background:
    radial-gradient(circle at top right, rgba(140, 42, 46, 0.16), transparent 24%),
    radial-gradient(circle at top left, rgba(179, 134, 0, 0.12), transparent 22%),
    linear-gradient(180deg, rgba(255, 252, 251, 0.94) 0%, rgba(247, 241, 239, 0.98) 100%);
}

.glass-panel {
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 24px 72px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(16px);
}

.hero-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.82);
  padding: 0.6rem 0.9rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: rgba(31, 35, 41, 0.72);
}

.primary-action-button {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  background: linear-gradient(135deg, rgb(20, 86, 240), rgb(10, 63, 196));
  padding: 0.8rem 1.1rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: white;
  box-shadow: 0 16px 32px rgba(20, 86, 240, 0.24);
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.primary-action-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 20px 38px rgba(20, 86, 240, 0.28);
}

.quick-step-card {
  display: grid;
  grid-template-columns: 2.35rem minmax(0, 1fr);
  gap: 0.9rem;
  align-items: start;
  border-radius: 1.35rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.86);
  padding: 1rem;
}

.quick-step__index {
  display: grid;
  height: 2.35rem;
  width: 2.35rem;
  place-items: center;
  border-radius: 999px;
  background: rgba(20, 86, 240, 0.08);
  color: rgb(20, 86, 240);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.tutorial-example {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border-radius: 1.15rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.9);
  padding: 0.95rem 1rem;
  text-align: left;
  transition: border-color 180ms ease, transform 180ms ease, box-shadow 180ms ease;
}

.tutorial-example:hover {
  border-color: rgba(20, 86, 240, 0.24);
  box-shadow: 0 12px 24px rgba(20, 86, 240, 0.08);
  transform: translateY(-1px);
}

.audience-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border-radius: 999px;
  border: 1px solid rgba(20, 86, 240, 0.14);
  background: rgba(20, 86, 240, 0.08);
  padding: 0.55rem 0.8rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: rgb(20, 86, 240);
}

.secondary-ghost-button {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: rgba(255, 255, 255, 0.9);
  padding: 0.7rem 0.9rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: rgba(31, 35, 41, 0.72);
  transition: border-color 180ms ease, color 180ms ease, background-color 180ms ease;
}

.secondary-ghost-button:hover {
  border-color: rgba(20, 86, 240, 0.22);
  color: rgb(20, 86, 240);
  background: rgba(20, 86, 240, 0.03);
}
</style>
