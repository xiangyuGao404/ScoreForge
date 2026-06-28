<template>
  <view class="result-page">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <view class="loading-spinner"></view>
      <text class="loading-text">AI 正在评估掌握程度...</text>
      <text class="loading-sub">预计 10-20 秒，请耐心等待</text>
    </view>

    <view v-else>
      <!-- 掌握度仪表盘 -->
      <view class="gauge-section">
        <view class="gauge-ring">
          <view class="gauge-bg"></view>
          <view class="gauge-fill" :style="{ background: `conic-gradient(${gaugeColor} ${assessment.mastery_score * 3.6}deg, #E2E8F0 0deg)` }"></view>
          <view class="gauge-inner">
            <text class="gauge-num">{{ assessment.mastery_score }}</text>
            <text class="gauge-label">掌握度</text>
          </view>
        </view>

        <view class="gauge-info">
          <view class="trend-badge" :class="assessment.trend">
            <text>{{ trendLabel[assessment.trend] }}</text>
          </view>
          <text class="error-pattern">{{ assessment.error_pattern }}</text>
        </view>
      </view>

      <!-- AI 建议 -->
      <view class="advice-card">
        <text class="advice-title">🤖 AI 建议</text>
        <text class="advice-text">{{ assessment.suggestion_detail }}</text>

        <view v-if="assessment.recommendation === 'continue'" class="advice-action">
          <text class="action-icon">📅</text>
          <text class="action-text">建议还需练习 <text class="highlight">{{ assessment.suggested_days }}</text> 天</text>
        </view>
        <view v-else-if="assessment.recommendation === 'mastered'" class="advice-action success">
          <text class="action-icon">🎉</text>
          <text class="action-text">已达到掌握标准！</text>
        </view>
      </view>

      <!-- 本次练习数据 -->
      <view class="data-card">
        <text class="data-title">📊 本次练习</text>
        <view class="data-row">
          <view class="data-item">
            <text class="data-num">{{ history.length > 0 ? (history[0].correct_rate * 100).toFixed(0) : 0 }}%</text>
            <text class="data-label">正确率</text>
          </view>
          <view class="data-item">
            <text class="data-num">{{ history.length }}</text>
            <text class="data-label">练习轮次</text>
          </view>
        </view>
      </view>

      <!-- 底部操作 -->
      <view class="bottom-actions safe-area-bottom">
        <button class="secondary-btn" @tap="goHome">返回首页</button>
        <button class="primary-btn" @tap="continuePractice">
          {{ assessment.recommendation === 'mastered' ? '标记已掌握' : '继续练习' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getAssessment, masterWeakness } from '../../utils/service'
import { poll } from '../../utils/poll'

const sessionId = ref('')
const weaknessName = ref('')
const weaknessId = ref('')
const loading = ref(true)
const assessment = ref<any>({})
const history = ref<any[]>([])

const trendLabel: Record<string, string> = { rising: '📈 上升中', stable: '➡️ 持平', falling: '📉 下降中' }

const gaugeColor = computed(() => {
  const score = assessment.value.mastery_score || 0
  if (score >= 80) return '#10B981'
  if (score >= 60) return '#F59E0B'
  return '#EF4444'
})

onMounted(async () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  sessionId.value = currentPage?.options?.sessionId || 'ps-001'
  weaknessName.value = decodeURIComponent(currentPage?.options?.weaknessName || '')
  weaknessId.value = currentPage?.options?.weaknessId || ''

  try {
    // 轮询直到 status === 'assessed'（后端异步评估）
    const res = await poll(
      () => getAssessment(sessionId.value),
      (data: any) => data?.code === 0 && data?.data?.status === 'assessed',
      2500,
      60
    )
    if (res.code === 0) {
      assessment.value = res.data
      history.value = res.data.history || []
    }
  } catch (e: any) {
    uni.showToast({ title: e.message || '评估超时，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
})

function goHome() {
  uni.switchTab({ url: '/pages/home/index' })
}

async function continuePractice() {
  if (assessment.value.recommendation === 'mastered') {
    if (!weaknessId.value) {
      uni.showToast({ title: '已标记为掌握', icon: 'success' })
      setTimeout(() => goHome(), 1000)
      return
    }
    try {
      const res = await masterWeakness(weaknessId.value)
      if (res.code === 0) {
        uni.showToast({ title: '已标记为掌握', icon: 'success' })
        setTimeout(() => goHome(), 1000)
      }
    } catch (e: any) {
      uni.showToast({ title: e.message || '标记失败', icon: 'none' })
    }
  } else {
    uni.navigateBack()
  }
}
</script>

<style lang="scss" scoped>
.result-page {
  min-height: 100vh;
  background: #F8FAFC;
  padding-bottom: 180rpx;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  gap: 24rpx;
}

.loading-spinner {
  width: 80rpx;
  height: 80rpx;
  border: 6rpx solid #E2E8F0;
  border-top-color: #2563EB;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.loading-text { font-size: 32rpx; font-weight: 600; color: #1E293B; }

/* 仪表盘 */
.gauge-section {
  display: flex;
  align-items: center;
  gap: 40rpx;
  background: #FFFFFF;
  margin: 16rpx;
  padding: 40rpx;
  border-radius: 20rpx;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.gauge-ring {
  width: 200rpx;
  height: 200rpx;
  border-radius: 50%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gauge-bg {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #E2E8F0;
}

.gauge-fill {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  mask: radial-gradient(transparent 80rpx, #000 81rpx);
  -webkit-mask: radial-gradient(transparent 80rpx, #000 81rpx);
}

.gauge-inner {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: #FFFFFF;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.gauge-num {
  font-size: 56rpx;
  font-weight: 700;
  color: #1E293B;
}

.gauge-label {
  font-size: 22rpx;
  color: #64748B;
}

.gauge-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.trend-badge {
  display: inline-flex;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  font-size: 26rpx;
  font-weight: 600;
  width: fit-content;

  &.rising { background: #D1FAE5; color: #065F46; }
  &.stable { background: #F1F5F9; color: #475569; }
  &.falling { background: #FEE2E2; color: #991B1B; }
}

.error-pattern {
  font-size: 26rpx;
  color: #64748B;
  line-height: 1.5;
}

/* AI 建议 */
.advice-card {
  background: #FFFFFF;
  margin: 0 16rpx 16rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  border-left: 6rpx solid #2563EB;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.advice-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
  margin-bottom: 16rpx;
}

.advice-text {
  font-size: 28rpx;
  color: #475569;
  line-height: 1.6;
  display: block;
  margin-bottom: 20rpx;
}

.advice-action {
  display: flex;
  align-items: center;
  gap: 12rpx;
  background: #FEF3C7;
  padding: 16rpx 20rpx;
  border-radius: 12rpx;

  &.success {
    background: #D1FAE5;
  }
}

.action-icon {
  font-size: 32rpx;
}

.action-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #1E293B;
}

.highlight {
  color: #2563EB;
  font-weight: 700;
  font-size: 36rpx;
}

/* 数据卡片 */
.data-card {
  background: #FFFFFF;
  margin: 0 16rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.data-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
  margin-bottom: 20rpx;
}

.data-row {
  display: flex;
}

.data-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.data-num {
  font-size: 44rpx;
  font-weight: 700;
  color: #2563EB;
}

.data-label {
  font-size: 24rpx;
  color: #64748B;
}

/* 底部 */
.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 16rpx;
  background: #FFFFFF;
  padding: 24rpx 32rpx;
  box-shadow: 0 -2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.secondary-btn {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  background: #FFFFFF;
  color: #2563EB;
  font-size: 30rpx;
  font-weight: 600;
  border: 2rpx solid #2563EB;
  border-radius: 16rpx;
}

.primary-btn {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  background: #2563EB;
  color: #FFFFFF;
  font-size: 30rpx;
  font-weight: 600;
  border: none;
  border-radius: 16rpx;
}
</style>
