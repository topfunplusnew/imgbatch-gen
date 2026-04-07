<template>
  <main class="flex h-full min-h-0 flex-1 flex-col overflow-y-auto bg-background-dark">
    <!-- Hero -->
    <div class="px-4 pt-8 pb-6 text-center xs:px-6 md:px-8 md:pt-12">
      <h1 class="text-2xl font-bold text-ink-950 md:text-3xl">
        找到你的场景，<span class="text-primary">即刻出图</span>
      </h1>
      <p class="mt-2 text-sm text-ink-500">
        每个场景都预设好了图片类型、风格和提示词，选中即用
      </p>
    </div>

    <!-- Search bar -->
    <div class="mx-auto w-full max-w-[600px] px-4 xs:px-6">
      <el-input
        v-model="searchQuery"
        size="large"
        clearable
        placeholder="搜索场景或提示词..."
        class="scene-search"
      >
        <template #prefix>
          <span class="material-symbols-outlined !text-xl text-ink-500">search</span>
        </template>
      </el-input>
    </div>

    <!-- Hot scenes -->
    <div class="mx-auto mt-6 w-full max-w-[800px] px-4 xs:px-6 md:px-8">
      <div class="mb-3 flex items-center gap-2">
        <span class="text-lg">🔥</span>
        <h3 class="text-sm font-semibold text-ink-700">热门场景</h3>
      </div>
      <div class="grid grid-cols-2 gap-2 xs:grid-cols-3 md:grid-cols-3">
        <button
          v-for="scene in hotScenes"
          :key="scene.id"
          @click="selectScene(scene)"
          class="flex items-center gap-2.5 rounded-2xl border border-border-dark bg-white/80 px-3 py-2.5 text-left transition hover:border-primary/30 hover:shadow-sm"
        >
          <span class="text-xl">{{ scene.icon }}</span>
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-medium text-ink-950">{{ scene.name }}</div>
            <div class="text-xs text-ink-500">{{ scene.templateCount }} 个模版</div>
          </div>
        </button>
      </div>
    </div>

    <!-- Category filter -->
    <div class="mx-auto mt-6 w-full max-w-[800px] px-4 xs:px-6 md:px-8">
      <div class="flex flex-wrap items-center justify-center gap-2 pb-2">
        <el-button
          :type="selectedCategory === null ? 'primary' : 'default'"
          :plain="selectedCategory !== null"
          round
          size="small"
          @click="selectedCategory = null"
        >
          <span class="material-symbols-outlined !text-sm">home</span>
          <span>全部</span>
        </el-button>
        <el-button
          v-for="cat in categories"
          :key="cat.id"
          :type="selectedCategory === cat.id ? 'primary' : 'default'"
          :plain="selectedCategory !== cat.id"
          round
          size="small"
          @click="selectedCategory = cat.id"
        >
          <span>{{ cat.icon }}</span>
          <span>{{ cat.name }}</span>
        </el-button>
      </div>
    </div>

    <!-- Scene cards grid -->
    <div class="mx-auto mt-4 w-full max-w-[800px] px-4 pb-8 xs:px-6 md:px-8">
      <!-- Loading -->
      <div v-if="loading" class="grid grid-cols-2 gap-4 xs:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        <div v-for="i in 8" :key="i" class="animate-pulse rounded-2xl bg-white/60">
          <div class="aspect-square rounded-t-2xl bg-primary-soft"></div>
          <div class="p-3 space-y-2">
            <div class="h-4 w-3/4 rounded bg-primary-soft"></div>
            <div class="h-3 w-1/2 rounded bg-primary-soft"></div>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="filteredScenes.length === 0" class="py-16 text-center text-ink-500">
        <span class="material-symbols-outlined !text-5xl text-ink-300">search_off</span>
        <p class="mt-3 text-sm">未找到匹配的场景</p>
      </div>

      <!-- Scene cards -->
      <div v-else class="grid grid-cols-2 gap-4 xs:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        <div
          v-for="scene in filteredScenes"
          :key="scene.id"
          @click="selectScene(scene)"
          class="group cursor-pointer overflow-hidden rounded-2xl border border-border-dark bg-white/90 shadow-sm hover:shadow-xl hover:-translate-y-0.5 hover:border-primary/30"
        >
          <!-- Cover image / icon -->
          <div class="aspect-[4/3] overflow-hidden bg-primary-soft/20">
            <img
              v-if="scene.coverImage"
              :src="scene.coverImage"
              :alt="scene.name"
              class="w-full h-full object-cover transition-transform group-hover:scale-105"
              loading="lazy"
            />
            <div v-else class="flex h-full items-center justify-center">
              <span class="text-5xl">{{ scene.icon }}</span>
            </div>
          </div>
          <!-- Info -->
          <div class="p-3">
            <h4 class="truncate text-sm font-semibold text-ink-950">{{ scene.name }}</h4>
            <p class="mt-1 text-xs text-ink-500 line-clamp-2">
              {{ scene.templateCount }} 个模版 · {{ scene.description }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Scene detail drawer -->
    <el-drawer
      v-model="showSceneDetail"
      direction="rtl"
      size="min(480px, 90vw)"
      :title="selectedScene?.name"
      append-to-body
    >
      <template v-if="selectedScene">
        <!-- Scene header -->
        <div class="mb-4 flex items-center gap-3">
          <div class="grid h-12 w-12 place-items-center rounded-2xl bg-primary-soft text-2xl">
            {{ selectedScene.icon }}
          </div>
          <div>
            <h3 class="text-lg font-bold text-ink-950">{{ selectedScene.name }}</h3>
            <p class="text-xs text-ink-500">{{ selectedScene.templateCount }} 个模版</p>
          </div>
        </div>
        <p class="mb-6 text-sm text-ink-700">{{ selectedScene.description }}</p>

        <!-- Templates -->
        <div class="space-y-3">
          <div
            v-for="tpl in selectedScene.templates"
            :key="tpl.id"
            class="group overflow-hidden rounded-2xl border border-border-dark bg-white/80 transition hover:shadow-md"
          >
            <div v-if="tpl.exampleImage" class="aspect-[4/3] overflow-hidden bg-primary-soft/20">
              <img :src="tpl.exampleImage" class="w-full h-full object-cover transition-transform group-hover:scale-105" />
            </div>
            <div class="p-3">
              <h5 class="text-sm font-semibold text-ink-950">{{ tpl.title }}</h5>
              <div class="mt-1.5 flex flex-wrap gap-1.5">
                <el-tag v-if="tpl.type" size="small">{{ tpl.type }}</el-tag>
                <el-tag v-if="tpl.style" size="small" type="info">{{ tpl.style }}</el-tag>
              </div>
              <el-button
                type="primary"
                size="small"
                round
                class="mt-3"
                @click="useSameStyle(tpl)"
              >
                <span class="material-symbols-outlined !text-sm">arrow_upward</span>
                做同款
              </el-button>
            </div>
          </div>
        </div>
      </template>
    </el-drawer>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGeneratorStore } from '@/store/useGeneratorStore'
