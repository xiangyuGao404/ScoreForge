# AI 异步化改造 + opencode 配置切换 — 前后端协同文档

**目标**：解决前端 AI 请求超时问题，所有 AI 调用改为"提交即返回 + 轮询结果"；同时切换 AI 平台到 opencode go 套餐。

---

## 一、背景与问题

### 当前问题

后端 5 个端点同步阻塞调用 AI，AI 执行需 1-3 分钟，前端默认超时 30 秒 → **大部分 AI 请求超时失败**。

| 端点 | AI 调用 | 当前模式 | 前端超时 |
|------|---------|---------|---------|
| `POST /exams/upload` | OCR 图片识别 | 同步阻塞 | 5 分钟 |
| `POST /exams/{id}/confirm` | 薄弱点分析 | 同步阻塞（前端 fire-and-forget） | 3 分钟 |
| `POST /practice/generate` | AI 出题 | 同步阻塞 | 30 秒 |
| `GET /practice/{id}/assessment` | AI 掌握度评估 | 同步阻塞 | 30 秒 |

**最严重的问题**：confirm 页用了 fire-and-forget（发完请求不等结果就跳转），但 analysis 页没有轮询机制 → **提交后永远拿不到分析结果**。

### 目标架构

```
前端提交 → 后端立即返回 {status: "处理中"} + 后台异步跑 AI
                ↓
前端跳到目标页 → 轮询状态接口 → status 变为完成态 → 展示结果
```

---

## 二、整体方案

### 核心原则

1. **所有 AI 调用改为后台异步执行**，HTTP 请求立即返回
2. **用状态字段标记处理进度**，前端轮询状态
3. **识别试卷特殊保留审查入口**：上传后带 exam_id 跳确认页，确认页轮询

### 状态机扩展

#### Exam 状态（已有，需启用 ANALYZING）

```
UPLOADING → RECOGNIZING → RECOGNIZED → CONFIRMED → ANALYZING → ANALYZED
                         (OCR后台跑)              (分析后台跑)
```

- `RECOGNIZING`：OCR 后台识别中（upload 返回此状态）
- `ANALYZING`：薄弱点分析后台进行中（confirm 返回此状态）—— 当前已定义但未使用，需启用

#### PracticeSession 状态（需新增 status 字段）

当前 `PracticeSession` **没有 status 字段**，需新增：

```python
class PracticeStatus(str, PyEnum):
    GENERATING = "generating"      # AI 出题中
    READY = "ready"                # 题目就绪，可答题
    ASSESSING = "assessing"        # AI 评估中
    ASSESSED = "assessed"          # 评估完成
```

### 后台任务技术选型

**V1.0 推荐：FastAPI BackgroundTasks**（改动最小，无需额外进程）

```python
from fastapi import BackgroundTasks

@router.post("/upload")
async def upload_exam(..., background_tasks: BackgroundTasks):
    exam = Exam(status=ExamStatus.RECOGNIZING, ...)
    db.add(exam); await db.flush()
    background_tasks.add_task(run_ocr_background, exam.id, image_urls)
    return {"exam_id": str(exam.id), "status": "recognizing"}  # 立即返回
```

**注意**：开发模式 `--reload` 时文件改动会重启进程，后台任务会丢失（生产环境无此问题）。如需更高可靠性，V1.1 可切换到已配置的 Celery（当前是死代码）。

---

## 三、后端改造任务

### B-1：PracticeSession 模型新增 status 字段

**文件**：`backend/app/models/practice.py`

```python
class PracticeStatus(str, PyEnum):
    GENERATING = "generating"
    READY = "ready"
    ASSESSING = "assessing"
    ASSESSED = "assessed"

class PracticeSession(...):
    # 新增字段
    status: Mapped[PracticeStatus] = mapped_column(
        Enum(PracticeStatus), default=PracticeStatus.GENERATING
    )
```

生成 Alembic 迁移：`alembic revision --autogenerate -m "add practice status"`

### B-2：upload 端点异步化（OCR）

**文件**：`backend/app/api/v1/exams.py` 第 59-175 行（upload）和 224-323 行（upload-by-urls）

**当前**：第 134 行 `await ocr_service.recognize_exam(image_urls)` 同步阻塞

