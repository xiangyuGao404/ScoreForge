<template>
  <view class="confirm-page">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <view class="loading-spinner"></view>
      <text class="loading-text">AI 正在识别试卷...</text>
      <text class="loading-sub">预计需要 10-15 秒</text>
    </view>

    <!-- 识别结果 -->
    <view v-else>
      <!-- 统计摘要 -->
      <view class="summary-bar">
        <view class="summary-item">
          <text class="summary-num">{{ questions.length }}</text>
          <text class="summary-label">总题数</text>
        </view>
        <view class="summary-item">
          <text class="summary-num correct">{{ correctCount }}</text>
          <text class="summary-label">正确</text>
        </view>
        <view class="summary-item">
          <text class="summary-num wrong">{{ wrongCount }}</text>
          <text class="summary-label">错误</text>
        </view>
        <view class="summary-item">
          <text class="summary-num low">{{ lowConfidenceCount }}</text>
          <text class="summary-label">需确认</text>
        </view>
      </view>

      <view class="tip-bar">
        <text class="tip-icon">💡</text>
        <text class="tip-text">请逐题核对 AI 识别结果，点击题目可修改对错状态</text>
      </view>

      <!-- 题目列表 -->
      <view class="question-list">
        <view
          v-for="q in questions"
          :key="q.question_no"
          class="question-card"
          :class="{
            'low-confidence': q.confidence < 0.7,
            correct: q.is_correct,
            wrong: !q.is_correct,
          }"
        >
          <view class="q-header">
            <view class="q-no-badge" :class="{ correct: q.is_correct, wrong: !q.is_correct }">
              <text class="q-no">{{ q.question_no }}</text>
            </view>
            <view class="q-status">
              <text
                class="status-tag"
                :class="{ correct: q.is_correct, wrong: !q.is_correct }"
              >
                {{ q.is_correct ? '✓ 正确' : '✗ 错误' }}
              </text>
              <view v-if="q.confidence < 0.7" class="confidence-warn">
                <text class="warn-text">⚠️ 置信度 {{ (q.confidence * 100).toFixed(0) }}%，请核实</text>
              </view>
            </view>
          </view>

          <text class="q-content">{{ latexToText(q.question_content) }}</text>

          <view class="q-score-row">
            <text class="score-label">得分：</text>
            <input
              v-model="q.score_got"
              type="digit"
              class="score-input"
              @blur="validateScore(q)"
            />
            <text class="score-total">/ {{ q.score_total }}</text>
          </view>

          <view class="q-actions">
            <view
              class="action-btn"
              :class="{ active: q.is_correct }"
              @tap="setCorrect(q, true)"
            >
              <text>✓ 正确</text>
            </view>
            <view
              class="action-btn wrong"
              :class="{ active: !q.is_correct }"
              @tap="setCorrect(q, false)"
            >
              <text>✗ 错误</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 底部按钮 -->
      <view class="bottom-bar safe-area-bottom">
        <button class="confirm-btn" :loading="submitting" @tap="handleConfirm">
          确认提交 · 开始分析
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getRecognition, confirmRecognition } from '../../utils/service'
import { latexToText } from '../../utils/math'

interface Question {
  question_no: number
  question_content: string
  is_correct: boolean
  score_got: number
  score_total: number
  confidence: number
  parent_verified: boolean
}

const examId = ref('')
const loading = ref(true)
const submitting = ref(false)
const questions = ref<Question[]>([])

const correctCount = computed(() => questions.value.filter(q => q.is_correct).length)
const wrongCount = computed(() => questions.value.filter(q => !q.is_correct).length)
const lowConfidenceCount = computed(() => questions.value.filter(q => q.confidence < 0.7).length)

onMounted(() => {
  // 从页面参数获取 examId
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  examId.value = currentPage?.options?.examId || 'exam-001'
  loadRecognition()
})