import { notification } from '@/utils/notification'

const router = useRouter()
const generatorStore = useGeneratorStore()

const searchQuery = ref('')
const selectedCategory = ref(null)
const loading = ref(false)
const showSceneDetail = ref(false)
const selectedScene = ref(null)

const categories = ref([])

const scenes = ref([
  // Default fallback — actual data loaded from /data/scenes.json in onMounted
  {
    id: 'math',
    name: '数学',
    icon: '📐',
    category: 'education',
    description: '数学公式、几何图形、函数图表的可视化卡片',
    coverImage: '',
    templateCount: 6,
    templates: [
      { id: 'm1', title: '数学公式卡片', type: '知识卡片', style: '扁平', prompt: '请生成一张精美的数学公式知识卡片。卡片背景为浅米色纸质纹理，顶部有深蓝色标题栏写着"核心公式"。卡片中央用清晰的LaTeX风格排版展示3-5个重要数学公式（如二次方程求根公式、三角恒等式、导数公式），每个公式下方用小字标注公式名称和适用场景。底部有一条装饰性的数学符号边框。整体风格简洁专业，适合学生复习使用。', exampleImage: '' },
      { id: 'm2', title: '几何图形海报', type: '海报设计', style: '极简', prompt: '设计一张几何之美艺术海报，展示数学中经典几何图形的优雅之处。画面以纯白背景为底，用金色细线绘制黄金螺旋、正二十面体、分形三角形等几何图形，图形之间有微妙的光影渐变。底部用衬线字体写"The Beauty of Geometry"。整体风格极简高级，像是数学博物馆的展览海报。', exampleImage: '' },
      { id: 'm3', title: '数学思维导图', type: '信息图表', style: '手绘', prompt: '创建一张高中数学知识体系思维导图。中心主题"高中数学"向外发散为函数、几何、概率统计、数列、三角函数五大分支。每个分支用不同颜色区分，下面继续细分出关键知识点。手绘涂鸦风格，线条略带手写感，重要公式用荧光笔标注效果突出。整体布局清晰，色彩活泼但不杂乱。', exampleImage: '' },
      { id: 'm4', title: '函数图像对比', type: '信息图表', style: '扁平', prompt: '生成一张常见函数图像对比卡片。在坐标系中用不同颜色的平滑曲线展示y=x², y=√x, y=1/x, y=eˣ, y=ln(x)五个基本函数的图像。每条曲线旁标注函数名和定义域。背景为淡灰色网格，坐标轴用黑色加粗。右侧配一个小型图例。风格清晰专业，像高质量教材插图。', exampleImage: '' },
      { id: 'm5', title: '数学错题整理', type: '知识卡片', style: '扁平', prompt: '设计一张数学错题整理卡片模板。顶部标题"易错题精析"，卡片分为四个区域：①题目区（白底黑字）②错误解法（用红色删除线标注）③正确解法（用绿色高亮标注关键步骤）④易错点总结（黄色便签风格）。整体配色清新，使用蓝白主色调，圆角卡片设计。', exampleImage: '' },
      { id: 'm6', title: '数学趣味故事', type: '漫画故事', style: '卡通', prompt: '绘制一幅关于数学家欧拉的趣味故事漫画。Q版卡通风格，欧拉坐在书桌前，周围飘浮着他发现的著名公式e^(iπ)+1=0。场景温馨有趣，背景是18世纪的欧洲书房，桌上堆满手稿。色彩温暖明亮，线条圆润可爱，适合激发学生对数学的兴趣。', exampleImage: '' },
    ]
  },
  {
    id: 'knowledge_card',
    name: '知识卡片',
    icon: '🃏',
    category: 'education',
    description: '各学科知识的精美卡片，适合学习记忆和分享',
    coverImage: '',
    templateCount: 6,
    templates: [
      { id: 'k1', title: '历史事件卡片', type: '知识卡片', style: '复古', prompt: '设计一张历史大事件知识卡片，主题为"丝绸之路"。卡片采用羊皮纸质感背景，顶部用毛笔字体写标题。正文区域配有丝绸之路路线简图，标注重要节点城市（长安、敦煌、撒马尔罕、罗马）。下方用时间轴展示关键历史节点。配色使用暖棕色和金色，边框有中国传统纹样装饰。整体风格古朴典雅。', exampleImage: '' },
      { id: 'k2', title: '英语单词记忆卡', type: '知识卡片', style: '卡通', prompt: '制作一张英语单词记忆卡片，单词为"Serendipity（意外的美好发现）"。卡片上半部分用大号艺术字体展示单词和音标，中间配一幅可爱的插画（一个人在雨天偶然走进一家温馨的咖啡店），下方用中英文解释词义，并给出2个例句。卡片边角有小型装饰图案。配色清新活泼，适合社交媒体分享。', exampleImage: '' },
      { id: 'k3', title: '古诗词鉴赏卡', type: '知识卡片', style: '水墨', prompt: '生成一张古诗词鉴赏卡片，内容为李白《静夜思》。背景为淡雅水墨山水画，上方用楷书字体书写诗文全文，中间配以月光下窗前思乡的意境插画（水墨风格）。下方用现代字体写注释和赏析要点。整体留白充足，意境悠远，色调以黑白灰为主，点缀一抹月黄色。', exampleImage: '' },
      { id: 'k4', title: '化学元素卡片', type: '知识卡片', style: '扁平', prompt: '设计一张化学元素周期表知识卡片，聚焦碳元素(C)。卡片顶部大号显示元素符号C和原子序数6，中间区域图解碳的原子结构、常见化合物（CO₂、CH₄、金刚石、石墨）和应用场景。底部用图标展示碳在日常生活中的存在形式。配色使用深灰和荧光绿，科技感十足。', exampleImage: '' },
      { id: 'k5', title: '地理气候图解', type: '信息图表', style: '扁平', prompt: '生成一张世界气候类型分布图解卡片。用简化的世界地图标注主要气候带（热带雨林、温带季风、地中海、寒带等），每种气候用不同颜色区分。右侧配小型温度-降水柱状图对比。底部列出各气候类型的特征关键词。配色鲜明但协调，地图线条简洁，信息层次分明。', exampleImage: '' },
      { id: 'k6', title: '物理实验步骤', type: '流程指南', style: '扁平', prompt: '制作一张物理实验步骤指南卡片，主题为"测量重力加速度g"。用编号步骤图展示实验流程：①准备器材（单摆装置图）②测量摆长③计时多次摆动④记录数据⑤计算g值。每步配简洁的示意图，关键注意事项用红色标注。底部给出计算公式T=2π√(L/g)。整体风格清晰专业。', exampleImage: '' },
    ]
  },
  {
    id: 'parenting',
    name: '育儿故事',
    icon: '🏰',
    category: 'education',
    description: '儿童绘本插画、童话故事、亲子教育内容',
    coverImage: '',
    templateCount: 5,
    templates: [
      { id: 'p1', title: '童话故事插画', type: '漫画故事', style: '水彩', prompt: '绘制一幅温馨的儿童绘本风格插画。场景：一只穿着红色围巾的小兔子站在秋天的森林里，抬头望着树上最后一片金黄色的叶子飘落。周围有蘑菇、橡果和小野花。色调温暖柔和，使用水彩晕染效果，线条柔软圆润。画面充满童趣和温馨感，适合3-6岁儿童绘本。', exampleImage: '' },
      { id: 'p2', title: '睡前故事卡片', type: '知识卡片', style: '卡通', prompt: '设计一张睡前故事卡片，标题"星星的约定"。画面上方是一片深蓝色星空，一颗特别亮的星星有一个微笑的脸。下方是一个小女孩站在窗前，双手合十许愿。文字区域写着故事开头："每天晚上，小星星都会来到莉莉的窗前……"。整体色调为深蓝紫配金色星光，氛围宁静安详。', exampleImage: '' },
      { id: 'p3', title: '好习惯养成表', type: '信息图表', style: '卡通', prompt: '制作一张儿童好习惯养成打卡表。标题用彩虹色大字"我的好习惯"。左侧列出7个好习惯（早起、刷牙、整理玩具、阅读、运动、喝水、早睡），每个习惯配一个可爱的小图标。右侧是周一到周日的打卡格子，格子里可以贴星星。底部有一排小动物啦啦队加油。配色活泼明亮，风格可爱童趣。', exampleImage: '' },
      { id: 'p4', title: '认识动物卡片', type: '知识卡片', style: '卡通', prompt: '生成一张幼儿认知卡片，主题"认识森林动物"。卡片中央是一片卡通森林场景，里面藏着小鹿、松鼠、猫头鹰、小狐狸、刺猬五种动物。每只动物旁边标注中文名和拼音。画风Q萌可爱，色彩饱满鲜艳，动物表情生动有趣。适合2-4岁幼儿启蒙认知。', exampleImage: '' },
      { id: 'p5', title: '亲子手工教程', type: '流程指南', style: '手绘', prompt: '设计一张亲子手工教程图，教小朋友用纸杯做可爱的小企鹅。分4个步骤展示：①准备材料（纸杯、彩纸、剪刀、胶水）②剪裁黑白彩纸③粘贴组装④完成成品。每步配清晰的手绘示意图和简短文字说明。整体风格温馨可爱，使用柔和的粉蓝色调。', exampleImage: '' },
    ]
  },
  {
    id: 'enrollment',
    name: '招生海报',
    icon: '📢',
    category: 'education',
    description: '培训机构、学校招生宣传海报设计',
    coverImage: '',
    templateCount: 4,
    templates: [
      { id: 'e1', title: '暑期班招生', type: '海报设计', style: '扁平', prompt: '设计一张暑期培训班招生海报。主标题"暑期特训营·火热招生中"用大号醒目字体。画面以明亮的橙黄色为主色调，配蓝色点缀。中间展示课程亮点（数学提升、英语强化、编程启蒙）用图标卡片排列。底部放报名电话、二维码和校区地址。加入夏日元素（太阳、冰淇淋、西瓜）装饰。整体活泼有活力，吸引家长关注。', exampleImage: '' },
      { id: 'e2', title: '艺术班招生', type: '海报设计', style: '水彩', prompt: '设计一张少儿美术班招生海报。画面以水彩泼墨效果为背景，色彩斑斓但和谐。中央是一个小朋友拿着画笔在画架前创作的剪影，周围飘散着彩色的颜料飞溅效果。标题"让色彩点亮童年"用手写艺术字体。底部信息区放课程安排和联系方式。整体充满艺术气息和创造力。', exampleImage: '' },
      { id: 'e3', title: '考研辅导班', type: '海报设计', style: '扁平', prompt: '制作一张考研辅导班招生海报。顶部大标题"2025考研·一战成硕"，使用深蓝色学术风配色。中间用信息图展示：通过率数据、师资力量、课程体系（政治/英语/数学/专业课）。配有学生认真学习的插画。底部突出早鸟优惠价格和报名截止日期。风格专业可信，传递实力感。', exampleImage: '' },
      { id: 'e4', title: '幼儿园招生', type: '海报设计', style: '卡通', prompt: '设计一张幼儿园春季招生海报。画面充满春天元素——樱花树、蝴蝶、彩虹。几个可爱的卡通小朋友手拉手站在草地上。标题"春暖花开·成长起航"用圆润可爱的字体。中间区域展示园所特色：双语教学、艺术培养、户外运动、营养膳食，每项配一个简约图标。配色温暖柔和，粉色绿色为主。', exampleImage: '' },
    ]
  },
  // === 创意文案 ===
  {
    id: 'social_media',
    name: '社交媒体',
    icon: '📱',
    category: 'creative',
    description: '小红书、抖音、微信等社交平台的封面和配图',
    coverImage: '',
    templateCount: 6,
    templates: [
      { id: 's1', title: '小红书封面', type: '海报设计', style: '扁平', prompt: '设计一张小红书风格的封面图，主题"周末居家咖啡指南"。画面采用奶油色暖色调背景，中央是一杯拉花咖啡的俯拍视角，周围散落着咖啡豆、肉桂棒和一本打开的书。标题用网红手写字体，加上"收藏这篇就够了"的副标题。整体风格温馨文艺，色调统一，构图留出文字空间。9:16竖版比例。', exampleImage: '' },
      { id: 's2', title: '产品种草卡片', type: '知识卡片', style: '极简', prompt: '制作一张产品种草分享卡片，主题"我的护肤好物分享"。白色简洁背景，顶部标题用金色优雅字体。中间分3-4格展示产品（洁面、精华、面霜、防晒），每格一个产品轮廓图标配名称和一句话推荐理由。底部用星级评分和适合肤质标签。配色白金搭配，高级极简风。', exampleImage: '' },
      { id: 's3', title: '打卡Vlog封面', type: '海报设计', style: '扁平', prompt: '设计一张旅行打卡Vlog封面图。画面风格为杂志感排版，大标题"72小时·成都漫游记"用撞色字体。背景是成都地标元素的插画拼贴（熊猫、太古里、火锅、春熙路）。加入胶片相机边框效果和手写日期戳。配色为莫兰迪色系，整体时尚又有记录感。', exampleImage: '' },
      { id: 's4', title: '语录金句图', type: '知识卡片', style: '极简', prompt: '生成一张适合朋友圈分享的励志语录图。纯色渐变背景（从深蓝渐变到紫色），中央用大号白色衬线字体排版一句话："所有的努力都不会被辜负，时间会给你答案。"下方用小号字体标注来源。画面四角有几何线条装饰，整体高级简约，适合转发分享。1:1方形比例。', exampleImage: '' },
      { id: 's5', title: '美食探店图', type: '海报设计', style: '扁平', prompt: '制作一张美食探店分享封面，主题"藏在巷子里的宝藏面馆"。画面用暖黄色灯光氛围，展示一碗热气腾腾的面条特写（俯拍角度），旁边有筷子和小菜。用杂志风文字排版：大标题+店铺评分+地址标签。加入"本地人推荐"的角标。整体色调暖黄，有食欲感和烟火气。', exampleImage: '' },
      { id: 's6', title: '日签打卡图', type: '知识卡片', style: '极简', prompt: '设计一张每日签到打卡图。顶部显示日期"4月1日 星期二"和天气图标。中央配一幅应季的小清新插画（春日樱花树下的长椅）。下方写一句温暖的文案"春天的每一天都值得期待"。底部有今日待办清单格式（3个复选框）。配色樱花粉配抹茶绿，清新治愈。', exampleImage: '' },
    ]
  },
  {
    id: 'logo_brand',
    name: 'Logo品牌',
    icon: '🎨',
    category: 'creative',
    description: 'Logo设计、品牌视觉识别、名片设计',
    coverImage: '',
    templateCount: 4,
    templates: [
      { id: 'lb1', title: '简约Logo设计', type: '海报设计', style: '极简', prompt: '为一家名为"云栖咖啡"的精品咖啡店设计Logo。要求：极简线条风格，用云朵和咖啡杯元素巧妙结合成一个图形标志，下方配中英文店名"云栖咖啡 YUNQI COFFEE"。配色方案：深棕色+米白色。展示在白色背景上，同时展示在深色背景上的反白版本。Logo需要辨识度高，缩小后依然清晰。', exampleImage: '' },
      { id: 'lb2', title: '品牌色卡展示', type: '信息图表', style: '极简', prompt: '设计一张品牌色彩体系展示卡。展示一套完整的品牌配色方案：主色（深森绿#2D5F3F）、辅色（暖金#C9A96E）、中性色（米灰#F5F1EB）、强调色（珊瑚橘#E8734A）。每个颜色展示大色块+色值(HEX/RGB)+使用场景建议。底部展示颜色搭配组合效果示例。白色背景，排版整洁专业。', exampleImage: '' },
      { id: 'lb3', title: '名片设计', type: '海报设计', style: '极简', prompt: '设计一张高端商务名片，正反两面。正面：左上角放Logo占位区，右侧竖排姓名（中文大号+英文小号）、职位、公司名。底部一行排列电话、邮箱、地址图标和文字。背面：大面积使用品牌深蓝色，中央放Logo水印。配色深蓝+白+金，使用细衬线字体。尺寸90×54mm标准比例。', exampleImage: '' },
      { id: 'lb4', title: '品牌VI延展', type: '海报设计', style: '扁平', prompt: '制作一张品牌VI视觉延展效果图，展示一个咖啡品牌的物料应用。画面用等距视角（isometric）排列展示：纸杯、手提袋、菜单、围裙、外卖盒上的Logo应用效果。背景浅灰色，物品整齐排列形成品牌墙效果。整体专业大气，展示品牌统一性。', exampleImage: '' },
    ]
  },
  {
    id: 'poster_design',
    name: '活动海报',
    icon: '🎪',
    category: 'creative',
    description: '各类活动、节日、促销海报设计',
    coverImage: '',
    templateCount: 5,
    templates: [
      { id: 'pd1', title: '音乐节海报', type: '海报设计', style: '复古', prompt: '设计一张户外音乐节海报。标题"2025星空音乐节"用复古迷幻字体，色彩渐变效果（紫→橙→粉）。背景是夜空下的露天舞台剪影，观众举手欢呼。中间列出演出嘉宾名单（3-4位），底部放时间地点和购票二维码。风格参考经典摇滚海报，加入迷幻花纹和星星元素。', exampleImage: '' },
      { id: 'pd2', title: '双十一促销', type: '海报设计', style: '扁平', prompt: '制作一张双十一购物节促销海报。大标题"11.11狂欢盛典"用立体金色字体，背景为深红色配金色飘带。中间展示核心优惠信息："全场5折起"、"满300减50"、"前100名赠好礼"。底部有倒计时钟和"立即抢购"按钮设计。加入礼盒、红包、购物袋等元素。风格热烈喜庆，营造紧迫感。', exampleImage: '' },
      { id: 'pd3', title: '公益环保海报', type: '海报设计', style: '水彩', prompt: '设计一张环保主题公益海报，标题"守护蓝色星球"。画面用水彩风格绘制一双手捧着地球，地球一半是绿色森林和蓝色海洋，另一半正在变成灰色沙漠和枯树。手掌上有一棵发芽的小树苗，象征希望。色调从灰暗过渡到明亮。底部文案"每一个小行动，都在改变世界"。', exampleImage: '' },
      { id: 'pd4', title: '中秋节海报', type: '海报设计', style: '水墨', prompt: '设计一张中秋节祝福海报。画面以深蓝色夜空为背景，一轮明亮的满月居中。月亮下方是传统水墨画风格的山水和亭台楼阁剪影。前景有几支桂花枝从画面角落伸入。标题"花好月圆·中秋快乐"用书法字体。整体意境古典优美，配色深蓝、金黄、白色，充满东方美学韵味。', exampleImage: '' },
      { id: 'pd5', title: '新品发布会', type: '海报设计', style: '极简', prompt: '设计一张科技产品新品发布会邀请海报。纯黑背景，中央一束聚光灯照亮产品轮廓（智能手表），光线产生丁达尔效应。上方小字"重新定义·时间" 下方大字"NEW ERA"。底部白色小字显示发布会日期、时间和线上直播入口。整体极度简约，苹果发布会风格，科技感和仪式感并存。', exampleImage: '' },
    ]
  },
  // === 内容创作 ===
  {
    id: 'reading',
    name: '读书笔记',
    icon: '📖',
    category: 'content',
    description: '书籍摘录、读后感、阅读打卡分享',
    coverImage: '',
    templateCount: 4,
    templates: [
      { id: 'r1', title: '读书笔记卡', type: '知识卡片', style: '极简', prompt: '设计一张精美的读书笔记卡片，书目《百年孤独》。顶部展示书名、作者（加西亚·马尔克斯）和一个5星评分。中间区域是一段经典语录摘抄："生命中曾经有过的所有灿烂，原来终究，都需要用寂寞来偿还。"用优雅的衬线字体排版。底部有阅读进度条和日期标记。背景为米白色亚麻纹理，配色温暖低调。', exampleImage: '' },
      { id: 'r2', title: '年度书单推荐', type: '信息图表', style: '扁平', prompt: '制作一张年度书单推荐信息图，标题"2025必读好书TOP10"。用书架造型排列10本推荐书籍，每本书展示书脊和简短推荐理由（一句话）。按类别分色：文学（蓝色）、商业（橙色）、科普（绿色）、心理（紫色）。底部有阅读统计数据。白色背景，排版像杂志内页，高级且有设计感。', exampleImage: '' },
      { id: 'r3', title: '读书思维导图', type: '信息图表', style: '手绘', prompt: '创建一张《思考，快与慢》的读书思维导图。中心是书名和作者丹尼尔·卡尼曼。分出两大主干：系统1（快速直觉思维）和系统2（慢速理性思维）。每个系统下展开3-4个关键概念（锚定效应、框架效应、损失厌恶等）。手写风格线条，用不同颜色区分章节，重要结论用星号标注。', exampleImage: '' },
      { id: 'r4', title: '阅读打卡日历', type: '信息图表', style: '扁平', prompt: '设计一张月度阅读打卡日历。顶部标题"四月阅读计划"配一个可爱的书本图标。日历网格31天，已读日期用绿色填充并标注阅读页数，当日用橘色高亮。右侧栏显示本月目标（4本书）、已完成进度条、累计阅读时长。底部放正在读的书籍封面缩略图。配色清新柔和。', exampleImage: '' },
    ]
  },
  {
    id: 'infographic',
    name: '数据图表',
    icon: '📊',
    category: 'content',
    description: '数据可视化、统计图表、信息图解',
    coverImage: '',
    templateCount: 4,
    templates: [
      { id: 'ig1', title: '年度数据报告', type: '信息图表', style: '扁平', prompt: '设计一张年度数据报告信息图。标题"2024年度运营数据总览"。包含以下数据可视化元素：①用户增长趋势折线图（月度数据）②营收占比环形图（4个产品线）③关键指标KPI卡片（DAU/MAU/留存率/ARPU）④地区分布热力地图。深蓝色主色调，数据用亮色（青绿、橙、紫）区分。专业商务风格，像咨询公司的报告图。', exampleImage: '' },
      { id: 'ig2', title: '对比分析图', type: '信息图表', style: '扁平', prompt: '制作一张产品对比分析信息图，对比"方案A vs 方案B"。用左右分栏布局，中间一条分割线。对比维度包括：价格（柱状图）、性能（雷达图）、用户评分（星级）、上市时间、核心优势。用蓝色和橙色分别代表两个方案。底部给出推荐结论。白色背景，扁平化图标，数据清晰易读。', exampleImage: '' },
      { id: 'ig3', title: '流程图解', type: '流程指南', style: '扁平', prompt: '设计一张产品开发流程图。从左到右展示6个阶段：需求分析→原型设计→UI设计→开发编码→测试验收→上线发布。每个阶段用不同颜色的圆角矩形表示，之间用箭头连接，下方标注每阶段的预计时间和负责角色。关键里程碑用钻石形标记。配色专业，使用品牌蓝色系。', exampleImage: '' },
      { id: 'ig4', title: '时间轴信息图', type: '信息图表', style: '扁平', prompt: '创建一张公司发展历程时间轴信息图。垂直时间轴展示5-6个关键里程碑（2018创立→2019首轮融资→2020产品上线→2022用户破百万→2024海外扩张）。每个节点配一个标志性图标和简短描述。左右交替排列。背景深色，时间轴用金色，节点用品牌色。整体像精美的公司介绍PPT页面。', exampleImage: '' },
    ]
  },
  {
    id: 'wechat_article',
    name: '公众号配图',
    icon: '💬',
    category: 'content',
    description: '微信公众号头图、文中配图、封面图',
    coverImage: '',
    templateCount: 4,
    templates: [
      { id: 'wa1', title: '公众号头图', type: '海报设计', style: '扁平', prompt: '设计一张微信公众号文章头图，主题"5个提升工作效率的方法"。画面采用2.35:1宽幅比例，左侧是一个人在整洁桌面上高效工作的扁平插画，右侧用大号字体排版标题。配色使用专业的藏蓝色+亮橙色。底部有作者头像小圆框和公众号名称。风格干净专业，有品质感。', exampleImage: '' },
      { id: 'wa2', title: '文章分割配图', type: '海报设计', style: '极简', prompt: '生成一张公众号文章中间的分割配图，主题"思考与总结"。画面极简：浅灰色背景上，中央一盏台灯照亮一本翻开的笔记本，光影效果柔和。没有文字，纯意境图。色调低饱和度暖灰色系，有高级感。比例900×500像素，适合公众号文中插入。', exampleImage: '' },
      { id: 'wa3', title: '年终总结封面', type: '海报设计', style: '扁平', prompt: '制作一张年终总结公众号封面，标题"2024·年度盘点"。画面用拼贴风格展示一年的关键词云和小图标（成长曲线↗、奖杯🏆、里程碑🎯、团队👥）。背景从深蓝渐变到星空紫，象征年终回望。数字"2024"用超大号半透明字体做背景元素。金色光点散布，有跨年仪式感。', exampleImage: '' },
      { id: 'wa4', title: '招聘信息图', type: '信息图表', style: '扁平', prompt: '设计一张公众号招聘信息配图。标题"我们在找你！"用活力感字体。中间展示3个招聘岗位卡片（前端工程师/产品经理/UI设计师），每个卡片含岗位图标、关键要求和薪资范围。底部放公司Logo和投简历邮箱。配色年轻活泼，使用渐变紫+亮绿+白色。整体有互联网公司氛围。', exampleImage: '' },
    ]
  },
  // === 生活百科 ===
  {
    id: 'food',
    name: '美食食谱',
    icon: '🍳',
    category: 'life',
    description: '食谱步骤图、美食卡片、菜单设计',
    coverImage: '',
    templateCount: 4,
    templates: [
      { id: 'f1', title: '食谱步骤图', type: '流程指南', style: '手绘', prompt: '制作一张红烧肉食谱步骤图。标题"经典红烧肉·家的味道"用手写字体。分6个步骤展示：①五花肉切块焯水②炒糖色③煸炒上色④加调料和水⑤小火慢炖40分钟⑥大火收汁。每步配手绘风格的烹饪示意图和简洁文字。底部标注用量清单（五花肉500g、冰糖30g、生抽2勺…）。色调暖黄，氛围温馨。', exampleImage: '' },
      { id: 'f2', title: '下午茶菜单', type: '海报设计', style: '极简', prompt: '设计一张精致的下午茶菜单卡。米白色卡纸质感背景，顶部用烫金效果写"Afternoon Tea"和中文"悠享时光"。菜单分三层展示（参考英式下午茶塔）：①甜点层（马卡龙、提拉米苏、舒芙蕾）②三明治层（烟熏三文鱼、鸡蛋沙拉）③司康层（原味司康配果酱和奶油）。配手绘茶具边框装饰。', exampleImage: '' },
      { id: 'f3', title: '营养搭配图', type: '信息图表', style: '扁平', prompt: '生成一张每日营养均衡搭配指南图。用餐盘模型展示一餐的理想搭配比例：蔬菜40%（绿色区域）、优质蛋白25%（橙色区域）、碳水化合物25%（黄色区域）、水果10%（紫色区域）。每个区域列出推荐食物。旁边配一杯水和营养素小贴士。配色清新健康，扁平风格。', exampleImage: '' },
      { id: 'f4', title: '咖啡种类图鉴', type: '信息图表', style: '扁平', prompt: '制作一张咖啡种类图鉴卡片。用截面图展示6种经典咖啡的成分比例：浓缩咖啡、美式、拿铁、卡布奇诺、摩卡、玛奇朵。每种咖啡用玻璃杯截面图分层显示（咖啡层/牛奶层/奶泡层/巧克力层），层次用不同颜色区分。旁边标注名称和特点。背景深棕色咖啡色调，整体像精品咖啡馆的装饰画。', exampleImage: '' },
    ]
  },
  {
    id: 'travel',
    name: '旅行攻略',
    icon: '✈️',
    category: 'life',
    description: '旅行路线图、景点推荐、行程规划',
    coverImage: '',
    templateCount: 4,
    templates: [
      { id: 't1', title: '旅行路线图', type: '信息图表', style: '水彩', prompt: '绘制一张云南旅行路线图。水彩画风格的简化地图上标注路线：昆明→大理（高铁2h）→丽江（大巴3h）→泸沽湖（车程4h）→香格里拉（车程5h）。每个城市旁配一个代表性景点/美食的小水彩插画（翠湖海鸥、洱海、玉龙雪山、走婚桥、松赞林寺）。路线用虚线连接，标注交通方式和时间。整体清新文艺。', exampleImage: '' },
      { id: 't2', title: '行李清单', type: '知识卡片', style: '扁平', prompt: '设计一张旅行行李打包清单卡。标题"出发前Check List"。分类整理：证件类（身份证、护照）、电子产品（充电宝、转换插头）、衣物（根据天气建议）、洗护用品、药品急救包、其他（伞、零食）。每类配简洁图标，用复选框格式可打勾。底部有温馨提示"提前一天整理，从容出发"。配色活力橙+白色。', exampleImage: '' },
      { id: 't3', title: '酒店对比卡', type: '信息图表', style: '扁平', prompt: '制作一张旅行酒店对比推荐卡，对比3家酒店。用卡片式布局横向排列，每张卡片包含：酒店封面照（示意框）、名称、星级、价格/晚、地理位置、核心优势（海景房/含早/泳池）、用户评分。用颜色标注性价比最高的选项。底部给出推荐结论。风格清晰实用，方便对比决策。', exampleImage: '' },
      { id: 't4', title: '旅行手账', type: '知识卡片', style: '手绘', prompt: '设计一张旅行手账页面模板。手绘风格，包含：日期和天气图标区、今日路线简图（手绘小地图）、照片粘贴区（3个虚线框）、文字记录区（横线格）、今日花费小账本、心情评分（5个表情）和一句话感悟区。装饰元素有胶带贴纸效果、邮戳印章、小飞机图标。整体像真实的手账本页面。', exampleImage: '' },
    ]
  },
  {
    id: 'fitness',
    name: '健身运动',
    icon: '💪',
    category: 'life',
    description: '健身计划、动作教学、运动数据可视化',
    coverImage: '',
    templateCount: 4,
    templates: [
      { id: 'fit1', title: '健身动作图解', type: '流程指南', style: '扁平', prompt: '制作一张深蹲动作标准教学图。分4个步骤展示正确姿势：①起始站姿（双脚与肩同宽）②下蹲过程（膝盖不超过脚尖）③最低点保持（大腿与地面平行）④起身还原。每步用简洁的人体轮廓线条画展示，关键角度用红色标注线标出。旁边列出常见错误动作（用X号标注）。背景深灰色，运动感配色。', exampleImage: '' },
      { id: 'fit2', title: '周训练计划表', type: '信息图表', style: '扁平', prompt: '设计一张一周健身训练计划表。标题"每周训练计划"。用日历格式展示周一到周日：周一胸+三头/周二背+二头/周三休息/周四肩+核心/周五腿部/周六有氧HIIT/周日休息。每天列出3-4个训练动作和组数。用不同颜色区分肌肉群。底部有训练小贴士。深色背景配荧光色系，运动App风格。', exampleImage: '' },
      { id: 'fit3', title: '运动数据卡', type: '信息图表', style: '扁平', prompt: '生成一张月度运动数据统计卡片，模拟运动手环数据展示。包含：本月跑步总里程（环形进度条）、平均心率变化折线图、每周运动天数柱状图、消耗热量总计、最佳配速记录。数据用大号数字突出显示。深色背景（近黑），数据用荧光绿和电光蓝高亮，科技运动感十足。', exampleImage: '' },
      { id: 'fit4', title: '拉伸指南', type: '流程指南', style: '手绘', prompt: '制作一张运动后拉伸动作指南。展示8个基础拉伸动作：颈部环绕、肩部拉伸、三角式、前屈体、股四头肌拉伸、腿后侧拉伸、臀部拉伸、婴儿式。每个动作用简笔画人体展示，标注保持时间（15-30秒）和拉伸部位。排列为2×4网格。柔和的薄荷绿配色，轻松舒缓氛围。', exampleImage: '' },
    ]
  },
  {
    id: 'home_decor',
    name: '家居生活',
    icon: '🏠',
    category: 'life',
    description: '家居布置、收纳整理、生活小妙招',
    coverImage: '',
    templateCount: 3,
    templates: [
      { id: 'hd1', title: '房间布置方案', type: '信息图表', style: '扁平', prompt: '设计一张小户型客厅布置方案图。俯视角度的平面布局图，展示15平米客厅的家具摆放：L型沙发靠墙、茶几居中、电视柜对面、落地灯在角落、小书架沿墙。用不同颜色区分功能区（休息区/阅读角/储物区）。旁边标注关键尺寸和选购建议。配色莫兰迪色系，简约北欧风格。', exampleImage: '' },
      { id: 'hd2', title: '收纳技巧图', type: '流程指南', style: '扁平', prompt: '制作一张衣柜收纳整理技巧信息图。展示衣柜分区方案：上层放换季被褥、中层挂区分短/长衣物、下层叠放区用收纳盒分类、门板内侧挂配饰。用Before/After对比展示整理前后效果。配实用小贴士："竖着叠放节省50%空间"。配色清爽白+原木色，给人整洁治愈感。', exampleImage: '' },
      { id: 'hd3', title: '绿植养护卡', type: '知识卡片', style: '手绘', prompt: '生成一张室内绿植养护指南卡片，介绍5种好养的绿植：龟背竹、虎皮兰、绿萝、多肉、琴叶榕。每种植物配手绘插画，标注：浇水频率（水滴图标）、光照需求（太阳图标）、难度等级（星星评分）、净化能力。卡片底部有季节养护提醒。手绘水彩风格，清新自然的绿色调。', exampleImage: '' },
    ]
  },
])

