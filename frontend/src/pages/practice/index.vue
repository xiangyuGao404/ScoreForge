<template>
  <view class="practice-page">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <view class="loading-spinner"></view>
      <text class="loading-text">正在生成题目...</text>
    </view>

    <view v-else>
      <!-- 进度条 -->
      <view class="progress-header">
        <text class="progress-label">{{ currentIndex + 1 }} / {{ questions.length }}</text>
        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: ((currentIndex + 1) / questions.length * 100) + '%' }"></view>
        </view>
      </view>

      <!-- 知识点标题 -->
      <view class="weakness-title">
        <text>{{ weaknessName }}</text>
      </view>

      <!-- 当前题目 -->
      <view class="question-card">
        <view class="q-header">
          <view class="q-no">第 {{ currentQ.question_no }} 题</view>
          <view class="q-difficulty" :class="currentQ.difficulty">
            {{ difficultyLabel[currentQ.difficulty] }}
          </view>
        </view>

        <text class="q-content">{{ currentQ.question_content }}</text>

        <!-- 答题区域 -->
        <view class="answer-area">
          <!-- 选择题 -->
          <view v-if="currentQ.question_type === 'choice'" class="choice-area">
            <view
              v-for="opt in ['A', 'B', 'C', 'D']"
              :key="opt"
              class="choice-option"
              :class="{ selected: answers[currentIndex] === opt }"
              @tap="selectAnswer(opt)"
            >
              <text class="opt-letter">{{ opt }}</text>
            </view>
          </view>

          <!-- 填空/解答 -->
          <view v-else class="text-area">
            <textarea
              v-model="answers[currentIndex]"
              placeholder="请输入你的答案..."
              class="answer-input"
              :maxlength="500"
            />
          </view>
        </view>
      </view>

      <!-- 参考答案（提交后显示） -->
      <view v-if="showAnswer" class="answer-section">
        <view class="answer-header">
          <text class="answer-title">📖 参考答案</text>
        </view>
        <view class="answer-card">
          <text class="ref-answer">{{ currentQ.reference_answer }}</text>
          <view class="divider"></view>
          <text class="solution-title">解析：</text>
          <text class="solution-detail">{{ currentQ.solution_detail }}</text>
        </view>
      </view>

      <!-- 底部操作 -->
      <view class="bottom-bar safe-area-bottom">
        <button
          v-if="!showAnswer"
          class="submit-btn"
          :disabled="!answers[currentIndex]"
          @tap="submitCurrent"
        >
          提交答案
        </button>
        <view v-else class="nav-buttons">
          <button class="nav-btn" :disabled="currentIndex === 0" @tap="prevQuestion">
            上一题
          </button>
          <button class="nav-btn primary" @tap="nextQuestion">
            {{ currentIndex < questions.length - 1 ? '下一题' : '查看结果' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getPracticeQuestions, submitPracticeResult } from '../../utils/service'

interface Question {
  question_no: number
  difficulty: 'basic' | 'medium' | 'advanced'
  question_type: 'choice' | 'fill_blank' | 'solve'
  question_content: string
  reference_answer: string
  solution_detail: string
}

const sessionId = ref('')
const weaknessName = ref('')
const loading = ref(true)
const questions = ref<Question[]>([])
const currentIndex = ref(0)
const answers = ref<string[]>([])
const results = ref<boolean[]>([])
const showAnswer = ref(false)

const difficultyLabel: Record<string, string> = { basic: '基础', medium: '中等', advanced: '进阶' }

const currentQ = computed(() => questions.value[currentIndex.value] || {} as Question)

onMounted(async () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  sessionId.value = currentPage?.options?.sessionId || 'ps-001'
  weaknessName.value = decodeURIComponent(currentPage?.options?.weaknessName || '函数基础概念')

  const res = await getPracticeQuestions(sessionId.value)
  if (res.code === 0) {
    questions.value = res.data.questions
    answers.value = new Array(questions.value.length).fill('')
    results.value = new Array(questions.value.length).fill(false)
  }
  loading.value = false
})

function selectAnswer(opt: string) {
  answers.value[currentIndex.value = currentIndex.value] = opt
  answers.value[currentIndex.value] = opt
}