**改为**：
```python
@router.post("/upload-by-urls", response_model=APIResponse[ExamUploadResponse])
async def upload_exam_by_urls(
    req: ExamUploadByUrlsRequest,
    background_tasks: BackgroundTasks,        # 新增
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    # 校验 + 创建 exam，status=RECOGNIZING
    exam = Exam(status=ExamStatus.RECOGNIZING, ...)
    db.add(exam); await db.flush()
    await db.commit()  # 必须提交，后台任务才能读到

    # 后台执行 OCR，不阻塞响应
    background_tasks.add_task(
        run_ocr_background, str(exam.id), image_urls, subject, str(current_user.id)
    )

    # 立即返回
    return APIResponse(data=ExamUploadResponse(
        exam_id=str(exam.id),
        status="recognizing",
        message="试卷已接收，正在识别",
    ))
```

**新增后台任务函数**（可在 `exams.py` 或 `tasks/exam_tasks.py`）：
```python
async def run_ocr_background(exam_id: str, image_urls: list, subject: str, user_id: str):
    """后台执行 OCR，完成后更新 exam 状态和题目。"""
    from app.core.database import async_session_factory
    async with async_session_factory() as db:
        try:
            result = await ocr_service.recognize_exam(image_urls, subject=subject)
            # 保存 ExamQuestion，更新 exam.status = RECOGNIZED
            ...
            await db.commit()
        except Exception as e:
            logger.error(f"OCR failed for exam {exam_id}: {e}")
            exam = await db.get(Exam, uuid.UUID(exam_id))
            exam.status = ExamStatus.UPLOADING  # 失败回退
            await db.commit()
```

### B-3：confirm 端点异步化（薄弱点分析）

**文件**：`backend/app/api/v1/exams.py` 第 349-458 行

**当前**：第 392 行 `await ai_service.analyze_weaknesses(...)` 同步阻塞

**改为**：
```python
@router.post("/{exam_id}/confirm")
async def confirm_recognition(..., background_tasks: BackgroundTasks):
    # 保存确认数据，status = ANALYZING（启用未用状态）
    exam.status = ExamStatus.ANALYZING
    # 保存确认的题目...
    await db.commit()

    # 后台执行分析
    background_tasks.add_task(
        run_analysis_background, str(exam_id), str(current_user.id)
    )

    return APIResponse(data={
        "exam_id": str(exam_id),
        "status": "analyzing",   # 立即返回
        "message": "已确认，AI 正在分析薄弱点",
    })
```

**后台任务**：调 `ai_service.analyze_weaknesses`，成功后设 `status=ANALYZED` 并保存 weaknesses，失败回退 `CONFIRMED`。

### B-4：analysis 端点支持"处理中"状态

**文件**：`backend/app/api/v1/exams.py` 第 461-502 行

**当前**：status 必须是 `ANALYZED` 或 `CONFIRMED`，否则报错

**改为**：支持返回 `ANALYZING` 状态，让前端轮询：

```python
@router.get("/{exam_id}/analysis")
async def get_analysis(exam_id, ...):
    exam = ...  # 查 exam
    if exam.status == ExamStatus.ANALYZING:
        # 分析中，返回空薄弱点 + analyzing 状态
        return APIResponse(data={
            "exam_id": str(exam_id),
            "status": "analyzing",
            "subject": exam.subject,
            "total_score": exam.total_score,
            "actual_score": exam.actual_score,
            "weaknesses": [],   # 空
            "message": "AI 正在分析中",
        })
    if exam.status == ExamStatus.ANALYZED:
        # 返回完整薄弱点
        return APIResponse(data={..., "status": "analyzed", "weaknesses": [...]})
    # 其他状态报错
```

### B-5：practice/generate 端点异步化（出题）

**文件**：`backend/app/api/v1/practice.py` 第 36-134 行

**当前**：第 88 行 `await ai_service.generate_questions(...)` 同步阻塞

**改为**：
```python
@router.post("/generate")
async def generate_practice(..., background_tasks: BackgroundTasks):
    # 校验 + 创建 session，status=GENERATING
    session = PracticeSession(status=PracticeStatus.GENERATING, ...)
    db.add(session); await db.commit()

    background_tasks.add_task(
        run_generate_background, str(session.id), kp.name, kp.subject,
        student.grade.value, req.question_count, str(current_user.id)
    )

    return APIResponse(data=PracticeGenerateResponse(
        session_id=str(session.id),
        mode=mode.value,
        status="generating",   # 立即返回
        message="正在生成题目",
    ))
```

