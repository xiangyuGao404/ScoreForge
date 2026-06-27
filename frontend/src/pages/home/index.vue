<template>
  <view class="home-page">
    <!-- 顶部：孩子切换 + 上传入口 -->
    <view class="top-bar">
      <view class="child-selector" @tap="showChildPicker = true">
        <text class="child-avatar">👦</text>
        <text class="child-name">{{ currentStudent?.name || '请选择孩子' }}</text>
        <text class="arrow">▼</text>
      </view>
      <button class="upload-fab" @tap="goUpload">
        <text class="fab-icon">📷</text>
        <text class="fab-text">上传试卷</text>
      </button>
    </view>

    <!-- 孩子选择弹窗 -->
    <view v-if="showChildPicker" class="picker-mask" @tap="showChildPicker = false">
      <view class="picker-modal" @tap.stop>
        <text class="picker-title">选择孩子</text>
        <view
          v-for="s in students"
          :key="s.id"
          class="picker-item"
          :class="{ active: s.id === currentStudent?.id }"
          @tap="switchChild(s.id)"
        >
          <text class="picker-name">{{ s.name }}</text>
          <text class="picker-grade">{{ s.grade }} · {{ s.school }}</text>
        </view>
      </view>
    </view>

    <!-- 概览卡片 -->
    <view class="overview-card">
      <view class="overview-row">
        <view class="overview-item">
          <text class="ov-num">{{ stats.totalExams }}</text>
          <text class="ov-label">试卷数</text>
        </view>
        <view class="overview-item">
          <text class="ov-num practicing">{{ stats.practicing }}</text>
          <text class="ov-label">练习中</text>
        </view>
        <view class="overview-item">
          <text class="ov-num mastered">{{ stats.mastered }}</text>
          <text class="ov-label">已掌握</text>
        </view>
      </view>
    </view>

    <!-- 最近诊断 -->
    <view class="section" v-if="recentExam">
      <text class="section-title">📋 最近诊断</text>
      <view class="recent-card" @tap="goAnalysis(recentExam.id)">
        <view class="recent-header">
          <text class="recent-subject">{{ recentExam.subject }}</text>
          <text class="recent-date">{{ recentExam.date }}</text>
        </view>
        <view class="recent-score">
          <text class="score-val">{{ recentExam.score }}</text>
          <text class="score-total">/{{ recentExam.total }}</text>
        </view>
        <text class="recent-weakness">发现 {{ recentExam.weaknessCount }} 个薄弱点</text>
      </view>
    </view>

    <!-- 待练薄弱点 -->
    <view class="section">
      <text class="section-title">🎯 待练薄弱点</text>
      <view v-if="pendingWeaknesses.length === 0" class="empty-state">
        <text class="empty-icon">🎉</text>
        <text class="empty-text">暂无待练薄弱点，上传试卷开始诊断吧！</text>
      </view>
      <view
        v-for="w in pendingWeaknesses"
        :key="w.id"
        class="weakness-mini"
        @tap="goPractice(w)"
      >
        <view class="mini-left">
          <text class="mini-stars">{{ '⭐'.repeat(w.stars) }}</text>
          <text class="mini-name">{{ w.name }}</text>
        </view>
        <view class="mini-right">
          <text class="mini-status" :class="w.status">{{ statusLabel[w.status] }}</text>
          <text class="mini-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 快捷入口 -->
    <view class="quick-actions">
      <view class="quick-item" @tap="goWeaknesses">
        <text class="quick-icon">📊</text>
        <text class="quick-text">全部薄弱点</text>
      </view>
      <view class="quick-item" @tap="goChat">
        <text class="quick-icon">💬</text>
        <text class="quick-text">教师团</text>
      </view>
      <view class="quick-item" @tap="goSettings">
        <text class="quick-icon">⚙️</text>
        <text class="quick-text">设置</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useStudentStore } from '../../store/student'
import { getWeaknesses } from '../../utils/service'

const studentStore = useStudentStore()
const showChildPicker = ref(false)

const students = computed(() => studentStore.students)
const currentStudent = computed(() => studentStore.currentStudent)

const statusLabel: Record<string, string> = {
  not_started: '未开始',
  practicing: '练习中',
  mastered: '已掌握',
}

// 数据
const stats = ref({ totalExams: 0, practicing: 0, mastered: 0 })
const recentExam = ref<any>(null)
const pendingWeaknesses = ref<any[]>([])

async function loadHomeData() {
  try {
    const res = await getWeaknesses()
    if (res.code === 0) {
      const list = res.data
      stats.value = {
        totalExams: 0,
        practicing: list.filter((w: any) => w.status === 'practicing').length,
        mastered: list.filter((w: any) => w.status === 'mastered').length,
      }
      pendingWeaknesses.value = list
        .filter((w: any) => w.status !== 'mastered')
        .map((w: any) => ({
          id: w.weakness_id,
          name: w.knowledge_point,
          stars: w.star_rating,
          status: w.status,
        }))
    }
  } catch (e) {
    console.error('加载首页数据失败', e)
  }
}

