<template>
  <view class="weakness-page">
    <!-- 筛选标签 -->
    <view class="filter-tabs">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        class="tab-item"
        :class="{ active: currentTab === tab.value }"
        @tap="currentTab = tab.value"
      >
        <text class="tab-text">{{ tab.label }}</text>
        <text v-if="tab.count > 0" class="tab-badge">{{ tab.count }}</text>
      </view>
    </view>

    <!-- 薄弱点列表 -->
    <view class="list-area">
      <view v-if="filteredList.length === 0" class="empty-state">
        <text class="empty-icon">📭</text>
        <text class="empty-text">暂无数据</text>
      </view>

      <view
        v-for="w in filteredList"
        :key="w.weakness_id"
        class="weakness-card"
        :style="{ borderLeftColor: starColors[w.star_rating] }"
      >
        <view class="card-header">
          <view class="star-badge" :style="{ background: starBgColors[w.star_rating] }">
            <text>{{ '⭐'.repeat(w.star_rating) }}</text>
          </view>
          <view class="status-tag" :class="w.status">
            {{ statusLabel[w.status] }}
          </view>
        </view>

        <text class="card-name">{{ w.knowledge_point }}</text>
        <text class="card-reason">{{ w.reason }}</text>

        <!-- 进度条 -->
        <view v-if="w.status !== 'not_started'" class="progress-section">
          <view class="progress-bar">
            <view
              class="progress-fill"
              :style="{
                width: w.mastery_score + '%',
                background: w.mastery_score >= 80 ? '#10B981' : '#F59E0B',
              }"
            ></view>
          </view>
          <text class="progress-text">掌握度 {{ w.mastery_score }}%</text>
        </view>

        <view class="card-meta">
          <text class="meta-text">已练 {{ w.practice_days }}/{{ w.recommended_days }} 天</text>
        </view>

        <view class="card-actions">
          <button
            v-if="w.status !== 'mastered'"
            class="action-btn primary"
            @tap="startPractice(w)"
          >
            {{ w.status === 'practicing' ? '继续练习' : '开始练习' }}
          </button>
          <button
            v-if="w.status === 'practicing' && w.mastery_score >= 80"
            class="action-btn success"
            @tap="markMastered(w)"
          >
            标记已掌握
          </button>
          <view v-if="w.status === 'mastered'" class="mastered-badge">
            <text>✅ 已掌握</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getWeaknesses, masterWeakness, generatePractice } from '../../utils/service'
import { useStudentStore } from '../../store/student'

interface Weakness {
  weakness_id: string
  student_id: string
  knowledge_point: string
  star_rating: number
  reason: string
  status: 'not_started' | 'practicing' | 'mastered'
  mastery_score: number
  practice_days: number
  recommended_days: number
}

const currentTab = ref('all')
const list = ref<Weakness[]>([])

const starColors: Record<number, string> = { 5: '#EF4444', 4: '#F59E0B', 3: '#F59E0B', 2: '#94A3B8', 1: '#94A3B8' }
const starBgColors: Record<number, string> = { 5: '#FEF2F2', 4: '#FFF7ED', 3: '#FFFBEB', 2: '#F8FAFC', 1: '#F8FAFC' }
const statusLabel: Record<string, string> = { not_started: '未开始', practicing: '练习中', mastered: '已掌握' }

const tabs = computed(() => [
  { value: 'all', label: '全部', count: list.value.length },
  { value: 'not_started', label: '未开始', count: list.value.filter(w => w.status === 'not_started').length },
  { value: 'practicing', label: '练习中', count: list.value.filter(w => w.status === 'practicing').length },
  { value: 'mastered', label: '已掌握', count: list.value.filter(w => w.status === 'mastered').length },
])

const filteredList = computed(() => {
  if (currentTab.value === 'all') return list.value
  return list.value.filter(w => w.status === currentTab.value)
})

onMounted(async () => {
  const studentStore = useStudentStore()
  const sid = studentStore.currentStudent?.id
  const res = await getWeaknesses(sid)
  if (res.code === 0) list.value = res.data
})

async function startPractice(w: Weakness) {
  uni.showLoading({ title: '正在生成题目...' })
  try {
    const res = await generatePractice({
      student_id: w.student_id,
      weakness_id: w.weakness_id,
      mode: 'online',
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

async function markMastered(w: Weakness) {
  uni.showModal({
    title: '确认标记',
    content: `确定将"${w.knowledge_point}"标记为已掌握？`,
    success: async (res) => {
      if (res.confirm) {
        const r = await masterWeakness(w.weakness_id)
        if (r.code === 0) {
          w.status = 'mastered'
          w.mastery_score = 100
          uni.showToast({ title: '已标记为掌握', icon: 'success' })
        }
      }
    },
  })
}
</script>

<style lang="scss" scoped>
.weakness-page {
  min-height: 100vh;
  background: #F8FAFC;
}

.filter-tabs {
  display: flex;
  background: #FFFFFF;
  padding: 16rpx;
  gap: 12rpx;
  position: sticky;
  top: 0;
  z-index: 10;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  height: 64rpx;
  background: #F8FAFC;
  border-radius: 10rpx;
  font-size: 26rpx;
  color: #64748B;

  &.active {
    background: #DBEAFE;
    color: #2563EB;
    font-weight: 600;
  }
}

.tab-badge {
  font-size: 20rpx;
  background: #E2E8F0;
  padding: 2rpx 10rpx;
  border-radius: 8rpx;

  .active & {
    background: #2563EB;
    color: #FFFFFF;
  }
}

.list-area {
  padding: 16rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
  gap: 16rpx;
}

.empty-icon { font-size: 64rpx; }
.empty-text { font-size: 28rpx; color: #94A3B8; }

.weakness-card {
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 28rpx;
  margin-bottom: 20rpx;
  border-left: 6rpx solid #E2E8F0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.star-badge {
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
  font-size: 22rpx;
}

.status-tag {
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 6rpx;

  &.not_started { background: #F1F5F9; color: #64748B; }
  &.practicing { background: #FEF3C7; color: #92400E; }
  &.mastered { background: #D1FAE5; color: #065F46; }
}

.card-name {
  font-size: 32rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
  margin-bottom: 8rpx;
}

.card-reason {
  font-size: 26rpx;
  color: #64748B;
  line-height: 1.5;
  display: block;
  margin-bottom: 16rpx;
}

.progress-section {
  margin-bottom: 12rpx;
}

.progress-bar {
  height: 12rpx;
  background: #E2E8F0;
  border-radius: 6rpx;
  overflow: hidden;
  margin-bottom: 6rpx;
}

.progress-fill {
  height: 100%;
  border-radius: 6rpx;
  transition: width 0.3s;
}

.progress-text {
  font-size: 22rpx;
  color: #64748B;
}

.card-meta {
  margin-bottom: 16rpx;
}

.meta-text {
  font-size: 22rpx;
  color: #94A3B8;
}

.card-actions {
  display: flex;
  gap: 12rpx;
}

.action-btn {
  flex: 1;
  height: 64rpx;
  line-height: 64rpx;
  font-size: 28rpx;
  font-weight: 600;
  border-radius: 12rpx;
  border: none;

  &.primary {
    background: #2563EB;
    color: #FFFFFF;
  }

  &.success {
    background: #10B981;
    color: #FFFFFF;
  }
}

.mastered-badge {
  font-size: 28rpx;
  color: #10B981;
  font-weight: 600;
}
</style>
