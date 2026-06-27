<template>
  <view class="analysis-page">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <view class="loading-spinner"></view>
      <text class="loading-text">AI 正在分析薄弱点...</text>
      <text class="loading-sub">结合历史数据，为你定制提分方案</text>
    </view>

    <!-- 分析结果 -->
    <view v-else>
      <!-- 考试概览 -->
      <view class="exam-overview">
        <view class="overview-header">
          <text class="overview-title">📊 诊断结果</text>
          <text class="overview-sub">{{ subjectLabel[analysis.subject] || analysis.subject }}</text>
        </view>
        <view class="score-display">
          <view class="score-circle">
            <text class="score-num">{{ analysis.actual_score }}</text>
            <text class="score-total">/{{ analysis.total_score }}</text>
          </view>
          <view class="score-info">
            <text class="score-rate">
              得分率 {{ ((analysis.actual_score / analysis.total_score) * 100).toFixed(0) }}%
            </text>
            <text class="score-desc">发现 {{ weaknesses.length }} 个薄弱方向</text>
          </view>
        </view>
      </view>

      <!-- 提分建议标题 -->
      <view class="section-header">
        <text class="section-title">🎯 提分性价比排序</text>
        <text class="section-desc">星级越高 = 越应该优先练习</text>
      </view>

      <!-- 薄弱点卡片列表 -->
      <view class="weakness-list">
        <view
          v-for="w in weaknesses"
          :key="w.weakness_id"
          class="weakness-card"
          :style="{ borderLeftColor: starColors[w.star_rating] }"
        >
          <!-- 星级标签 -->
          <view class="star-badge" :style="{ background: starBgColors[w.star_rating] }">
            <text class="star-text">{{ '⭐'.repeat(w.star_rating) }}</text>
          </view>

          <!-- 知识点名称 -->
          <text class="weakness-name">{{ w.knowledge_point }}</text>

          <!-- 说明 -->
          <text class="weakness-reason">{{ w.reason }}</text>

          <!-- 操作按钮 -->
          <view class="card-actions">
            <button class="practice-btn" @tap="startPractice(w)">
              开始练习
            </button>
            <view class="sub-info">
              <text class="sub-text">预计 {{ getEstimatedDays(w.star_rating) }} 天可见成效</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 底部操作 -->
      <view class="bottom-actions safe-area-bottom">
        <button class="secondary-btn" @tap="goHome">
          返回首页
        </button>
        <button class="primary-btn" @tap="startAllPractice">
          全部练习
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAnalysis, generatePractice } from '../../utils/service'

interface Weakness {
  weakness_id: string
  knowledge_point: string
  star_rating: number
  reason: string
  status: string
}

const examId = ref('')
const loading = ref(true)
const analysis = ref<any>({})
const weaknesses = ref<Weakness[]>([])

const subjectLabel: Record<string, string> = {
  math: '数学',
  politics: '道法',
  history: '历史',
}

const starColors: Record<number, string> = {
  5: '#EF4444',
  4: '#F59E0B',
  3: '#F59E0B',
  2: '#94A3B8',
  1: '#94A3B8',
}

const starBgColors: Record<number, string> = {
  5: '#FEF2F2',
  4: '#FFF7ED',
  3: '#FFFBEB',
  2: '#F8FAFC',
  1: '#F8FAFC',
}

function getEstimatedDays(star: number): number {
  const map: Record<number, number> = { 5: 3, 4: 5, 3: 7, 2: 10, 1: 14 }
  return map[star] || 7
}

onMounted(async () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  examId.value = currentPage?.options?.examId || 'exam-001'
  await loadAnalysis()
})

async function loadAnalysis() {
  loading.value = true
  try {
    const res = await getAnalysis(examId.value)
    if (res.code === 0) {
      analysis.value = res.data
      weaknesses.value = res.data.weaknesses
    }
  } catch (e: any) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function startPractice(w: Weakness) {
  uni.showLoading({ title: '正在生成题目...' })
  try {
    const res = await generatePractice({
      student_id: 's-001',
      weakness_id: w.weakness_id,
      mode: 'online',
      question_count: 5,
    })
    uni.hideLoading()
    if (res.code === 0) {
      uni.navigateTo({
        url: `/pages/practice/index?sessionId=${res.data.session_id}&weaknessName=${encodeURIComponent(w.knowledge_point)}`,
      })
    }
  } catch (e: any) {
    uni.hideLoading()
    uni.showToast({ title: e.message || '生成失败', icon: 'none' })
  }
}

function startAllPractice() {
  if (weaknesses.value.length > 0) {
    startPractice(weaknesses.value[0])
  }
}

function goHome() {
  uni.switchTab({ url: '/pages/home/index' })
}
</script>

<style lang="scss" scoped>
.analysis-page {
  min-height: 100vh;
  background: #F8FAFC;
  padding-bottom: 180rpx;
}

/* 加载状态 */
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

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #1E293B;
}

.loading-sub {
  font-size: 26rpx;
  color: #64748B;
}

/* 考试概览 */
.exam-overview {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  padding: 40rpx 32rpx;
  margin: 16rpx;
  border-radius: 20rpx;
  color: #FFFFFF;
}

.overview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32rpx;
}

.overview-title {
  font-size: 36rpx;
  font-weight: 700;
}

.overview-sub {
  font-size: 26rpx;
  background: rgba(255, 255, 255, 0.2);
  padding: 6rpx 20rpx;
  border-radius: 8rpx;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 32rpx;
}

.score-circle {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
}

.score-num {
  font-size: 72rpx;
  font-weight: 700;
  line-height: 1;
}

.score-total {
  font-size: 32rpx;
  opacity: 0.7;
}

.score-info {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.score-rate {
  font-size: 28rpx;
  opacity: 0.9;
}

.score-desc {
  font-size: 24rpx;
  opacity: 0.7;
}

/* 区块标题 */
.section-header {
  padding: 24rpx 32rpx 8rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
}

.section-desc {
  font-size: 24rpx;
  color: #64748B;
  display: block;
  margin-top: 4rpx;
}

/* 薄弱点卡片 */
.weakness-list {
  padding: 16rpx;
}

.weakness-card {
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 28rpx;
  margin-bottom: 20rpx;
  border-left: 6rpx solid #2563EB;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.star-badge {
  display: inline-flex;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  margin-bottom: 16rpx;
}

.star-text {
  font-size: 24rpx;
}

.weakness-name {
  font-size: 34rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
  margin-bottom: 12rpx;
}

.weakness-reason {
  font-size: 26rpx;
  color: #64748B;
  line-height: 1.6;
  display: block;
  margin-bottom: 24rpx;
}

.card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.practice-btn {
  height: 64rpx;
  line-height: 64rpx;
  padding: 0 40rpx;
  background: #2563EB;
  color: #FFFFFF;
  font-size: 28rpx;
  font-weight: 600;
  border-radius: 12rpx;
  border: none;
}

.sub-info {
  flex: 1;
  text-align: right;
}

.sub-text {
  font-size: 22rpx;
  color: #94A3B8;
}

/* 底部操作 */
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