**后台任务**：调 `ai_service.generate_questions`，成功后创建 PracticeQuestion 记录，设 `status=READY`。

### B-6：practice/questions 端点支持"生成中"状态

**文件**：`backend/app/api/v1/practice.py` 第 137-172 行

**改为**：session.status == GENERATING 时返回空题目 + generating 状态：
```python
if session.status == PracticeStatus.GENERATING:
    return APIResponse(data={
        "session_id": str(session.id),
        "weakness": kp.name,
        "status": "generating",
        "questions": [],   # 空
    })
if session.status == PracticeStatus.READY:
    # 返回完整题目
    return APIResponse(data={..., "status": "ready", "questions": [...]})
```

### B-7：submit + assessment 异步化（评估）

**文件**：`backend/app/api/v1/practice.py`

**submit 端点**（第 175-221 行）：保存答案 + 设 `session.status = ASSESSING` + 启动后台评估任务 + 立即返回：
```python
@router.post("/{session_id}/submit")
async def submit_practice(..., background_tasks: BackgroundTasks):
    # 保存答案，计算 correct_rate
    session.status = PracticeStatus.ASSESSING
    await db.commit()

    background_tasks.add_task(run_assessment_background, str(session.id), str(current_user.id))

    return APIResponse(data={
        "session_id": str(session_id),
        "status": "assessing",   # 立即返回
        "correct_rate": session.correct_rate,
    })
```

**assessment 端点**（第 224-329 行）：支持返回 assessing 中间态：
```python
if session.status == PracticeStatus.ASSESSING:
    return APIResponse(data={
        "session_id": str(session.id),
        "status": "assessing",
        "mastery_score": None,
        "message": "AI 正在评估中",
    })
if session.status == PracticeStatus.ASSESSED:
    # 返回完整评估结果
    return APIResponse(data={..., "status": "assessed", "mastery_score": ..., ...})
```

**后台任务**：调 `ai_service.assess_mastery`，成功后保存评估结果 + 设 `status=ASSESSED`。

### B-8：切换 AI 配置到 opencode go 套餐

**文件**：`backend/app/core/config.py` + `backend/.env`

用户的小米 TokenPlan 已到期，切换到 opencode go 套餐（OpenAI 兼容接口）。

**.env 配置**：
```bash
# AI Provider（复用 openai provider，base_url 指向 opencode）
AI_PROVIDER=openai

# opencode go 套餐（OpenAI 兼容）
OPENAI_API_KEY=<填入 opencode 的 key>
OPENAI_API_BASE=<填入 opencode 的 API 地址，如 https://api.opencode.ai/v1>
OPENAI_GENERAL_MODEL=deepseek-v4-flash   # 分析/出题/评估
OPENAI_VISION_MODEL=mimo-v2.5            # 图片识别
```

**.env.example 同步更新**（只放占位符，不写真实 key）：
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_API_BASE=https://api.opencode.ai/v1   # 需确认实际地址
OPENAI_GENERAL_MODEL=deepseek-v4-flash
OPENAI_VISION_MODEL=mimo-v2.5
```

**验证**：`ai_service._get_client("general")` 应返回 deepseek-v4-flash，`_get_client("vision")` 应返回 mimo-v2.5。代码逻辑已支持 general/vision 分离（之前重构已完成），只需改配置值。

**需用户确认**：opencode go 套餐的实际 API base_url（文档中留了占位符，请填入正确地址）。

---

## 四、前端改造任务

### F-1：新增统一轮询工具函数

**文件**：新建 `frontend/src/utils/poll.ts`

```ts
/**
 * 轮询直到条件满足或超时
 * @param fn 每次轮询执行的异步函数，返回数据
 * @param check 判断是否完成的函数，返回 true 表示停止轮询
 * @param interval 轮询间隔（毫秒），默认 2500
 * @param maxAttempts 最大轮询次数，默认 60（约 2.5 分钟）
 */
