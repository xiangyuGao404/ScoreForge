/**
 * API 服务层 — 前后端联调版
 *
 * 格式对齐说明：
 * - login: 后端 data = {token, user_id, nickname, user_level}（无嵌套 user 对象）
 * - getStudents: 后端 data = {students: [...]}（需解包）
 * - uploadExam: 后端 multipart/form-data，images 以 File 上传（非 JSON URL）
 * - getWeaknesses: 后端需 student_id 查询参数，data = {weaknesses: [...]}
 * - chat: 后端无此接口，保留 mock
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
  // 后端返回: {code, data: {token, user_id, nickname, user_level}}
  // 前端期望: {code, data: {token, user: {id, nickname, user_level}}}
  const res = await request<{
    token: string
    user_id: string
    nickname: string
    user_level: string
  }>({ url: '/auth/login', method: 'POST', data: { phone, code } })

  return {
    code: res.code,
    message: res.message,
    data: {
      token: res.data.token,
      user: {
        id: res.data.user_id,
        nickname: res.data.nickname,
        user_level: res.data.user_level as 'free' | 'paid',
      },
    },
  }
}

// ===== 学生 =====
export async function getStudents() {
  if (USE_MOCK) {
    await mock.delay(300)
    return { code: 0, data: mock.mockStudents }
  }
  // 后端返回: {code, data: {students: [...]}}
  // 前端期望: {code, data: [...]}
  const res = await request<{ students: any[] }>({ url: '/students' })
  return { code: res.code, data: res.data.students }
}

export async function createStudent(params: {
  name: string
  grade: string
  school?: string
  subjects: string[]
}) {
  if (USE_MOCK) {
    await mock.delay(500)
    return {
      code: 0,
      data: { id: 's-' + Date.now(), ...params, created_at: new Date().toISOString() },
    }
  }
  return request({ url: '/students', method: 'POST', data: params })
}

export async function updateStudent(
  studentId: string,
  params: { name?: string; grade?: string; school?: string; subjects?: string[] }
) {
  if (USE_MOCK) {
    await mock.delay(500)
    return { code: 0, data: { id: studentId, ...params } }
  }
  return request({ url: `/students/${studentId}`, method: 'PUT', data: params })
}

// ===== 试卷上传 =====

// 逐张上传图片到 /exams/upload-image，返回 URL 列表
function uploadSingleImage(filePath: string, token: string): Promise<string> {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: '/api/v1/exams/upload-image',
      filePath,
      name: 'image',
      header: { Authorization: `Bearer ${token}` },
      success: (res: any) => {
        if (res.statusCode === 200) {
          const data = JSON.parse(res.data)
          resolve(data.data?.url || data.data?.filepath || '')
        } else if (res.statusCode === 401) {
          reject(new Error('未登录或登录已过期'))
        } else {
          try {
            const err = JSON.parse(res.data)
            reject(new Error(err.message || '图片上传失败'))
          } catch {
            reject(new Error('图片上传失败'))
          }
        }
      },
      fail: (err: any) => reject(new Error(err.errMsg || '图片上传失败')),
    })
  })
}

export async function uploadExam(params: {
  student_id: string
  subject: string
  exam_name: string
  total_score: number
  actual_score?: number
  images: string[]
}) {
  if (USE_MOCK) {
    await mock.delay(800)
    return {
      code: 0,
      message: 'success',
      data: {
        exam_id: 'exam-001',
        status: 'recognizing',
        message: '试卷已上传，正在识别',
      },
    }
  }

  const token = uni.getStorageSync('token') || ''

  // Step 1: 逐张上传图片，收集 URL
  const imageUrls: string[] = []
  for (let i = 0; i < params.images.length; i++) {
    const url = await uploadSingleImage(params.images[i], token)
    if (url) imageUrls.push(url)
  }

  if (imageUrls.length === 0) {
    throw new Error('图片上传失败，请重试')
  }

  // Step 2: 调用 upload-by-urls（后端异步识别，立即返回 status=recognizing）
  return request({
    url: '/exams/upload-by-urls',
    method: 'POST',
    data: {
      student_id: params.student_id,
      subject: params.subject,
      exam_name: params.exam_name || '',
      total_score: params.total_score,
      actual_score: params.actual_score,
      image_urls: imageUrls,
    },
  })
}

// ===== 识别结果 =====
export async function getRecognition(examId: string) {
  if (USE_MOCK) {
    await mock.delay(2000)
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
  // 后端异步分析，立即返回 status=analyzing
  return request({
    url: `/exams/${examId}/confirm`,
    method: 'POST',
    data: { questions },
  })
}

// ===== 薄弱点分析 =====
export async function getAnalysis(examId: string) {
  if (USE_MOCK) {
    await mock.delay(2500)
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
export async function getWeaknesses(studentId?: string) {
  if (USE_MOCK) {
    await mock.delay(300)
    return { code: 0, data: mock.mockWeaknessList }
  }
  // 后端 GET /weaknesses?student_id=xxx 必须传 student_id
  // 返回: {code, data: {weaknesses: [...]}}，每项不含 student_id
  const sid = studentId || uni.getStorageSync('currentStudentId') || ''
  const res = await request<{ weaknesses: any[] }>({
    url: `/weaknesses?student_id=${sid}`,
  })
  // 注入 student_id（后端不返回该字段，前端页面需要）
  const list = (res.data.weaknesses || []).map(w => ({
    ...w,
    student_id: sid,
  }))
  return { code: res.code, data: list }
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

// ===== 教师对话（后端无此接口，保留 mock） =====
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
        content: `根据孩子最近的学习数据，我建议可以从基础题型开始巩固，每天坚持练习2-3道题，一周后会有明显进步。`,
        created_at: new Date().toISOString(),
      },
    }
  }
  // 后端暂无 chat 接口，降级为 mock
  console.warn('Chat API not implemented in backend, using mock')
  await mock.delay(1000)
  return {
    code: 0,
    data: {
      id: 'msg-' + Date.now(),
      role: 'assistant' as const,
      content: '教师团功能正在开发中，敬请期待！',
      created_at: new Date().toISOString(),
    },
  }
}

export async function getChatHistory(studentId: string, teacherRole: string) {
  if (USE_MOCK) {
    await mock.delay(300)
    return { code: 0, data: mock.mockChatMessages }
  }
  // 后端暂无 chat 接口，降级为空
  return { code: 0, data: [] }
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

// ===== API 配置 =====
export async function getApiConfig() {
  if (USE_MOCK) {
    await mock.delay(300)
    return {
      code: 0,
      data: {
        provider: 'xiaomi',
        api_key_set: false,
        api_base: 'https://token-plan-cn.xiaomimimo.com/v1',
        general_model: 'mimo-v2.5-pro',
        vision_model: 'mimo-v2.5',
      },
    }
  }
  return request({ url: '/settings/api-config' })
}

export async function saveApiConfig(config: {
  provider: string
  api_key: string
  api_base?: string
  general_model: string
  vision_model: string
}) {
  if (USE_MOCK) {
    await mock.delay(500)
    return { code: 0, message: '配置已保存' }
  }
  return request({ url: '/settings/api-config', method: 'PUT', data: config })
}

export async function testApiConfig(params: {
  provider?: string
  api_key?: string
  api_base?: string
  model?: string
  task_type: 'general' | 'vision'
}) {
  if (USE_MOCK) {
    await mock.delay(1500)
    return { code: 0, data: { success: true, model: 'mock-model', response_preview: 'OK', latency_ms: 500 } }
  }
  return request({ url: '/settings/test-api', method: 'POST', data: params })
}
