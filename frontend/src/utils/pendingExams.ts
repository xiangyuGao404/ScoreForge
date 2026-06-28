/**
 * 待审阅试卷管理（localStorage）
 * 上传试卷后记录，确认审阅后删除
 */

interface PendingExam {
  exam_id: string
  subject: string
  exam_name: string
  created_at: string
}

const STORAGE_KEY = 'scoreforge_pending_exams'

export function getPendingExams(): PendingExam[] {
  try {
    const raw = uni.getStorageSync(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function addPendingExam(exam: PendingExam) {
  const list = getPendingExams()
  // 去重
  if (!list.find(e => e.exam_id === exam.exam_id)) {
    list.unshift(exam)
    uni.setStorageSync(STORAGE_KEY, JSON.stringify(list))
  }
}

export function removePendingExam(examId: string) {
  const list = getPendingExams().filter(e => e.exam_id !== examId)
  uni.setStorageSync(STORAGE_KEY, JSON.stringify(list))
}