export function poll<T>(
  fn: () => Promise<T>,
  check: (data: T) => boolean,
  interval = 2500,
  maxAttempts = 60
): Promise<T> {
  return new Promise((resolve, reject) => {
    let attempts = 0
    const timer = setInterval(async () => {
      attempts++
      try {
        const data = await fn()
        if (check(data)) {
          clearInterval(timer)
          resolve(data)
        } else if (attempts >= maxAttempts) {
          clearInterval(timer)
          reject(new Error('处理超时，请稍后重试'))
        }
      } catch (e) {
        clearInterval(timer)
        reject(e)
      }
    }, interval)
  })
}
```

### F-2：upload 页 — 提交后立即跳确认页

**文件**：`frontend/src/pages/upload/index.vue` 第 216-236 行

**当前**：`await uploadExam()` 等待完整结果（5 分钟）

**改为**：提交后立即跳转，不等 OCR 完成：
```ts
async function handleUpload() {
  // ... 校验
  uploading.value = true
  try {
    const res = await uploadExam(form)  // 现在立即返回 status=recognizing
    if (res.code === 0) {
      uni.showToast({ title: '试卷已上传，正在识别', icon: 'none' })
      // 立即跳转，带 examId（确认页会轮询）
      setTimeout(() => {
        uni.navigateTo({ url: `/pages/exam/confirm?examId=${res.data.exam_id}` })
      }, 500)
    }
  } catch (e) {
    uni.showToast({ title: e.message || '上传失败', icon: 'none' })
  } finally {
    uploading.value = false
  }
}
```

**service.ts 的 uploadExam**：超时从 5 分钟改回默认 30 秒（因为现在立即返回了）。

### F-3：confirm 页 — 轮询识别结果（审查入口）

**文件**：`frontend/src/pages/exam/confirm.vue` 第 117-158 行

**这是保留审查入口的关键页面**。用户上传后跳到这里，页面轮询直到识别完成，然后展示题目供家长审查。

**改为**：
```ts
import { poll } from '../../utils/poll'

