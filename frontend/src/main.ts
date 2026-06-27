import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)

  // 任务 9：全局错误处理
  app.config.errorHandler = (err, instance, info) => {
    console.error('[Global Error]', err, info)
    uni.showToast({ title: '发生错误，请重试', icon: 'none' })
  }

  return { app }
}
