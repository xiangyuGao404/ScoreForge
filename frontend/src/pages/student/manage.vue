<template>
  <view class="manage-page">
    <!-- 学生列表 -->
    <view class="section">
      <text class="section-title">👶 我的孩子</text>

      <view v-if="students.length === 0" class="empty-state">
        <text class="empty-icon">👶</text>
        <text class="empty-text">还没有添加孩子，点击下方按钮添加</text>
      </view>

      <view
        v-for="s in students"
        :key="s.id"
        class="student-card"
        :class="{ active: s.id === currentStudentId }"
        @tap="switchStudent(s.id)"
      >
        <view class="card-left">
          <text class="student-avatar">{{ s.id === currentStudentId ? '👦' : '👤' }}</text>
          <view class="student-info">
            <text class="student-name">{{ s.name }}</text>
            <text class="student-meta">{{ s.grade }} · {{ s.school || '未填写学校' }}</text>
            <view class="subject-tags">
              <text v-for="sub in s.subjects" :key="sub" class="subject-tag">{{ subjectLabel[sub] || sub }}</text>
            </view>
          </view>
        </view>
        <view class="card-right">
          <text v-if="s.id === currentStudentId" class="current-badge">当前</text>
          <text class="edit-btn" @tap.stop="editStudent(s)">编辑</text>
        </view>
      </view>
    </view>

    <!-- 添加/编辑表单 -->
    <view class="section">
      <text class="section-title">{{ editingId ? '✏️ 编辑孩子' : '➕ 添加孩子' }}</text>

      <view class="form-item">
        <text class="form-label">姓名</text>
        <input v-model="form.name" placeholder="请输入孩子姓名" class="form-input" />
      </view>

      <view class="form-item">
        <text class="form-label">年级</text>
        <view class="grade-tabs">
          <view
            v-for="g in grades"
            :key="g"
            class="grade-tab"
            :class="{ active: form.grade === g }"
            @tap="form.grade = g"
          >
            <text>{{ g }}</text>
          </view>
        </view>
      </view>

      <view class="form-item">
        <text class="form-label">学校（选填）</text>
        <input v-model="form.school" placeholder="请输入学校名称" class="form-input" />
      </view>

      <view class="form-item">
        <text class="form-label">关注学科</text>
        <view class="subject-checks">
          <view
            v-for="sub in subjectOptions"
            :key="sub.value"
            class="subject-check"
            :class="{ active: form.subjects.includes(sub.value) }"
            @tap="toggleSubject(sub.value)"
          >
            <text class="check-icon">{{ form.subjects.includes(sub.value) ? '☑' : '☐' }}</text>
            <text class="check-label">{{ sub.label }}</text>
          </view>
        </view>
      </view>

      <view class="form-actions">
        <button v-if="editingId" class="cancel-btn" @tap="cancelEdit">取消</button>
        <button class="submit-btn" :disabled="!canSubmit" :loading="submitting" @tap="handleSubmit">
          {{ editingId ? '保存修改' : '添加孩子' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useStudentStore } from '../../store/student'
import { getStudents, createStudent, updateStudent } from '../../utils/service'

const studentStore = useStudentStore()
const students = computed(() => studentStore.students)
const currentStudentId = computed(() => studentStore.currentStudentId)

const grades = ['初一', '初二', '初三']
const subjectOptions = [
  { value: 'math', label: '数学' },
  { value: 'politics', label: '道法' },
  { value: 'history', label: '历史' },
]
const subjectLabel: Record<string, string> = {
  math: '数学',
  politics: '道法',
  history: '历史',
}

const editingId = ref('')
const submitting = ref(false)
const form = reactive({
  name: '',
  grade: '初二',
  school: '',
  subjects: ['math'] as string[],
})

const canSubmit = computed(() => form.name.trim() && form.grade && form.subjects.length > 0)

onMounted(async () => {
  await loadStudents()
})

async function loadStudents() {
  const res = await getStudents()
  if (res.code === 0) {
    studentStore.setStudents(res.data)
  }
}

function toggleSubject(val: string) {
  const idx = form.subjects.indexOf(val)
  if (idx >= 0) {
    form.subjects.splice(idx, 1)
  } else {
    form.subjects.push(val)
  }
}

function editStudent(s: any) {
  editingId.value = s.id
  form.name = s.name
  form.grade = s.grade
  form.school = s.school || ''
  form.subjects = [...(s.subjects || ['math'])]
}

function cancelEdit() {
  editingId.value = ''
  resetForm()
}

function resetForm() {
  form.name = ''
  form.grade = '初二'
  form.school = ''
  form.subjects = ['math']
}

async function handleSubmit() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    if (editingId.value) {
      const res = await updateStudent(editingId.value, {
        name: form.name.trim(),
        grade: form.grade,
        school: form.school.trim() || undefined,
        subjects: form.subjects,
      })
      if (res.code === 0) {
        uni.showToast({ title: '修改成功', icon: 'success' })
        editingId.value = ''
        resetForm()
        await loadStudents()
      }
    } else {
      const res = await createStudent({
        name: form.name.trim(),
        grade: form.grade,
        school: form.school.trim() || undefined,
        subjects: form.subjects,
      })
      if (res.code === 0) {
        uni.showToast({ title: '添加成功', icon: 'success' })
        resetForm()
        await loadStudents()
      }
    }
  } catch (e: any) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function switchStudent(id: string) {
  studentStore.switchStudent(id)
  uni.showToast({ title: '已切换', icon: 'success' })
}
</script>

