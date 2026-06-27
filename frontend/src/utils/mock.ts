/**
 * Mock 数据 - 后端未就绪时使用
 * 数据结构严格遵循技术设计说明书 API 定义
 */

// 模拟延迟
export function delay(ms: number = 800): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// ===== 用户相关 =====
export const mockUser = {
  id: 'u-001',
  phone: '138****1234',
  nickname: '张妈妈',
  user_level: 'paid' as const,
  paid_until: '2026-07-27T00:00:00Z',
}

// ===== 学生相关 =====
export const mockStudents = [
  {
    id: 's-001',
    name: '小明',
    grade: '初二',
    school: 'XX 中学',
    subjects: ['math', 'politics', 'history'],
  },
  {
    id: 's-002',
    name: '小红',
    grade: '初一',
    school: 'XX 中学',
    subjects: ['math'],
  },
]

// ===== 试卷识别结果 =====
export const mockExamQuestions = [
  {
    question_no: 1,
    question_content: '已知函数f(x)=2x+1，求f(3)的值。',
    is_correct: true,
    score_got: 5,
    score_total: 5,
    confidence: 0.95,
    parent_verified: false,
  },
  {
    question_no: 2,
    question_content: '解方程：x² - 5x + 6 = 0',
    is_correct: false,
    score_got: 0,
    score_total: 5,
    confidence: 0.88,
    parent_verified: false,
  },
  {
    question_no: 3,
    question_content: '下列哪个是函数？\nA. x² + y² = 1\nB. y = √x\nC. |y| = x\nD. x = 1',
    is_correct: true,
    score_got: 5,
    score_total: 5,
    confidence: 0.92,
    parent_verified: false,
  },
  {
    question_no: 4,
    question_content: '已知一次函数y=kx+b的图像经过点(1,3)和(0,1)，求k和b的值。',
    is_correct: false,
    score_got: 2,
    score_total: 8,
    confidence: 0.65,
    parent_verified: false,
  },
  {
    question_no: 5,
    question_content: '计算：(2x+3)(x-1)',
    is_correct: false,
    score_got: 0,
    score_total: 6,
    confidence: 0.91,
    parent_verified: false,
  },
  {
    question_no: 6,
    question_content: '如图，在△ABC中，D是BC的中点，求证：AD < (AB+AC)/2',
    is_correct: false,
    score_got: 0,
    score_total: 10,
    confidence: 0.72,
    parent_verified: false,
  },
]

// ===== 薄弱点分析结果 =====
export const mockWeaknesses = [
  {
    weakness_id: 'w-001',
    knowledge_point: '函数基础概念',
    star_rating: 5,
    reason: '函数是中考必考重点，占分约15分。孩子本次函数题全错，但属于基础概念题，掌握后提分空间大。',
    status: 'not_started' as const,
  },
  {
    weakness_id: 'w-002',
    knowledge_point: '一元二次方程计算',
    star_rating: 4,
    reason: '方程计算错误集中在求根公式应用，属于计算粗心而非概念不清，短期练习可明显改善。',
    status: 'not_started' as const,
  },
  {
    weakness_id: 'w-003',
    knowledge_point: '几何证明',
    star_rating: 3,
    reason: '几何证明需要较强的逻辑推理能力，短期提分难度较大，建议放在后期攻克。',
    status: 'not_started' as const,
  },
]

