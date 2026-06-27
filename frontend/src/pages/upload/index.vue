<template>
  <view class="upload-page">
    <!-- 步骤提示 -->
    <view class="steps">
      <view class="step" :class="{ active: step >= 1 }">
        <view class="step-dot">1</view>
        <text class="step-text">选择照片</text>
      </view>
      <view class="step-line" :class="{ active: step >= 2 }"></view>
      <view class="step" :class="{ active: step >= 2 }">
        <view class="step-dot">2</view>
        <text class="step-text">填写信息</text>
      </view>
      <view class="step-line" :class="{ active: step >= 3 }"></view>
      <view class="step" :class="{ active: step >= 3 }">
        <view class="step-dot">3</view>
        <text class="step-text">上传识别</text>
      </view>
    </view>

    <!-- 图片选择区 -->
    <view class="section">
      <text class="section-title">📷 试卷照片</text>
      <text class="section-desc">支持拍照或从相册选取，最多 5 张</text>

      <view class="image-grid">
        <view
          v-for="(img, index) in imageList"
          :key="index"
          class="image-item"
        >
          <image :src="img" mode="aspectFill" class="preview-img" />
          <view class="delete-btn" @tap="removeImage(index)">×</view>
        </view>
        <view
          v-if="imageList.length < 5"
          class="image-add"
          @tap="chooseImage"
        >
          <text class="add-icon">+</text>
          <text class="add-text">添加照片</text>
        </view>
      </view>
    </view>

    <!-- 考试信息 -->
    <view class="section">
      <text class="section-title">📝 考试信息</text>

      <!-- 学科选择 -->
      <view class="form-item">
        <text class="form-label">学科</text>
        <view class="subject-tabs">
          <view
            v-for="sub in subjects"
            :key="sub.value"
            class="subject-tab"
            :class="{ active: form.subject === sub.value }"
            @tap="form.subject = sub.value"
          >
            <text class="subject-icon">{{ sub.icon }}</text>
            <text class="subject-name">{{ sub.label }}</text>
          </view>
        </view>
      </view>

      <!-- 孩子选择 -->
      <view class="form-item">
        <text class="form-label">孩子</text>
        <picker :range="studentNames" @change="onStudentChange">
          <view class="picker-value">
            <text>{{ currentStudentName }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
      </view>

      <!-- 考试名称 -->
      <view class="form-item">
        <text class="form-label">考试名称</text>
        <view class="exam-name-tags">
          <view
            v-for="name in examNameOptions"
            :key="name"
            class="name-tag"
            :class="{ active: form.exam_name === name }"
            @tap="form.exam_name = name"
          >
            {{ name }}
          </view>
        </view>
        <input
          v-model="form.exam_name"
          placeholder="或手动输入考试名称"
          class="form-input"
        />
      </view>

      <!-- 满分和得分 -->
      <view class="score-row">
        <view class="form-item score-item">
          <text class="form-label">满分</text>
          <input
            v-model="form.total_score"
            type="number"
            placeholder="如 120"
            class="form-input"
          />
        </view>
        <view class="form-item score-item">
          <text class="form-label">得分（选填）</text>
          <input
            v-model="form.actual_score"
            type="number"
            placeholder="如 73"
            class="form-input"
          />
        </view>
      </view>
    </view>

    <!-- 上传按钮 -->
    <view class="bottom-bar safe-area-bottom">
      <button
        class="upload-btn"
        :disabled="!canUpload || uploading"
        :loading="uploading"
        @tap="handleUpload"
      >
        {{ uploading ? '上传识别中...' : '确认上传并识别' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useStudentStore } from '../../store/student'
import { uploadExam, getRecognition } from '../../utils/service'

const studentStore = useStudentStore()

const step = ref(1)
const imageList = ref<string[]>([])
const uploading = ref(false)

const subjects = [
  { value: 'math', label: '数学', icon: '📐' },
  { value: 'politics', label: '道法', icon: '📖' },
  { value: 'history', label: '历史', icon: '🏛️' },
]

const examNameOptions = ['月考', '期中', '期末', '单元测试']

const form = reactive({
  subject: 'math',
  student_id: '',
  exam_name: '月考',
  total_score: '',
  actual_score: '',
})

// 学生相关
const studentNames = computed(() => studentStore.students.map(s => s.name))
const currentStudentName = computed(() => {
  const s = studentStore.students.find(s => s.id === form.student_id)
  return s?.name || '请选择孩子'
})

// 初始化选中第一个学生
if (studentStore.currentStudent) {
  form.student_id = studentStore.currentStudent.id
}

function onStudentChange(e: any) {
  const idx = e.detail.value
  form.student_id = studentStore.students[idx].id
}

// 选择图片
function chooseImage() {
  uni.chooseImage({
    count: 5 - imageList.value.length,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      imageList.value.push(...res.tempFilePaths)
      if (imageList.value.length > 0) step.value = 2
    },
  })
}

function removeImage(index: number) {
  imageList.value.splice(index, 1)
  if (imageList.value.length === 0) step.value = 1
}

// 表单校验
const canUpload = computed(() => {
  return (
    imageList.value.length > 0 &&
    form.subject &&
    form.student_id &&
    form.total_score &&
    Number(form.total_score) > 0
  )
})

// 上传
async function handleUpload() {
  if (!canUpload.value) return
  uploading.value = true
  step.value = 3

  // 显示 loading 提示，告知用户需要等待
  uni.showLoading({ title: '图片上传中...', mask: true })

  try {
    // 先上传图片（速度较快）
    const res = await uploadExam({
      student_id: form.student_id,
      subject: form.subject,
      exam_name: form.exam_name,
      total_score: Number(form.total_score),
      actual_score: form.actual_score ? Number(form.actual_score) : undefined,
      images: imageList.value,
    })

    if (res.code === 0) {
      uni.hideLoading()
      uni.showToast({ title: '识别完成', icon: 'success' })
      // 跳转到识别确认页
      setTimeout(() => {
        uni.navigateTo({
          url: `/pages/exam/confirm?examId=${res.data.exam_id}`,
        })
      }, 500)
    }
  } catch (e: any) {
    uni.hideLoading()
    const msg = e.message || '上传失败'
    if (msg.includes('timeout')) {
      uni.showModal({
        title: '识别超时',
        content: 'AI 识别耗时较长，请稍后在"首页 → 最近诊断"中查看结果。',
        showCancel: false,
      })
    } else {
      uni.showToast({ title: msg, icon: 'none' })
    }
    step.value = 2
  } finally {
    uploading.value = false
  }
}
</script>

<style lang="scss" scoped>
.upload-page {
  min-height: 100vh;
  background: #F8FAFC;
  padding-bottom: 160rpx;
}

/* 步骤条 */
.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx 48rpx;
  background: #FFFFFF;
  margin-bottom: 16rpx;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;

  .step-dot {
    width: 48rpx;
    height: 48rpx;
    border-radius: 50%;
    background: #E2E8F0;
    color: #94A3B8;
    font-size: 24rpx;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .step-text {
    font-size: 22rpx;
    color: #94A3B8;
  }

  &.active {
    .step-dot {
      background: #2563EB;
      color: #FFFFFF;
    }
    .step-text {
      color: #2563EB;
    }
  }
}

.step-line {
  width: 80rpx;
  height: 4rpx;
  background: #E2E8F0;
  margin: 0 16rpx;
  margin-bottom: 28rpx;

  &.active {
    background: #2563EB;
  }
}

/* 区块 */
.section {
  background: #FFFFFF;
  margin: 16rpx 0;
  padding: 32rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
  margin-bottom: 8rpx;
}

.section-desc {
  font-size: 26rpx;
  color: #64748B;
  display: block;
  margin-bottom: 24rpx;
}

/* 图片网格 */
.image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.image-item {
  width: 200rpx;
  height: 200rpx;
  border-radius: 12rpx;
  overflow: hidden;
  position: relative;

  .preview-img {
    width: 100%;
    height: 100%;
  }

  .delete-btn {
    position: absolute;
    top: 4rpx;
    right: 4rpx;
    width: 40rpx;
    height: 40rpx;
    background: rgba(0, 0, 0, 0.5);
    color: #FFFFFF;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28rpx;
  }
}

.image-add {
  width: 200rpx;
  height: 200rpx;
  border: 3rpx dashed #CBD5E1;
  border-radius: 12rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;

  .add-icon {
    font-size: 56rpx;
    color: #94A3B8;
    line-height: 1;
  }

  .add-text {
    font-size: 22rpx;
    color: #94A3B8;
  }
}

/* 表单 */
.form-item {
  margin-bottom: 28rpx;
}

.form-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #1E293B;
  display: block;
  margin-bottom: 16rpx;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

/* 学科选择 */
.subject-tabs {
  display: flex;
  gap: 16rpx;
}

.subject-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 20rpx 0;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 12rpx;
  transition: all 0.2s;

  .subject-icon {
    font-size: 40rpx;
  }

  .subject-name {
    font-size: 26rpx;
    color: #64748B;
  }

  &.active {
    background: #DBEAFE;
    border-color: #2563EB;

    .subject-name {
      color: #2563EB;
      font-weight: 600;
    }
  }
}

/* 考试名称标签 */
.exam-name-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.name-tag {
  padding: 10rpx 24rpx;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 8rpx;
  font-size: 26rpx;
  color: #64748B;

  &.active {
    background: #DBEAFE;
    border-color: #2563EB;
    color: #2563EB;
    font-weight: 600;
  }
}

/* 分数行 */
.score-row {
  display: flex;
  gap: 24rpx;
}

.score-item {
  flex: 1;
}

/* Picker */
.picker-value {
  height: 80rpx;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 12rpx;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 28rpx;
  color: #1E293B;
}

.picker-arrow {
  font-size: 20rpx;
  color: #94A3B8;
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

.upload-btn {
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
</style>
