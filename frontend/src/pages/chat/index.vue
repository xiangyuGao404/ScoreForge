<template>
  <view class="chat-page">
    <!-- 角色切换 -->
    <view class="role-tabs">
      <view
        v-for="role in roles"
        :key="role.value"
        class="role-tab"
        :class="{ active: currentRole === role.value }"
        @tap="switchRole(role.value)"
      >
        <text class="role-icon">{{ role.icon }}</text>
        <text class="role-name">{{ role.label }}</text>
      </view>
    </view>

    <!-- 消息列表 -->
    <scroll-view
      class="message-list"
      scroll-y
      :scroll-into-view="scrollTarget"
      :scroll-with-animation="true"
    >
      <!-- 欢迎消息 -->
      <view class="welcome-msg">
        <view class="welcome-avatar">{{ currentRoleInfo.icon }}</view>
        <view class="welcome-bubble">
          <text class="welcome-name">{{ currentRoleInfo.label }}</text>
          <text class="welcome-text">你好！我是{{ currentRoleInfo.label }}，有什么学习上的问题可以问我~</text>
        </view>
      </view>

      <view
        v-for="msg in messages"
        :key="msg.id"
        :id="'msg-' + msg.id"
        class="message-item"
        :class="msg.role"
      >
        <view v-if="msg.role === 'assistant'" class="msg-avatar">
          {{ currentRoleInfo.icon }}
        </view>
        <view class="msg-bubble" :class="msg.role">
          <text class="msg-content">{{ msg.content }}</text>
          <text class="msg-time">{{ formatTime(msg.created_at) }}</text>
        </view>
      </view>

      <!-- 加载中 -->
      <view v-if="sending" class="message-item assistant">
        <view class="msg-avatar">{{ currentRoleInfo.icon }}</view>
        <view class="msg-bubble assistant loading-bubble">
          <view class="typing-dots">
            <view class="dot"></view>
            <view class="dot"></view>
            <view class="dot"></view>
          </view>
        </view>
      </view>

      <view id="msg-bottom" style="height: 20rpx;"></view>
    </scroll-view>

    <!-- 输入区域 -->
    <view class="input-area safe-area-bottom">
      <input
        v-model="inputText"
        class="msg-input"
        placeholder="输入问题..."
        :disabled="sending"
        @confirm="sendMessage"
      />
      <button
        class="send-btn"
        :disabled="!inputText.trim() || sending"
        @tap="sendMessage"
      >
        发送
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { sendChatMessage, getChatHistory } from '../../utils/service'
import { useStudentStore } from '../../store/student'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

const roles = [
  { value: 'math', label: '数学老师', icon: '📐' },
  { value: 'politics', label: '道法老师', icon: '📖' },
  { value: 'history', label: '历史老师', icon: '🏛️' },
  { value: 'homeroom', label: '班主任', icon: '👩‍🏫' },
]

const studentStore = useStudentStore()
const currentRole = ref('math')
const messages = ref<Message[]>([])
const inputText = ref('')
const sending = ref(false)
const scrollTarget = ref('')

const currentRoleInfo = computed(() => roles.find(r => r.value === currentRole.value)!)
const currentStudentId = computed(() => studentStore.currentStudent?.id || '')

async function switchRole(role: string) {
  currentRole.value = role
  messages.value = []
  if (!currentStudentId.value) return
  const res = await getChatHistory(currentStudentId.value, role)
  if (res.code === 0) {
    messages.value = res.data
  }
  scrollToBottom()
}