const hotScenes = computed(() => {
  return [...scenes.value]
    .sort((a, b) => (b.templates?.length || 0) - (a.templates?.length || 0))
    .slice(0, 6)
})

const filteredScenes = computed(() => {
  let result = scenes.value

  if (selectedCategory.value) {
    result = result.filter(s => s.category === selectedCategory.value)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(s =>
      s.name.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q) ||
      s.templates?.some(t => t.title.toLowerCase().includes(q) || t.prompt.toLowerCase().includes(q))
    )
  }

  return result
})

const selectScene = (scene) => {
  selectedScene.value = scene
  showSceneDetail.value = true
}

const useSameStyle = (template) => {
  // Start a new conversation to avoid previous context affecting generation
  generatorStore.startNewConversation()
  generatorStore.prompt = template.prompt || ''
  if (template.style) {
    generatorStore.style = template.style
  }
  showSceneDetail.value = false
  router.push('/')
  notification.success('已加载模版', '提示词已填入输入框，可直接发送或修改后发送')
}

onMounted(async () => {
  // Load scenes from API (database), fallback to static JSON
  loading.value = true
  try {
    const res = await fetch('/api/v1/admin/system-config/scenes')
    const data = await res.json()
    if (data.categories?.length) categories.value = data.categories
    if (data.scenes?.length) {
      scenes.value = data.scenes.map(s => ({
        ...s,
        templateCount: s.templates?.length || 0,
      }))
    }
  } catch (e) {
    console.warn('Failed to load scenes from API, trying static JSON:', e)
    try {
      const res = await fetch('/data/scenes.json')
      const data = await res.json()
      if (data.categories?.length) categories.value = data.categories
      if (data.scenes?.length) {
        scenes.value = data.scenes.map(s => ({
          ...s,
          templateCount: s.templates?.length || 0,
        }))
      }
    } catch {}
  }

  // Merge admin-managed scenes
  try {
    const adminScenes = localStorage.getItem('admin_scenes')
    if (adminScenes) {
      const parsed = JSON.parse(adminScenes)
      if (parsed.length > 0) {
        const adminIds = new Set(parsed.map(s => s.id))
        const merged = [
          ...parsed,
          ...scenes.value.filter(s => !adminIds.has(s.id))
        ]
        scenes.value = merged
      }
    }
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.scene-search :deep(.el-input__wrapper) {
  border-radius: 24px;
  padding: 4px 16px;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
