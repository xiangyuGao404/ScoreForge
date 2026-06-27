<template>
  <view class="settings-page">
    <!-- 用户信息 -->
    <view class="user-card">
      <view class="user-avatar">👤</view>
      <view class="user-info">
        <text class="user-name">{{ userStore.nickname || '未登录' }}</text>
        <text class="user-level" :class="userStore.userLevel">
          {{ userStore.userLevel === 'paid' ? 'Pro 会员' : '免费版' }}
        </text>
      </view>
    </view>

    <!-- 孩子管理 -->
    <view class="section">
      <text class="section-title">👶 孩子管理</text>
      <view
        v-for="s in students"
        :key="s.id"
        class="setting-item"
        @tap="goStudentManage"
      >
        <view class="item-left">
          <text class="item-icon">👦</text>
          <view class="item-info">
            <text class="item-name">{{ s.name }}</text>
            <text class="item-desc">{{ s.grade }} · {{ s.school }}</text>
          </view>
        </view>
        <text class="item-arrow">›</text>
      </view>
      <view class="add-btn" @tap="goStudentManage">
        <text class="add-icon">+</text>
        <text class="add-text">添加孩子</text>
      </view>
    </view>

    <!-- API 配置 -->
    <view class="section">
      <text class="section-title">🔑 API 配置</text>
      <view class="setting-item">
        <view class="item-left">
          <text class="item-icon">🤖</text>
          <view class="item-info">
            <text class="item-name">AI 模式</text>
            <text class="item-desc">{{ apiMode === 'builtin' ? '系统内置（¥0.99/月）' : '自备 API Key' }}</text>
          </view>
        </view>
        <switch :checked="apiMode === 'custom'" @change="toggleApiMode" color="#2563EB" />
      </view>

      <view v-if="apiMode === 'custom'" class="setting-item">
        <view class="item-left full">
          <text class="item-label">API Key</text>
          <input
            v-model="apiKey"
            type="text"
            placeholder="输入你的 OpenAI API Key"
            class="key-input"
            :password="!showKey"
          />
        </view>
        <text class="toggle-eye" @tap="showKey = !showKey">
          {{ showKey ? '🙈' : '👁️' }}
        </text>
      </view>
    </view>

    <!-- 其他设置 -->
    <view class="section">
      <text class="section-title">⚙️ 其他</text>
      <view class="setting-item" @tap="showAbout">
        <view class="item-left">
          <text class="item-icon">ℹ️</text>
          <view class="item-info">
            <text class="item-name">关于 ScoreForge</text>
            <text class="item-desc">版本 1.0.0</text>
          </view>
        </view>
        <text class="item-arrow">›</text>
      </view>

      <view class="setting-item" @tap="showFeedback">
        <view class="item-left">
          <text class="item-icon">💬</text>
          <view class="item-info">
            <text class="item-name">意见反馈</text>
          </view>
        </view>
        <text class="item-arrow">›</text>
      </view>
    </view>

    <!-- 退出登录 -->
    <view class="logout-area">
      <button class="logout-btn" @tap="handleLogout">退出登录</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '../../store/user'
import { useStudentStore } from '../../store/student'

const userStore = useUserStore()
const studentStore = useStudentStore()

const students = computed(() => studentStore.students)
const apiMode = ref<'builtin' | 'custom'>('builtin')
const apiKey = ref('')
const showKey = ref(false)

function toggleApiMode(e: any) {
  apiMode.value = e.detail.value ? 'custom' : 'builtin'
  if (apiMode.value === 'builtin') {
    apiKey.value = ''
  }
}

function goStudentManage() {
  uni.showToast({ title: '孩子管理页面开发中', icon: 'none' })
}

function showAbout() {
  uni.showModal({
    title: '关于 ScoreForge',
    content: 'ScoreForge V1.0.0\nAI 学情诊断工具\n\n拍一张试卷，AI 告诉你孩子最该补哪里。',
    showCancel: false,
  })
}

function showFeedback() {
  uni.showToast({ title: '反馈功能开发中', icon: 'none' })
}

function handleLogout() {
  uni.showModal({
    title: '确认退出',
    content: '退出后需要重新登录',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
        uni.reLaunch({ url: '/pages/login/index' })
      }
    },
  })
}
</script>

<style lang="scss" scoped>
.settings-page {
  min-height: 100vh;
  background: #F8FAFC;
  padding-bottom: 32rpx;
}

/* 用户卡片 */
.user-card {
  display: flex;
  align-items: center;
  gap: 24rpx;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  margin: 16rpx;
  padding: 32rpx;
  border-radius: 20rpx;
  color: #FFFFFF;
}

.user-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.user-name {
  font-size: 32rpx;
  font-weight: 700;
}

.user-level {
  font-size: 22rpx;
  padding: 2rpx 12rpx;
  border-radius: 6rpx;
  width: fit-content;

  &.paid {
    background: rgba(255, 255, 255, 0.2);
  }
  &.free {
    background: rgba(255, 255, 255, 0.1);
  }
}

/* 区块 */
.section {
  background: #FFFFFF;
  margin: 16rpx;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
  margin-bottom: 16rpx;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 0;
  border-bottom: 2rpx solid #F1F5F9;

  &:last-child {
    border-bottom: none;
  }
}

.item-left {
  display: flex;
  align-items: center;
  gap: 16rpx;

  &.full {
    flex: 1;
    flex-direction: column;
    align-items: flex-start;
    gap: 8rpx;
  }
}

.item-icon {
  font-size: 36rpx;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}

.item-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #1E293B;
}

.item-desc {
  font-size: 22rpx;
  color: #64748B;
}

.item-arrow {
  font-size: 36rpx;
  color: #CBD5E1;
}

.item-label {
  font-size: 26rpx;
  font-weight: 600;
  color: #1E293B;
}

.key-input {
  width: 100%;
  height: 72rpx;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 26rpx;
  box-sizing: border-box;
}

.toggle-eye {
  font-size: 32rpx;
  padding: 8rpx;
}

/* 添加按钮 */
.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  padding: 20rpx;
  border: 2rpx dashed #CBD5E1;
  border-radius: 12rpx;
  margin-top: 12rpx;
}

.add-icon {
  font-size: 32rpx;
  color: #94A3B8;
}

.add-text {
  font-size: 26rpx;
  color: #94A3B8;
}

/* 退出登录 */
.logout-area {
  padding: 32rpx 16rpx;
}

.logout-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: #FFFFFF;
  color: #EF4444;
  font-size: 30rpx;
  font-weight: 600;
  border: 2rpx solid #FEE2E2;
  border-radius: 16rpx;
}
</style>
