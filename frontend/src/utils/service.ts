/**
 * API 服务层
 * 后端就绪前使用 Mock，就绪后切换为真实请求
 */

import { request, uploadFile, USE_MOCK } from './api'
import * as mock from './mock'

// ===== 认证 =====
export async function sendCode(phone: string) {
  if (USE_MOCK) {
    await mock.delay(500)
    return { code: 0, message: '验证码已发送', data: {} }
  }
  return request({ url: '/auth/send-code', method: 'POST', data: { phone } })
}

export async function login(phone: string, code: string) {
  if (USE_MOCK) {
    await mock.delay(800)
    return {
      code: 0,
      message: 'success',
      data: { token: 'mock-token-001', user: mock.mockUser },
    }
  }
  return request({ url: '/auth/login', method: 'POST', data: { phone, code } })
}

// ===== 学生 =====
export async function getStudents() {
  if (USE_MOCK) {
    await mock.delay(300)
    return { code: 0, data: mock.mockStudents }
  }
  return request({ url: '/students' })
}

// ===== 试卷上传 =====
export async function uploadExam(params: {
  student_id: string
  subject: string
  exam_name: string
  total_score: number
  actual_score?: number
  images: string[]
}) {
  if (USE_MOCK) {
    await mock.delay(1500)
    return {
      code: 0,
      message: 'success',
      data: {
        exam_id: 'exam-001',
        status: 'recognizing',
        message: '试卷正在识别中，预计15秒完成',
      },
    }
  }
  // 真实上传：逐张上传图片获取 URL
  const uploadedUrls: string[] = []
  for (const img of params.images) {
    const res = await uploadFile({
      url: '/exams/upload-image',
      filePath: img,
      name: 'image',
      formData: { student_id: params.student_id },
    })
    if (res?.data?.url) uploadedUrls.push(res.data.url)
  }
  return request({
    url: '/exams/upload',
    method: 'POST',
    data: { ...params, images: uploadedUrls },
  })
}

// ===== 识别结果 =====
export async function getRecognition(examId: string) {
  if (USE_MOCK) {
    await mock.delay(2000) // 模拟识别耗时
    return {
      code: 0,
      data: {
        exam_id: examId,
        status: 'recognized',
        questions: mock.mockExamQuestions,
      },
    }
  }
  return request({ url: `/exams/${examId}/recognition` })
}

// ===== 确认识别结果 =====
export async function confirmRecognition(
  examId: string,
  questions: Array<{
    question_no: number
    is_correct: boolean
    score_got: number
    parent_verified: boolean
  }>
) {
  if (USE_MOCK) {
    await mock.delay(1000)
    return {
      code: 0,
      message: '确认成功，正在进行薄弱点分析...',
      data: { exam_id: examId, status: 'analyzing' },
    }
  }
  return request({
    url: `/exams/${examId}/confirm`,
    method: 'POST',
    data: { questions },
  })
}

// ===== 薄弱点分析 =====
export async function getAnalysis(examId: string) {
  if (USE_MOCK) {
    await mock.delay(2500) // 模拟分析耗时
    return {
      code: 0,
      data: {
        exam_id: examId,
        subject: 'math',
        total_score: 120,
        actual_score: 73,
        weaknesses: mock.mockWeaknesses,
      },
    }
  }
  return request({ url: `/exams/${examId}/analysis` })
}

// ===== 薄弱点列表 =====
export async function getWeaknesses() {
  if (USE_MOCK) {
    await mock.delay(300)
    return { code: 0, data: mock.mockWeaknessList }
  }
  return request({ url: '/weaknesses' })
}

// ===== 标记已掌握 =====
export async function masterWeakness(weaknessId: string) {
  if (USE_MOCK) {
    await mock.delay(500)
    return { code: 0, message: '已标记为掌握' }
  }
  return request({ url: `/weaknesses/${weaknessId}/master`, method: 'POST' })
}

// ===== 生成练习题 =====
export async function generatePractice(params: {
  student_id: string
  weakness_id: string
  mode: 'online' | 'pdf'
  question_count?: number
}) {
  if (USE_MOCK) {
    await mock.delay(2000)
    return {
      code: 0,
      data: {
        session_id: 'ps-001',
        mode: params.mode,
        status: 'generating',
        message: '正在生成题目...',
      },
    }
  }
  return request({ url: '/practice/generate', method: 'POST', data: params })
}

// ===== 获取练习题 =====
export async function getPracticeQuestions(sessionId: string) {
  if (USE_MOCK) {
    await mock.delay(500)
    return {
      code: 0,
      data: {
        session_id: sessionId,
        weakness: '函数基础概念',
        questions: mock.mockPracticeQuestions,
      },
    }
  }
  return request({ url: `/practice/${sessionId}/questions` })
}

// ===== 提交做题结果 =====
export async function submitPracticeResult(
  sessionId: string,
  results: Array<{
    question_no: number
    student_answer: string
    is_correct: boolean
  }>
) {
  if (USE_MOCK) {
    await mock.delay(1000)
    const correct = results.filter(r => r.is_correct).length
    return {
      code: 0,
      data: {
        session_id: sessionId,
        correct_rate: correct / results.length,
        assessment_status: 'assessing',
        message: '正在评估掌握程度...',
      },
    }
  }
  return request({
    url: `/practice/${sessionId}/submit`,
    method: 'POST',
    data: { results },
  })
}

// ===== 掌握度评估 =====
export async function getAssessment(sessionId: string) {
  if (USE_MOCK) {
    await mock.delay(2000)
    return { code: 0, data: mock.mockAssessment }
  }
  return request({ url: `/practice/${sessionId}/assessment` })
}

// ===== 教师对话 =====
export async function sendChatMessage(params: {
  student_id: string
  teacher_role: string
  content: string
}) {
  if (USE_MOCK) {
    await mock.delay(1500)
    return {
      code: 0,
      data: {
        id: 'msg-' + Date.now(),
        role: 'assistant' as const,
        content: `根据${params.student_id === 's-001' ? '小明' : '孩子'}最近的学习数据，我建议可以从基础题型开始巩固，每天坚持练习2-3道题，一周后会有明显进步。`,
        created_at: new Date().toISOString(),
      },
    }
  }
  return request({ url: '/chat/send', method: 'POST', data: params })
}

export async function getChatHistory(studentId: string, teacherRole: string) {
  if (USE_MOCK) {
    await mock.delay(300)
    return { code: 0, data: mock.mockChatMessages }
  }
  return request({
    url: `/chat/history?student_id=${studentId}&teacher_role=${teacherRole}`,
  })
}

// ===== PDF =====
export async function generatePdf(sessionId: string) {
  if (USE_MOCK) {
    await mock.delay(2000)
    return {
      code: 0,
      data: { pdf_id: 'pdf-001', status: 'generating', message: 'PDF 正在生成...' },
    }
  }
  return request({ url: '/pdf/generate', method: 'POST', data: { session_id: sessionId } })
}
