<template>
  <view class="login-page">
    <!-- Logo 区域 -->
    <view class="logo-area">
      <view class="logo-icon">📐</view>
      <text class="logo-title">ScoreForge</text>
      <text class="logo-subtitle">AI 学情诊断 · 精准提分</text>
    </view>

    <!-- 登录表单 -->
    <view class="form-area">
      <view class="input-group">
        <text class="input-label">手机号</text>
        <input
          v-model="phone"
          type="number"
          maxlength="11"
          placeholder="请输入手机号"
          class="input-field"
        />
      </view>

      <view class="input-group">
        <text class="input-label">验证码</text>
        <view class="code-row">
          <input
            v-model="code"
            type="number"
            maxlength="6"
            placeholder="请输入验证码"
            class="input-field code-input"
          />
          <button
            class="send-code-btn"
            :disabled="countdown > 0"
            @tap="handleSendCode"
          >
            {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </button>
        </view>
      </view>

      <button class="login-btn" :loading="loading" @tap="handleLogin">
        登录 / 注册
      </button>

      <view class="divider">
        <view class="divider-line"></view>
        <text class="divider-text">或</text>
        <view class="divider-line"></view>
      </view>

      <button class="wechat-btn" @tap="handleWechatLogin">
        微信一键登录
      </button>
    </view>

    <!-- 协议 -->
    <view class="agreement">
      <text class="agreement-text">
        登录即表示同意
        <text class="link">《用户协议》</text>
        和
        <text class="link">《隐私政策》</text>
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '../../store/user'
import { useStudentStore } from '../../store/student'
import { sendCode, login, getStudents } from '../../utils/service'

const phone = ref('')
const code = ref('')
const loading = ref(false)
const countdown = ref(0)
let timer: any = null

function handleSendCode() {
  if (!phone.value || phone.value.length !== 11) {
    uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
    return
  }
  sendCode(phone.value).then(() => {
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    countdown.value = 60
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  })
}

async function handleLogin() {
  if (!phone.value || phone.value.length !== 11) {
    uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
    return
  }
  if (!code.value || code.value.length < 4) {
    uni.showToast({ title: '请输入验证码', icon: 'none' })
    return
  }
  loading.value = true
  try {
    const res = await login(phone.value, code.value)
    if (res.code === 0) {
      const userStore = useUserStore()
      userStore.setLogin({
        token: res.data.token,
        nickname: res.data.user.nickname,
        user_level: res.data.user.user_level,
      })
      // 加载学生数据
      const studentRes = await getStudents()
      if (studentRes.code === 0) {
        useStudentStore().setStudents(studentRes.data)
      }
      uni.switchTab({ url: '/pages/home/index' })
    }
  } catch (e: any) {
    uni.showToast({ title: e.message || '登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function handleWechatLogin() {
  uni.showToast({ title: '微信登录开发中', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: #FFFFFF;
  padding: 0 32rpx;
  display: flex;
  flex-direction: column;
}

.logo-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 160rpx;
  margin-bottom: 80rpx;
}

.logo-icon {
  font-size: 96rpx;
  margin-bottom: 16rpx;
}

.logo-title {
  font-size: 48rpx;
  font-weight: 700;
  color: #2563EB;
  margin-bottom: 8rpx;
}

.logo-subtitle {
  font-size: 26rpx;
  color: #64748B;
}

.form-area {
  flex: 1;
}

.input-group {
  margin-bottom: 32rpx;
}

.input-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 12rpx;
  display: block;
}

.input-field {
  width: 100%;
  height: 88rpx;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 16rpx;
  padding: 0 24rpx;
  font-size: 30rpx;
  box-sizing: border-box;
}

.code-row {
  display: flex;
  gap: 16rpx;
}

.code-input {
  flex: 1;
}

.send-code-btn {
  width: 220rpx;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  background: #DBEAFE;
  color: #2563EB;
  font-size: 26rpx;
  font-weight: 600;
  border-radius: 16rpx;
  border: none;
  padding: 0;

  &[disabled] {
    background: #F1F5F9;
    color: #94A3B8;
  }
}

.login-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: #2563EB;
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 600;
  border-radius: 16rpx;
  border: none;
  margin-top: 16rpx;
}

.divider {
  display: flex;
  align-items: center;
  margin: 40rpx 0;
}

.divider-line {
  flex: 1;
  height: 2rpx;
  background: #E2E8F0;
}

.divider-text {
  padding: 0 24rpx;
  font-size: 26rpx;
  color: #94A3B8;
}

.wechat-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: #07C160;
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 600;
  border-radius: 16rpx;
  border: none;
}

.agreement {
  padding: 32rpx 0;
  text-align: center;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
}

.agreement-text {
  font-size: 24rpx;
  color: #94A3B8;
}

.link {
  color: #2563EB;
}
</style>