<style lang="scss" scoped>
.manage-page {
  min-height: 100vh;
  background: #F8FAFC;
  padding-bottom: 32rpx;
}

.section {
  background: #FFFFFF;
  margin: 16rpx;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #1E293B;
  display: block;
  margin-bottom: 20rpx;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0;
  gap: 12rpx;
}

.empty-icon { font-size: 56rpx; }
.empty-text { font-size: 26rpx; color: #94A3B8; }

/* 学生卡片 */
.student-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx;
  border: 2rpx solid #E2E8F0;
  border-radius: 12rpx;
  margin-bottom: 12rpx;

  &.active {
    border-color: #2563EB;
    background: #EFF6FF;
  }
}

.card-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.student-avatar {
  font-size: 40rpx;
}

.student-info {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.student-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #1E293B;
}

.student-meta {
  font-size: 24rpx;
  color: #64748B;
}

.subject-tags {
  display: flex;
  gap: 8rpx;
  margin-top: 4rpx;
}

.subject-tag {
  font-size: 20rpx;
  padding: 2rpx 10rpx;
  background: #DBEAFE;
  color: #2563EB;
  border-radius: 4rpx;
}

.card-right {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.current-badge {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  background: #2563EB;
  color: #FFFFFF;
  border-radius: 6rpx;
}

.edit-btn {
  font-size: 24rpx;
  color: #2563EB;
  padding: 8rpx;
}

/* 表单 */
.form-item {
  margin-bottom: 24rpx;
}

.form-label {
  font-size: 26rpx;
  font-weight: 600;
  color: #1E293B;
  display: block;
  margin-bottom: 12rpx;
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

/* 年级选择 */
.grade-tabs {
  display: flex;
  gap: 16rpx;
}

.grade-tab {
  flex: 1;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 10rpx;
  font-size: 28rpx;
  color: #64748B;

  &.active {
    background: #DBEAFE;
    border-color: #2563EB;
    color: #2563EB;
    font-weight: 600;
  }
}

/* 学科选择 */
.subject-checks {
  display: flex;
  gap: 16rpx;
}

.subject-check {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  height: 72rpx;
  background: #F8FAFC;
  border: 2rpx solid #E2E8F0;
  border-radius: 10rpx;

  &.active {
    background: #DBEAFE;
    border-color: #2563EB;
  }
}

.check-icon {
  font-size: 28rpx;
  color: #2563EB;
}

.check-label {
  font-size: 26rpx;
  color: #1E293B;

  .active & {
    color: #2563EB;
    font-weight: 600;
  }
}

/* 按钮 */
.form-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 8rpx;
}

.cancel-btn {
  flex: 1;
  height: 80rpx;
  line-height: 80rpx;
  background: #FFFFFF;
  color: #64748B;
  font-size: 28rpx;
  font-weight: 600;
  border: 2rpx solid #E2E8F0;
  border-radius: 12rpx;
}

.submit-btn {
  flex: 1;
  height: 80rpx;
  line-height: 80rpx;
  background: #2563EB;
  color: #FFFFFF;
  font-size: 28rpx;
  font-weight: 600;
  border: none;
  border-radius: 12rpx;

  &[disabled] {
    background: #CBD5E1;
    color: #94A3B8;
  }
}
</style>
