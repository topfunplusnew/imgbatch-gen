import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './assets/main.css'
import { useApiConfigStore } from './store/useApiConfigStore'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

// 初始化API配置
const apiConfig = useApiConfigStore()
apiConfig.initializeConfig().catch(error => {
  console.error('Failed to initialize API config:', error)
})

app.mount('#app')