async function loadRecognition() {
  loading.value = true
  try {
    const res = await getRecognition(examId.value)
    if (res.code === 0) {
      // 标准化字段：后端可能返回 null，需给默认值
      questions.value = (res.data.questions || []).map((q: any) => ({
        question_no: q.question_no,
        question_content: q.question_content || `第${q.question_no}题（内容识别中）`,
        is_correct: q.is_correct ?? false,
        score_got: q.score_got ?? 0,
        score_total: q.score_total ?? 0,
        confidence: q.confidence ?? 0,
        parent_verified: q.parent_verified ?? false,
      }))
    }
  } catch (e: any) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function setCorrect(q: Question, val: boolean) {
  q.is_correct = val
  if (val) {
    q.score_got = q.score_total
  } else {
    q.score_got = 0
  }
  q.parent_verified = true
}

function validateScore(q: Question) {
  const score = Number(q.score_got)
  if (isNaN(score) || score < 0) q.score_got = 0
  if (score > q.score_total) q.score_got = q.score_total
  q.is_correct = Number(q.score_got) >= Number(q.score_total)
}

async function handleConfirm() {
  submitting.value = true
  try {
    const res = await confirmRecognition(
      examId.value,
      questions.value.map(q => ({
        question_no: q.question_no,
        is_correct: !!q.is_correct, // 确保是 boolean，不是 null
        score_got: Number(q.score_got) || 0,
        parent_verified: true,
      }))
    )
    if (res.code === 0) {
      uni.showToast({ title: '提交成功', icon: 'success' })
      setTimeout(() => {
        uni.redirectTo({
          url: `/pages/exam/analysis?examId=${examId.value}`,
        })
      }, 500)
    }
  } catch (e: any) {
    uni.showToast({ title: e.message || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.confirm-page {
  min-height: 100vh;
  background: #F8FAFC;
  padding-bottom: 160rpx;
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

/* 统计摘要 */
.summary-bar {
  display: flex;
  background: #FFFFFF;
  padding: 24rpx 16rpx;
  margin-bottom: 2rpx;
}

.summary-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.summary-num {
  font-size: 40rpx;
  font-weight: 700;
  color: #1E293B;

  &.correct { color: #10B981; }
  &.wrong { color: #EF4444; }
  &.low { color: #F59E0B; }
}

.summary-label {
  font-size: 22rpx;
  color: #64748B;
}

/* 提示条 */
.tip-bar {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 16rpx 32rpx;
  background: #FFFBEB;
  border-bottom: 2rpx solid #FDE68A;
}

.tip-icon {
  font-size: 28rpx;
}

.tip-text {
  font-size: 24rpx;
  color: #92400E;
}

/* 题目卡片 */
.question-list {
  padding: 16rpx;
}

.question-card {
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
  border-left: 6rpx solid #E2E8F0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);

  &.correct { border-left-color: #10B981; }
  &.wrong { border-left-color: #EF4444; }
  &.low-confidence { border-left-color: #F59E0B; }
}

.q-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.q-no-badge {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #E2E8F0;

  &.correct { background: #D1FAE5; }
  &.wrong { background: #FEE2E2; }

  .q-no {
    font-size: 24rpx;
    font-weight: 700;
    color: #1E293B;
  }
}

.q-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4rpx;
}

.status-tag {
  font-size: 24rpx;
  font-weight: 600;
  padding: 4rpx 16rpx;
  border-radius: 6rpx;

  &.correct {
    background: #D1FAE5;
    color: #065F46;
  }
  &.wrong {
    background: #FEE2E2;
    color: #991B1B;
  }
}

.confidence-warn {
  background: #FEF3C7;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
}

.warn-text {
  font-size: 20rpx;
  color: #92400E;
}

.q-content {
  font-size: 28rpx;
  color: #1E293B;
  line-height: 1.6;
  margin-bottom: 16rpx;
  white-space: pre-wrap;
}

.q-score-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 16rpx;
}

.score-label {
  font-size: 26rpx;
  color: #64748B;
}

.score-input {
  width: 100rpx;
  height: 56rpx;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 8rpx;
  text-align: center;
  font-size: 28rpx;
  font-weight: 600;
}

.score-total {
  font-size: 26rpx;
  color: #94A3B8;
}

.q-actions {
  display: flex;
  gap: 16rpx;
}

.action-btn {
  flex: 1;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 10rpx;
  font-size: 26rpx;
  color: #64748B;

  &.active {
    background: #D1FAE5;
    border-color: #10B981;
    color: #065F46;
    font-weight: 600;
  }

  &.wrong.active {
    background: #FEE2E2;
    border-color: #EF4444;
    color: #991B1B;
  }
}

/* 底部按钮 */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #FFFFFF;
  padding: 24rpx 32rpx;
  box-shadow: 0 -2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.confirm-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: #2563EB;
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 600;
  border-radius: 16rpx;
  border: none;
}
</style>