function submitCurrent() {
  if (!answers.value[currentIndex.value]) return
  // 简单判断对错
  const correct = answers.value[currentIndex.value].trim().toLowerCase() ===
    currentQ.value.reference_answer.trim().toLowerCase()
  results.value[currentIndex.value] = correct
  showAnswer.value = true
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    showAnswer.value = false
  }
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
    showAnswer.value = false
  } else {
    // 提交全部结果
    finishPractice()
  }
}

async function finishPractice() {
  uni.showLoading({ title: '正在评估...' })
  try {
    const submitResults = questions.value.map((q, i) => ({
      question_no: q.question_no,
      student_answer: answers.value[i],
      is_correct: results.value[i],
    }))
    await submitPracticeResult(sessionId.value, submitResults)
    uni.hideLoading()
    uni.redirectTo({
      url: `/pages/practice/result?sessionId=${sessionId.value}&weaknessName=${encodeURIComponent(weaknessName.value)}`,
    })
  } catch (e: any) {
    uni.hideLoading()
    uni.showToast({ title: e.message || '提交失败', icon: 'none' })
  }
}
</script>

<style lang="scss" scoped>
.practice-page {
  min-height: 100vh;
  background: #F8FAFC;
  padding-bottom: 160rpx;
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

.progress-header {
  background: #FFFFFF;
  padding: 16rpx 32rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.progress-label {
  font-size: 26rpx;
  font-weight: 600;
  color: #2563EB;
  white-space: nowrap;
}

.progress-bar {
  flex: 1;
  height: 12rpx;
  background: #E2E8F0;
  border-radius: 6rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #2563EB;
  border-radius: 6rpx;
  transition: width 0.3s;
}

.weakness-title {
  background: #DBEAFE;
  padding: 16rpx 32rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: #2563EB;
}

.question-card {
  background: #FFFFFF;
  margin: 16rpx;
  border-radius: 16rpx;
  padding: 28rpx;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.q-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.q-no {
  font-size: 28rpx;
  font-weight: 700;
  color: #2563EB;
}

.q-difficulty {
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 6rpx;

  &.basic { background: #D1FAE5; color: #065F46; }
  &.medium { background: #FEF3C7; color: #92400E; }
  &.advanced { background: #FEE2E2; color: #991B1B; }
}

.q-content {
  font-size: 30rpx;
  color: #1E293B;
  line-height: 1.8;
  white-space: pre-wrap;
  display: block;
  margin-bottom: 32rpx;
}

/* 选择题 */
.choice-area {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.choice-option {
  width: calc(50% - 8rpx);
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 12rpx;
  font-size: 32rpx;
  font-weight: 600;
  color: #1E293B;

  &.selected {
    background: #DBEAFE;
    border-color: #2563EB;
    color: #2563EB;
  }
}

/* 文本输入 */
.text-area {
  margin-top: 8rpx;
}

.answer-input {
  width: 100%;
  min-height: 200rpx;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

/* 参考答案 */
.answer-section {
  margin: 0 16rpx;
}

.answer-header {
  margin-bottom: 12rpx;
}

.answer-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #1E293B;
}

.answer-card {
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 24rpx;
  border-left: 6rpx solid #10B981;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.ref-answer {
  font-size: 30rpx;
  font-weight: 700;
  color: #10B981;
  display: block;
  margin-bottom: 16rpx;
}

.divider {
  height: 2rpx;
  background: #E2E8F0;
  margin-bottom: 16rpx;
}

.solution-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #1E293B;
  display: block;
  margin-bottom: 8rpx;
}

.solution-detail {
  font-size: 26rpx;
  color: #475569;
  line-height: 1.8;
  white-space: pre-wrap;
  display: block;
}

/* 底部 */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #FFFFFF;
  padding: 24rpx 32rpx;
  box-shadow: 0 -2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: #2563EB;
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 600;
  border-radius: 16rpx;
  border: none;

  &[disabled] {
    background: #CBD5E1;
    color: #94A3B8;
  }
}

.nav-buttons {
  display: flex;
  gap: 16rpx;
}

.nav-btn {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  font-size: 30rpx;
  font-weight: 600;
  border-radius: 16rpx;
  border: 2rpx solid #2563EB;
  background: #FFFFFF;
  color: #2563EB;

  &.primary {
    background: #2563EB;
    color: #FFFFFF;
  }

  &[disabled] {
    border-color: #CBD5E1;
    color: #CBD5E1;
  }
}
</style>