onMounted(() => {
  loadHomeData()
})

// 切换孩子时刷新数据
function switchChild(id: string) {
  studentStore.switchStudent(id)
  showChildPicker.value = false
  loadHomeData()
}

function goUpload() {
  uni.navigateTo({ url: '/pages/upload/index' })
}

function goAnalysis(examId: string) {
  uni.navigateTo({ url: `/pages/exam/analysis?examId=${examId}` })
}

function goPractice(w: any) {
  uni.navigateTo({ url: `/pages/practice/index?weaknessId=${w.id}&weaknessName=${encodeURIComponent(w.name)}` })
}

function goWeaknesses() {
  uni.switchTab({ url: '/pages/weakness/index' })
}

function goChat() {
  uni.switchTab({ url: '/pages/chat/index' })
}

function goSettings() {
  uni.switchTab({ url: '/pages/settings/index' })
}
</script>

<style lang="scss" scoped>
.home-page {
  min-height: 100vh;
  background: #F8FAFC;
  padding-bottom: 32rpx;
}

/* 顶部栏 */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  background: #FFFFFF;
  margin-bottom: 16rpx;
}

.child-selector {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.child-avatar {
  font-size: 48rpx;
}

.child-name {
  font-size: 32rpx;
  font-weight: 700;
  color: #1E293B;
}

.arrow {
  font-size: 20rpx;
  color: #94A3B8;
}

.upload-fab {
  display: flex;
  align-items: center;
  gap: 8rpx;
  height: 64rpx;
  padding: 0 24rpx;
  background: #2563EB;
  color: #FFFFFF;
  border-radius: 32rpx;
  border: none;
  font-size: 26rpx;
  font-weight: 600;
}

.fab-icon {
  font-size: 28rpx;
}

/* 弹窗 */
.picker-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 100;
  display: flex;
  align-items: flex-end;
}

.picker-modal {
  width: 100%;
  background: #FFFFFF;
  border-radius: 24rpx 24rpx 0 0;
  padding: 32rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
}

.picker-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
  margin-bottom: 24rpx;
}

.picker-item {
  padding: 24rpx;
  border-radius: 12rpx;
  margin-bottom: 12rpx;
  background: #F8FAFC;

  &.active {
    background: #DBEAFE;
  }
}

.picker-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #1E293B;
  display: block;
}

.picker-grade {
  font-size: 24rpx;
  color: #64748B;
  display: block;
  margin-top: 4rpx;
}

/* 概览卡片 */
.overview-card {
  background: #FFFFFF;
  margin: 0 16rpx 16rpx;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.overview-row {
  display: flex;
}

.overview-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.ov-num {
  font-size: 44rpx;
  font-weight: 700;
  color: #1E293B;

  &.practicing { color: #F59E0B; }
  &.mastered { color: #10B981; }
}

.ov-label {
  font-size: 24rpx;
  color: #64748B;
}

/* 区块 */
.section {
  background: #FFFFFF;
  margin: 0 16rpx 16rpx;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
  margin-bottom: 16rpx;
}

/* 最近诊断 */
.recent-card {
  background: #F8FAFC;
  border-radius: 12rpx;
  padding: 20rpx;
}

.recent-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.recent-subject {
  font-size: 26rpx;
  font-weight: 600;
  color: #2563EB;
}

.recent-date {
  font-size: 22rpx;
  color: #94A3B8;
}

.recent-score {
  margin-bottom: 4rpx;
}

.score-val {
  font-size: 40rpx;
  font-weight: 700;
  color: #1E293B;
}

.score-total {
  font-size: 26rpx;
  color: #94A3B8;
}

.recent-weakness {
  font-size: 24rpx;
  color: #64748B;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0;
  gap: 12rpx;
}

.empty-icon {
  font-size: 56rpx;
}

.empty-text {
  font-size: 26rpx;
  color: #94A3B8;
}

/* 薄弱点迷你卡片 */
.weakness-mini {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 0;
  border-bottom: 2rpx solid #F1F5F9;

  &:last-child {
    border-bottom: none;
  }
}

.mini-left {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.mini-stars {
  font-size: 20rpx;
}

.mini-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #1E293B;
}

.mini-right {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.mini-status {
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;

  &.not_started { background: #F1F5F9; color: #64748B; }
  &.practicing { background: #FEF3C7; color: #92400E; }
  &.mastered { background: #D1FAE5; color: #065F46; }
}

.mini-arrow {
  font-size: 32rpx;
  color: #CBD5E1;
}

/* 快捷入口 */
.quick-actions {
  display: flex;
  margin: 0 16rpx;
  gap: 16rpx;
}

.quick-item {
  flex: 1;
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.quick-icon {
  font-size: 40rpx;
}

.quick-text {
  font-size: 24rpx;
  color: #64748B;
}
</style>