async function loadRecognition() {
  loading.value = true
  try {
    // 轮询直到 status === 'recognized'
    const res = await poll(
      () => getRecognition(examId.value),
      (data) => data.data.status === 'recognized',
      2500, 60   // 每 2.5 秒查一次，最多 2.5 分钟
    )
    if (res.code === 0) {
      questions.value = res.data.questions
    }
  } catch (e) {
    uni.showToast({ title: '识别超时，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}
```

**loading 文案**：显示 "AI 正在识别试卷... 预计 15-30 秒"，识别完成后自动展示题目。家长在此页面逐题审查对错。

### F-4：confirm 提交 — 改为正常 await + 跳转

**文件**：`frontend/src/pages/exam/confirm.vue` 第 185 行

**当前**：fire-and-forget（`.catch(() => {})` 不等结果）→ 导致 analysis 页拿不到结果

**改为**：提交后立即跳转 analysis 页（confirm 现在立即返回 analyzing）：
```ts
async function handleConfirm() {
  // ... 收集确认数据
  try {
    await confirmRecognition(examId.value, payload)  // 现在立即返回
    uni.showToast({ title: '已提交，正在分析', icon: 'none' })
    setTimeout(() => {
      uni.redirectTo({ url: `/pages/exam/analysis?examId=${examId.value}` })
    }, 500)
  } catch (e) {
    uni.showToast({ title: e.message || '提交失败', icon: 'none' })
  }
}
```

**service.ts 的 confirmRecognition**：超时从 3 分钟改回默认 30 秒。

### F-5：analysis 页 — 轮询分析结果

**文件**：`frontend/src/pages/exam/analysis.vue` 第 137-149 行

**当前**：`await getAnalysis()` 30 秒超时无轮询 → 拿不到结果

**改为**：
```ts
async function loadAnalysis() {
  loading.value = true
  try {
    const res = await poll(
      () => getAnalysis(examId.value),
      (data) => data.data.status === 'analyzed',
      2500, 60
    )
    if (res.code === 0) {
      analysis.value = res.data
    }
  } catch (e) {
    uni.showToast({ title: '分析超时，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}
```

### F-6：practice 答题页 — 轮询题目

**文件**：`frontend/src/pages/practice/index.vue` 第 132 行

**改为**：轮询直到题目就绪：
```ts
const res = await poll(
  () => getPracticeQuestions(sessionId.value),
  (data) => data.data.status === 'ready',
  2500, 60
)
```

### F-7：practice 提交 + 结果页 — 轮询评估

**文件**：`frontend/src/pages/practice/index.vue` 提交逻辑 + `practice/result.vue` 第 97 行

**提交**（practice/index.vue）：submit 现在立即返回 assessing，直接跳 result 页：
```ts
async function finishPractice() {
  await submitPracticeResult(sessionId, results)  // 立即返回
  uni.redirectTo({ url: `/pages/practice/result?sessionId=${sessionId}&...` })
}
```

**结果页轮询**（practice/result.vue）：
```ts
const res = await poll(
  () => getAssessment(sessionId.value),
  (data) => data.data.status === 'assessed',
  2500, 60
)
```

### F-8：移除 Promise.race 超时兜底

**文件**：`frontend/src/pages/exam/analysis.vue` 第 161-175 行、`weakness/index.vue` 类似位置

**当前**：`generatePractice` 用 `Promise.race` 10 秒超时后放弃 → 题目丢失

**改为**：generatePractice 现在立即返回 session_id（generating），直接跳答题页轮询，不再用 Promise.race。

---

## 五、识别试卷特殊处理说明（重点）

用户强调：识别试卷涉及家长审查对错，异步化后必须能找到审查入口。

**方案保证**：
1. 上传后**立即返回 exam_id**，前端带 exam_id 跳到 **confirm 页**
2. confirm 页是**常驻审查入口**，无论何时进入都会轮询并展示识别结果
3. 即使用户离开再回来，只要带 exam_id 进入 confirm 页，就能看到识别结果（已存储）并审查
4. 识别未完成时显示"识别中"，完成后自动展示题目

**入口路径**：
- 上传后：upload → confirm（自动跳转）
- 历史入口：home 页"最近诊断"卡片点击 → confirm（需 home 页带 exam_id 跳转，已有此逻辑）

---

## 六、任务分配

### 后端（8 个任务）

| # | 任务 | 优先级 |
|---|------|--------|
| B-1 | PracticeSession 新增 status 字段 + 迁移 | P0 |
| B-2 | upload/upload-by-urls 异步化（OCR 后台） | P0 |
| B-3 | confirm 异步化（分析后台）+ 启用 ANALYZING | P0 |
| B-4 | analysis 端点支持 analyzing 中间态 | P0 |
| B-5 | practice/generate 异步化（出题后台） | P0 |
| B-6 | practice/questions 支持 generating 中间态 | P0 |
| B-7 | submit + assessment 异步化（评估后台） | P0 |
| B-8 | 切换 AI 配置到 opencode（deepseek-v4-flash + mimo-v2.5） | P0 |

### 前端（8 个任务）

| # | 任务 | 优先级 |
|---|------|--------|
| F-1 | 新建 poll.ts 轮询工具 | P0 |
| F-2 | upload 页提交后立即跳 confirm | P0 |
| F-3 | confirm 页轮询识别结果（审查入口） | P0 |
| F-4 | confirm 提交改为正常 await + 跳 analysis | P0 |
| F-5 | analysis 页轮询分析结果 | P0 |
| F-6 | practice 答题页轮询题目 | P0 |
| F-7 | practice 提交 + result 页轮询评估 | P0 |
| F-8 | 移除 Promise.race 超时兜底 | P0 |

---

## 七、验收标准

```
1. 上传试卷 → 1 秒内跳到确认页 → 显示"识别中" → 15-30 秒后自动展示题目 → 家长可审查
2. 确认提交 → 立即跳分析页 → 显示"分析中" → 30-60 秒后展示薄弱点
3. 开始练习 → 立即跳答题页 → 显示"生成中" → 10-20 秒后展示题目
4. 提交答案 → 立即跳结果页 → 显示"评估中" → 10-20 秒后展示掌握度
5. 全程无 30 秒超时报错
6. AI 调用走 opencode：通用 deepseek-v4-flash，图片 mimo-v2.5
7. 带 exam_id 重新进入 confirm 页，能再次看到识别结果（审查入口不丢）
```

---

## 八、需用户确认

1. **opencode go 套餐的 API base_url**（文档中留了 `https://api.opencode.ai/v1` 占位符，请提供实际地址）
2. **opencode 的 API Key**（填入 .env，不提交到 git）