function formatTime(t: string) {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

function scrollToBottom() {
  nextTick(() => {
    scrollTarget.value = 'msg-bottom'
  })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  // 添加用户消息
  const userMsg: Message = {
    id: 'msg-' + Date.now(),
    role: 'user',
    content: text,
    created_at: new Date().toISOString(),
  }
  messages.value.push(userMsg)
  inputText.value = ''
  scrollToBottom()

  sending.value = true
  try {
    const res = await sendChatMessage({
      student_id: currentStudentId.value,
      teacher_role: currentRole.value,
      content: text,
    })
    if (res.code === 0) {
      messages.value.push({
        id: res.data.id,
        role: 'assistant',
        content: res.data.content,
        created_at: res.data.created_at,
      })
    }
  } catch (e: any) {
    uni.showToast({ title: e.message || '发送失败', icon: 'none' })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

// 初始化加载
onMounted(() => {
  switchRole('math')
})
</script>

<style lang="scss" scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #F8FAFC;
}

/* 角色标签 */
.role-tabs {
  display: flex;
  background: #FFFFFF;
  padding: 16rpx;
  gap: 12rpx;
  flex-shrink: 0;
}

.role-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  padding: 12rpx 0;
  border-radius: 12rpx;
  background: #F8FAFC;

  &.active {
    background: #DBEAFE;
  }
}

.role-icon {
  font-size: 32rpx;
}

.role-name {
  font-size: 22rpx;
  color: #64748B;

  .active & {
    color: #2563EB;
    font-weight: 600;
  }
}

/* 消息列表 */
.message-list {
  flex: 1;
  padding: 16rpx;
}

.welcome-msg {
  display: flex;
  gap: 12rpx;
  margin-bottom: 24rpx;
}

.welcome-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: #DBEAFE;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  flex-shrink: 0;
}

.welcome-bubble {
  background: #FFFFFF;
  border-radius: 0 20rpx 20rpx 20rpx;
  padding: 20rpx 24rpx;
  max-width: 70%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.welcome-name {
  font-size: 24rpx;
  font-weight: 600;
  color: #2563EB;
  display: block;
  margin-bottom: 8rpx;
}

.welcome-text {
  font-size: 28rpx;
  color: #1E293B;
  line-height: 1.5;
}

/* 消息项 */
.message-item {
  display: flex;
  gap: 12rpx;
  margin-bottom: 24rpx;

  &.user {
    flex-direction: row-reverse;
  }
}

.msg-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: #DBEAFE;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  flex-shrink: 0;
}

.msg-bubble {
  max-width: 70%;
  padding: 20rpx 24rpx;
  border-radius: 20rpx;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);

  &.assistant {
    background: #FFFFFF;
    border-radius: 0 20rpx 20rpx 20rpx;
  }

  &.user {
    background: #2563EB;
    border-radius: 20rpx 0 20rpx 20rpx;
  }
}

.msg-content {
  font-size: 28rpx;
  line-height: 1.6;
  display: block;

  .assistant & { color: #1E293B; }
  .user & { color: #FFFFFF; }
}

.msg-time {
  font-size: 20rpx;
  margin-top: 8rpx;
  display: block;

  .assistant & { color: #94A3B8; }
  .user & { color: rgba(255, 255, 255, 0.7); }
}

/* 打字动画 */
.loading-bubble {
  padding: 24rpx 32rpx;
}

.typing-dots {
  display: flex;
  gap: 8rpx;
}

.dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #94A3B8;
  animation: typing 1.4s infinite;

  &:nth-child(2) { animation-delay: 0.2s; }
  &:nth-child(3) { animation-delay: 0.4s; }
}

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-4rpx); }
}

/* 输入区域 */
.input-area {
  display: flex;
  gap: 12rpx;
  background: #FFFFFF;
  padding: 16rpx;
  border-top: 2rpx solid #E2E8F0;
  flex-shrink: 0;
}

.msg-input {
  flex: 1;
  height: 72rpx;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 36rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
}

.send-btn {
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 32rpx;
  background: #2563EB;
  color: #FFFFFF;
  font-size: 28rpx;
  font-weight: 600;
  border-radius: 36rpx;
  border: none;

  &[disabled] {
    background: #CBD5E1;
  }
}
</style>
