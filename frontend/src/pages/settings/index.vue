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
            <text class="item-desc">{{ s.grade }} · {{ s.school || '未填写学校' }}</text>
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

      <!-- AI 模式 -->
      <view class="form-item">
        <text class="form-label">AI 模式</text>
        <view class="radio-group">
          <view class="radio-item" :class="{ active: apiMode === 'builtin' }" @tap="apiMode = 'builtin'">
            <view class="radio-dot" :class="{ checked: apiMode === 'builtin' }"></view>
            <text>系统内置（¥0.99/月）</text>
          </view>
          <view class="radio-item" :class="{ active: apiMode === 'custom' }" @tap="apiMode = 'custom'">
            <view class="radio-dot" :class="{ checked: apiMode === 'custom' }"></view>
            <text>自备 API Key</text>
          </view>
        </view>
      </view>

      <!-- 自备 Key 配置区域 -->
      <view v-if="apiMode === 'custom'" class="custom-config">
        <!-- AI 平台 -->
        <view class="form-item">
          <text class="form-label">AI 平台</text>
          <view class="platform-tabs">
            <view
              v-for="p in platforms"
              :key="p.value"
              class="platform-tab"
              :class="{ active: config.provider === p.value }"
              @tap="selectPlatform(p.value)"
            >
              <text class="platform-icon">{{ p.icon }}</text>
              <text class="platform-name">{{ p.label }}</text>
            </view>
          </view>
        </view>

        <!-- API Key -->
        <view class="form-item">
          <text class="form-label">API Key</text>
          <view class="key-row">
            <input
              v-model="config.api_key"
              :type="showKey ? 'text' : 'password'"
              :placeholder="keyPlaceholder"
              class="form-input"
            />
            <text class="toggle-eye" @tap="showKey = !showKey">
              {{ showKey ? '🙈' : '👁️' }}
            </text>
          </view>
        </view>

        <!-- API 地址 -->
        <view class="form-item">
          <text class="form-label">API 地址</text>
          <input v-model="config.api_base" :placeholder="basePlaceholder" class="form-input" />
        </view>

        <!-- 通用模型 -->
        <view class="form-item">
          <text class="form-label">通用模型（分析/出题/评估）</text>
          <picker :range="generalModelOptions" :range-key="'label'" @change="onGeneralModelChange">
            <view class="picker-value">
              <text>{{ config.general_model || '请选择模型' }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </picker>
        </view>

        <!-- 图片识别模型 -->
        <view class="form-item">
          <text class="form-label">图片识别模型（试卷识别）</text>
          <picker :range="visionModelOptions" :range-key="'label'" @change="onVisionModelChange">
            <view class="picker-value">
              <text>{{ config.vision_model || '请选择模型' }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </picker>
        </view>

        <!-- 测试连接 -->
        <view class="form-actions">
          <button class="test-btn" :loading="testing" @tap="handleTest">
            🔗 测试连接
          </button>
          <button class="save-btn" :loading="saving" @tap="handleSave">
            💾 保存配置
          </button>
        </view>

        <!-- 测试结果 -->
        <view v-if="testResult" class="test-result" :class="testResult.success ? 'success' : 'fail'">
          <text class="result-icon">{{ testResult.success ? '✅' : '❌' }}</text>
          <view class="result-info">
            <text class="result-text">
              {{ testResult.success ? '连接成功' : '连接失败' }}
            </text>
            <text v-if="testResult.success" class="result-detail">
              模型 {{ testResult.model }} · 响应时间 {{ testResult.latency_ms }}ms
            </text>
            <text v-else class="result-detail error">
              {{ testResult.error || '请检查 API Key 和地址是否正确' }}
            </text>
          </view>
        </view>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import { useStudentStore } from '../../store/student'
import { getApiConfig, saveApiConfig, testApiConfig } from '../../utils/service'

const userStore = useUserStore()
const studentStore = useStudentStore()

const students = computed(() => studentStore.students)
const apiMode = ref<'builtin' | 'custom'>('builtin')
const showKey = ref(false)
const testing = ref(false)
const saving = ref(false)
const testResult = ref<any>(null)

const platforms = [
  { value: 'xiaomi', label: '小米 TokenPlan', icon: '🟠' },
  { value: 'deepseek', label: 'DeepSeek', icon: '🔵' },
  { value: 'openai', label: 'OpenAI 兼容', icon: '🟢' },
]

const modelOptions: Record<string, { general: string[]; vision: string[] }> = {
  xiaomi: {
    general: ['mimo-v2.5-pro'],
    vision: ['mimo-v2.5'],
  },
  deepseek: {
    general: ['deepseek-v4-flash'],
    vision: ['DeepSeek-VL2'],
  },
  openai: {
    general: ['gpt-4o', 'gpt-4o-mini'],
    vision: ['gpt-4o'],
  },
}

const config = reactive({
  provider: 'xiaomi',
  api_key: '',
  api_base: '',
  general_model: 'mimo-v2.5-pro',
  vision_model: 'mimo-v2.5',
})

const generalModelOptions = computed(() =>
  (modelOptions[config.provider]?.general || []).map(m => ({ label: m, value: m }))
)
const visionModelOptions = computed(() =>
  (modelOptions[config.provider]?.vision || []).map(m => ({ label: m, value: m }))
)

const keyPlaceholder = computed(() => {
  const map: Record<string, string> = {
    xiaomi: '输入小米 TokenPlan API Key (tp-xxx)',
    deepseek: '输入 DeepSeek API Key (sk-xxx)',
    openai: '输入 OpenAI API Key (sk-xxx)',
  }
  return map[config.provider] || '输入 API Key'
})

const basePlaceholder = computed(() => {
  const map: Record<string, string> = {
    xiaomi: 'https://token-plan-cn.xiaomimimo.com/v1',
    deepseek: 'https://api.deepseek.com/v1',
    openai: 'https://api.openai.com/v1',
  }
  return map[config.provider] || 'https://...'
})

onMounted(async () => {
  const res = await getApiConfig()
  if (res.code === 0 && res.data) {
    const d = res.data
    if (d.provider) config.provider = d.provider
    if (d.api_base) config.api_base = d.api_base
    if (d.general_model) config.general_model = d.general_model
    if (d.vision_model) config.vision_model = d.vision_model
    if (d.api_key_set) apiMode.value = 'custom'
  }
})

function selectPlatform(val: string) {
  config.provider = val
  config.api_key = ''
  config.api_base = ''
  config.general_model = modelOptions[val]?.general[0] || ''
  config.vision_model = modelOptions[val]?.vision[0] || ''
  testResult.value = null
}

function onGeneralModelChange(e: any) {
  config.general_model = generalModelOptions.value[e.detail.value].value
}

function onVisionModelChange(e: any) {
  config.vision_model = visionModelOptions.value[e.detail.value].value
}

async function handleTest() {
  if (!config.api_key) {
    uni.showToast({ title: '请先填写 API Key', icon: 'none' })
    return
  }
  testing.value = true
  testResult.value = null
  try {
    const res = await testApiConfig({
      provider: config.provider,
      api_key: config.api_key,
      api_base: config.api_base || undefined,
      model: config.general_model,
      task_type: 'general',
    })
    if (res.code === 0) {
      testResult.value = res.data
    } else {
      // 后端 code!=0 时，data 里仍有 {success:false, error:"..."} 结构
      testResult.value = res.data || { success: false, error: res.message }
    }
  } catch (e: any) {
    testResult.value = { success: false, error: e.message || '测试失败' }
  } finally {
    testing.value = false
  }
}

async function handleSave() {
  if (apiMode.value === 'custom' && !config.api_key) {
    uni.showToast({ title: '请填写 API Key', icon: 'none' })
    return
  }
  saving.value = true
  try {
    const res = await saveApiConfig({
      provider: config.provider,
      api_key: config.api_key,
      api_base: config.api_base || undefined,
      general_model: config.general_model,
      vision_model: config.vision_model,
    })
    if (res.code === 0) {
      uni.showToast({ title: '配置已保存', icon: 'success' })
    }
  } catch (e: any) {
    uni.showToast({ title: e.message || '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

function goStudentManage() {
  uni.navigateTo({ url: '/pages/student/manage' })
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

.user-info { display: flex; flex-direction: column; gap: 4rpx; }
.user-name { font-size: 32rpx; font-weight: 700; }
.user-level {
  font-size: 22rpx; padding: 2rpx 12rpx; border-radius: 6rpx; width: fit-content;
  &.paid { background: rgba(255, 255, 255, 0.2); }
  &.free { background: rgba(255, 255, 255, 0.1); }
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
  font-size: 28rpx; font-weight: 700; color: #1E293B;
  display: block; margin-bottom: 16rpx;
}

.setting-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20rpx 0; border-bottom: 2rpx solid #F1F5F9;
  &:last-child { border-bottom: none; }
}

.item-left {
  display: flex; align-items: center; gap: 16rpx;
  &.full { flex: 1; flex-direction: column; align-items: flex-start; gap: 8rpx; }
}

.item-icon { font-size: 36rpx; }
.item-info { display: flex; flex-direction: column; gap: 2rpx; }
.item-name { font-size: 28rpx; font-weight: 600; color: #1E293B; }
.item-desc { font-size: 22rpx; color: #64748B; }
.item-arrow { font-size: 36rpx; color: #CBD5E1; }

/* 表单 */
.form-item { margin-bottom: 24rpx; }
.form-label {
  font-size: 26rpx; font-weight: 600; color: #1E293B;
  display: block; margin-bottom: 12rpx;
}

.form-input {
  width: 100%; height: 80rpx; background: #F8FAFC;
  border: 2rpx solid #E2E8F0; border-radius: 12rpx;
  padding: 0 24rpx; font-size: 28rpx; box-sizing: border-box;
}

/* 单选 */
.radio-group { display: flex; flex-direction: column; gap: 12rpx; }
.radio-item {
  display: flex; align-items: center; gap: 12rpx;
  padding: 16rpx 20rpx; background: #F8FAFC;
  border: 2rpx solid #E2E8F0; border-radius: 12rpx;
  font-size: 28rpx; color: #1E293B;
  &.active { border-color: #2563EB; background: #EFF6FF; }
}
.radio-dot {
  width: 32rpx; height: 32rpx; border-radius: 50%;
  border: 3rpx solid #CBD5E1; position: relative;
  &.checked { border-color: #2563EB; }
  &.checked::after {
    content: ''; position: absolute; top: 4rpx; left: 4rpx;
    width: 20rpx; height: 20rpx; border-radius: 50%; background: #2563EB;
  }
}

/* 自备配置区域 */
.custom-config {
  padding-top: 8rpx; border-top: 2rpx solid #F1F5F9; margin-top: 8rpx;
}

/* 平台选择 */
.platform-tabs { display: flex; gap: 12rpx; }
.platform-tab {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  gap: 6rpx; padding: 16rpx 0; background: #F8FAFC;
  border: 2rpx solid #E2E8F0; border-radius: 12rpx;
  &.active { border-color: #2563EB; background: #EFF6FF; }
}
.platform-icon { font-size: 32rpx; }
.platform-name {
  font-size: 22rpx; color: #64748B;
  .active & { color: #2563EB; font-weight: 600; }
}

/* Key 输入行 */
.key-row {
  display: flex; gap: 12rpx; align-items: center;
  .form-input { flex: 1; }
}
.toggle-eye { font-size: 32rpx; padding: 8rpx; }

/* Picker */
.picker-value {
  height: 80rpx; background: #F8FAFC; border: 2rpx solid #E2E8F0;
  border-radius: 12rpx; padding: 0 24rpx;
  display: flex; align-items: center; justify-content: space-between;
  font-size: 28rpx; color: #1E293B;
}
.picker-arrow { font-size: 20rpx; color: #94A3B8; }

/* 按钮 */
.form-actions { display: flex; gap: 16rpx; margin-top: 8rpx; }
.test-btn {
  flex: 1; height: 80rpx; line-height: 80rpx;
  background: #FFFFFF; color: #2563EB; font-size: 28rpx; font-weight: 600;
  border: 2rpx solid #2563EB; border-radius: 12rpx;
}
.save-btn {
  flex: 1; height: 80rpx; line-height: 80rpx;
  background: #2563EB; color: #FFFFFF; font-size: 28rpx; font-weight: 600;
  border: none; border-radius: 12rpx;
}

/* 测试结果 */
.test-result {
  display: flex; align-items: center; gap: 16rpx;
  padding: 20rpx; border-radius: 12rpx; margin-top: 16rpx;
  &.success { background: #D1FAE5; }
  &.fail { background: #FEE2E2; }
}
.result-icon { font-size: 36rpx; }
.result-info { display: flex; flex-direction: column; gap: 4rpx; }
.result-text { font-size: 28rpx; font-weight: 600; color: #1E293B; }
.result-detail { font-size: 24rpx; color: #64748B; }
.result-detail.error { color: #991B1B; }

/* 添加按钮 */
.add-btn {
  display: flex; align-items: center; justify-content: center; gap: 8rpx;
  padding: 20rpx; border: 2rpx dashed #CBD5E1; border-radius: 12rpx; margin-top: 12rpx;
}
.add-icon { font-size: 32rpx; color: #94A3B8; }
.add-text { font-size: 26rpx; color: #94A3B8; }

/* 退出登录 */
.logout-area { padding: 32rpx 16rpx; }
.logout-btn {
  width: 100%; height: 88rpx; line-height: 88rpx;
  background: #FFFFFF; color: #EF4444; font-size: 30rpx; font-weight: 600;
  border: 2rpx solid #FEE2E2; border-radius: 16rpx;
}
</style>
