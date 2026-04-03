import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'ant-design-vue/dist/reset.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import { useApiConfigStore } from './store/useApiConfigStore'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// 初始化API配置
const apiConfig = useApiConfigStore()
apiConfig.initializeConfig().catch(error => {
  console.error('Failed to initialize API config:', error)
})

app.mount('#app')