// ===== 练习题 =====
export const mockPracticeQuestions = [
  {
    question_no: 1,
    difficulty: 'basic' as const,
    question_type: 'fill_blank' as const,
    question_content: '已知 f(x) = 3x - 2，求 f(4) 的值。',
    reference_answer: '10',
    solution_detail: '将 x=4 代入 f(x)：\nf(4) = 3×4 - 2 = 12 - 2 = 10',
  },
  {
    question_no: 2,
    difficulty: 'basic' as const,
    question_type: 'choice' as const,
    question_content: '下列哪个是函数？\nA. x² + y² = 1\nB. y = √x\nC. |y| = x\nD. x = 1',
    reference_answer: 'B',
    solution_detail: '函数的定义：对于x的每一个值，y都有唯一确定的值与之对应。\nA中一个x对应两个y值；C中一个x可能对应两个y值；D中x=1是一条竖线。只有B满足函数定义。',
  },
  {
    question_no: 3,
    difficulty: 'medium' as const,
    question_type: 'solve' as const,
    question_content: '已知一次函数 y = kx + b 的图像经过点 A(2, 5) 和点 B(-1, -1)。\n(1) 求这个一次函数的解析式；\n(2) 求该函数图像与x轴的交点坐标。',
    reference_answer: '(1) y = 2x + 1；(2) (-0.5, 0)',
    solution_detail: '(1) 将A(2,5)和B(-1,-1)代入y=kx+b：\n    5 = 2k + b ①\n    -1 = -k + b ②\n    ①-②得：3k = 6，k = 2\n    代入②得：b = -1 + 2 = 1\n    所以 y = 2x + 1\n\n(2) 令y=0：2x + 1 = 0，x = -0.5\n    交点坐标为(-0.5, 0)',
  },
  {
    question_no: 4,
    difficulty: 'medium' as const,
    question_type: 'fill_blank' as const,
    question_content: '反比例函数 y = k/x 的图像经过点(3, 2)，则 k = ____。',
    reference_answer: '6',
    solution_detail: '将点(3,2)代入 y = k/x：\n2 = k/3\nk = 2 × 3 = 6',
  },
  {
    question_no: 5,
    difficulty: 'advanced' as const,
    question_type: 'solve' as const,
    question_content: '已知二次函数 y = ax² + bx + c 的图像开口向上，对称轴为 x = 1，且经过点(-1, 0)。\n(1) 求该二次函数的解析式（设 a = 1）；\n(2) 当 x 取何值时，y < 0？',
    reference_answer: '(1) y = x² - 2x - 3；(2) -1 < x < 3',
    solution_detail: '(1) 对称轴 x = -b/(2a) = 1，a = 1\n    所以 -b/2 = 1，b = -2\n    y = x² - 2x + c\n    过点(-1,0)：0 = 1 + 2 + c，c = -3\n    y = x² - 2x - 3\n\n(2) 令 y < 0：x² - 2x - 3 < 0\n    (x-3)(x+1) < 0\n    所以 -1 < x < 3',
  },
]

// ===== 掌握度评估 =====
export const mockAssessment = {
  session_id: 'ps-001',
  mastery_score: 60,
  trend: 'rising' as const,
  error_pattern: '概念不清 — 函数定义理解有偏差',
  recommendation: 'continue' as const,
  suggested_days: 2,
  suggestion_detail: '孩子对函数的基本定义还需要巩固，特别是"一个x对应唯一y"这个核心概念。建议再练习2天，重点关注函数定义判断题。',
  history: [
    { date: '2026-06-27', correct_rate: 0.6, mastery_score: 60 },
  ],
}

// ===== 教师对话 =====
export const mockChatMessages = [
  {
    id: 'msg-001',
    role: 'user' as const,
    content: '小明最近数学有进步，但几何还是不行，我该怎么安排？',
    created_at: '2026-06-27T10:00:00Z',
  },
  {
    id: 'msg-002',
    role: 'assistant' as const,
    content: '根据小明最近两周的练习数据，几何证明的薄弱点在辅助线构造。建议先从基础辅助线题型开始，每天 2 题，预计 5-7 天可见明显进步。',
    created_at: '2026-06-27T10:00:05Z',
  },
]

// 薄弱点列表（带状态）
export const mockWeaknessList = [
  {
    weakness_id: 'w-001',
    student_id: 's-001',
    knowledge_point: '函数基础概念',
    star_rating: 5,
    reason: '函数是中考必考重点，占分约15分。',
    status: 'practicing' as const,
    mastery_score: 60,
    practice_days: 3,
    recommended_days: 5,
  },
  {
    weakness_id: 'w-002',
    student_id: 's-001',
    knowledge_point: '一元二次方程计算',
    star_rating: 4,
    reason: '方程计算错误集中在求根公式应用。',
    status: 'not_started' as const,
    mastery_score: 0,
    practice_days: 0,
    recommended_days: 3,
  },
  {
    weakness_id: 'w-003',
    student_id: 's-001',
    knowledge_point: '几何证明',
    star_rating: 3,
    reason: '几何证明需要较强的逻辑推理能力。',
    status: 'not_started' as const,
    mastery_score: 0,
    practice_days: 0,
    recommended_days: 7,
  },
  {
    weakness_id: 'w-004',
    student_id: 's-001',
    knowledge_point: '分式运算',
    star_rating: 2,
    reason: '分式运算错误较少，偶尔粗心。',
    status: 'mastered' as const,
    mastery_score: 95,
    practice_days: 4,
    recommended_days: 3,
  },
]
