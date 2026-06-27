<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { useUserStore } from './store/user'
import { useStudentStore } from './store/student'
import { getStudents } from './utils/service'

// 不需要登录就能访问的页面
const publicPages = ['/pages/login/index']

onLaunch(async () => {
  const userStore = useUserStore()

  // 任务 10：路由守卫 — 检查登录状态
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const currentPath = currentPage ? '/' + (currentPage as any).route : ''

  if (!userStore.isLoggedIn && !publicPages.includes(currentPath)) {
    uni.redirectTo({ url: '/pages/login/index' })
    return
  }

  if (userStore.isLoggedIn) {
    // 已登录，加载学生数据
    try {
      const res = await getStudents()
      if (res.code === 0) {
        useStudentStore().setStudents(res.data)
      }
    } catch (e) {
      console.error('加载学生数据失败', e)
    }
  }
})
</script>

<style>
/* 全局样式 */
page {
  background-color: #F8FAFC;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  color: #1E293B;
  font-size: 15px;
  line-height: 1.5;
}

/* 安全区域 */
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
