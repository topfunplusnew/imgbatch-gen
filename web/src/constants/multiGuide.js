export const quickStartSteps = [
  {
    index: '01',
    title: '先选类型和风格',
    description: '教程指南、信息图表、海报设计这三类最适合做多图排版。',
  },
  {
    index: '02',
    title: '一句话写清主题',
    description: '把核心内容、受众和期望张数写进去，系统会更容易拆分版面。',
  },
  {
    index: '03',
    title: '生成后在下方回看',
    description: '点击图片即可放大，历史会横向保留，方便挑图和继续复用提示词。',
  },
]

export const tutorialExamples = [
  {
    id: 'chemistry-bridge',
    title: '老师做知识衔接图',
    description: '自动填入“初高中化学衔接指南”的多图示例',
    prompt: '把“初高中化学衔接指南”整理成 4 张知识图，要求标题清晰、层级明确、适合学生收藏复习。',
    type: 'tutorial',
    style: 'hand_drawn',
    count: 4,
  },
  {
    id: 'enrollment-promo',
    title: '机构做招生宣传图',
    description: '快速生成一组课程卖点与报名引导图',
    prompt: '围绕“暑期衔接班招生”生成 4 张招生图，包含课程亮点、适合人群、学习成果和报名引导，视觉醒目。',
    type: 'poster',
    style: 'flat',
    count: 4,
  },
  {
    id: 'blogger-tutorial',
    title: '博主做教程拆解图',
    description: '适合把操作步骤拆成多张流程图',
    prompt: '将“如何用三步记忆英语单词”做成 4 张教程图，每张图只讲一个重点，适合社交平台发布。',
    type: 'tutorial',
    style: 'cartoon',
    count: 4,
  },
]

export const audienceChips = ['招生老师', '课程顾问', '知识博主', '自媒体创作者', '新手运营', '培训机构']

export function getTutorialExampleById(id) {
  return tutorialExamples.find((example) => example.id === id)
}
