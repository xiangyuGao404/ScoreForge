# ScoreForge AI 模型重构任务清单

**目标**：重构 AI 服务架构，支持多模型、多平台、用户自配置，试卷识别改用多模态 AI。

---

## 需求概览

### 当前问题

1. **试卷识别是假的** — `ocr_service.py` 返回 `random.choice` 的随机数据
2. **AI 平台写死在代码里** — `config.py` 硬编码了小米 TokenPlan 地址
3. **只支持一个模型** — 识别和对话用同一个模型，无法区分
4. **用户无法配置自己的 API** — 设置页只有开关，没有实际的配置和测试功能

### 目标架构

```
用户设置
├── API 来源：系统内置 / 自备 Key
├── AI 平台：小米 TokenPlan / DeepSeek / OpenAI 兼容
├── 通用模型：mimo-v2.5-pro / deepseek-v4-flash / gpt-4o
├── 图片识别模型：mimo-v2.5 / DeepSeek-VL2 / gpt-4o
└── [测试连接] 按钮 → 验证 API Key + 模型是否可用
```

### 模型配置规则

| 平台 | 通用模型（分析/出题/评估） | 图片识别模型（试卷识别） |
|------|--------------------------|------------------------|
| 小米 TokenPlan | `mimo-v2.5-pro` | `mimo-v2.5` |
| DeepSeek | `deepseek-v4-flash` | `DeepSeek-VL2` |
| OpenAI 兼容 | 用户自填 | 用户自填 |

---

## 后端任务

### B-1：重构 config.py — 支持多平台多模型配置

**文件**：`backend/app/core/config.py`

**当前**：
```python
XIAOMI_API_KEY: Optional[str] = None
XIAOMI_API_BASE: str = "https://token-plan-cn.xiaomimimo.com/v1"
XIAOMI_MODEL: str = "mimo-v2.5-pro"
AI_PROVIDER: str = "xiaomi"
```

**改为**：
```python
# AI 平台配置（系统级默认值，可被用户配置覆盖）
AI_PROVIDER: str = "xiaomi"  # xiaomi / deepseek / openai

# 小米 TokenPlan
XIAOMI_API_KEY: Optional[str] = None
XIAOMI_API_BASE: str = "https://token-plan-cn.xiaomimimo.com/v1"
XIAOMI_GENERAL_MODEL: str = "mimo-v2.5-pro"      # 通用：分析、出题、评估
XIAOMI_VISION_MODEL: str = "mimo-v2.5"            # 图片识别

# DeepSeek
DEEPSEEK_API_KEY: Optional[str] = None
DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
DEEPSEEK_GENERAL_MODEL: str = "deepseek-v4-flash"
DEEPSEEK_VISION_MODEL: str = "DeepSeek-VL2"

# OpenAI 兼容（用户自填）
OPENAI_API_KEY: Optional[str] = None
OPENAI_API_BASE: str = "https://api.openai.com/v1"
OPENAI_GENERAL_MODEL: str = "gpt-4o"
OPENAI_VISION_MODEL: str = "gpt-4o"
```

**要点**：
- 每个平台区分 `GENERAL_MODEL`（文本任务）和 `VISION_MODEL`（图片识别）
- 不要把任何平台的 API Key 写死在代码或 .env.example 中
- `.env.example` 中只放占位符：`XIAOMI_API_KEY=`

---

### B-2：重写 OCR 服务 — 用多模态 AI 识别试卷

**文件**：`backend/app/services/ocr_service.py`

**当前**：用 PaddleOCR 做文字识别 + `random.choice` 生成对错。

**改为**：用多模态 AI（如 mimo-v2.5）直接分析试卷图片，一次性输出：
- 每道题的题目内容
- 学生的答案
- 是否正确
- 得分
- 置信度

**核心逻辑**：
```python
class OCRService:
    async def recognize_exam(self, image_paths: list[str], subject: str) -> dict:
        """
        用多模态 AI 识别试卷图片。
        1. 将图片编码为 base64
        2. 构造多模态 prompt（含图片）
        3. 调用 vision model
        4. 解析返回的 JSON
        """
        # 获取 vision model 配置
        client, model = ai_service._get_vision_client()

        if not client:
            return self._mock_recognition()

        # 构造多模态消息
        content = [
            {"type": "text", "text": VISION_PROMPT.format(subject=subject)},
        ]
        for img_path in image_paths:
            base64_img = self._encode_image(img_path)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
            })

        # 调用 AI
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=4096,
        )

        # 解析结果
        result = _parse_json_from_text(response.choices[0].message.content)
        return {"questions": _extract_list_from_response(result)}
```

**Vision Prompt 设计**：
```
你是一位试卷识别专家。请仔细分析这张试卷图片，识别出每一道题目。

对于每道题，请输出：
1. 题号
2. 题目内容（完整抄写）
3. 学生写的答案（如果能看到）
4. 是否正确（根据批改痕迹判断：✓/✗、分数、红笔批注）
5. 该题得分
6. 该题总分
7. 置信度（0-1，你对识别结果的确信程度）

注意事项：
- 如果看不清某道题，置信度设为 0.5 以下
- 如果没有批改痕迹，is_correct 设为 null
- 如果分数看不清，score_got 设为 null
- 数学公式请用 LaTeX 格式表示

请严格返回 JSON 数组格式：
[{"question_no":1, "question_content":"...", "student_answer":"...", "is_correct":true, "score_got":5, "score_total":5, "confidence":0.95}]
```

---

### B-3：重构 AI 服务 — 支持多平台切换

**文件**：`backend/app/services/ai_service.py`

**改动要点**：

1. **`_get_client(task_type="general")`** — 根据 task_type 返回对应的 client 和 model
   - `task_type="general"` → 用通用模型（分析、出题、评估）
   - `task_type="vision"` → 用视觉模型（试卷识别）

2. **支持用户自备 API Key** — 优先使用用户的 Key，其次用系统默认

3. **平台切换逻辑**：
```python
def _get_client(self, task_type="general", user_config=None):
    """
    获取 AI 客户端。
    优先级：用户配置 > 系统配置 > mock
    """
    # 如果用户配置了自己的 API
    if user_config and user_config.get("api_key"):
        provider = user_config.get("provider", "openai")
        api_key = user_config["api_key"]
        api_base = user_config.get("api_base", "")
        model = user_config.get(f"{task_type}_model", "")
    else:
        # 使用系统默认配置
        provider = settings.AI_PROVIDER
        if provider == "xiaomi":
            api_key = settings.XIAOMI_API_KEY
            api_base = settings.XIAOMI_API_BASE
            model = settings.XIAOMI_VISION_MODEL if task_type == "vision" else settings.XIAOMI_GENERAL_MODEL
        elif provider == "deepseek":
            api_key = settings.DEEPSEEK_API_KEY
            api_base = settings.DEEPSEEK_API_BASE
            model = settings.DEEPSEEK_VISION_MODEL if task_type == "vision" else settings.DEEPSEEK_GENERAL_MODEL
        else:  # openai
            api_key = settings.OPENAI_API_KEY
            api_base = settings.OPENAI_API_BASE
            model = settings.OPENAI_VISION_MODEL if task_type == "vision" else settings.OPENAI_GENERAL_MODEL

    if not api_key:
        return None, None

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key, base_url=api_base)
    return client, model
```

---

### B-4：新增 API 测试端点

**文件**：新建 `backend/app/api/v1/settings.py`

```
POST /api/v1/settings/test-api
Body: {
    "provider": "xiaomi",          // 可选，默认用系统配置
    "api_key": "tp-xxx",           // 可选，测试用户自己的 Key
    "api_base": "https://...",     // 可选
    "model": "mimo-v2.5-pro",      // 可选
    "task_type": "general"         // general 或 vision
}
Response: {
    "code": 0,
    "data": {
        "success": true,
        "model": "mimo-v2.5-pro",
        "response_preview": "你好，我是...",
        "latency_ms": 1200
    }
}
```

**实现**：发送一个简单的测试请求（如"请回复OK"），验证 API Key 和模型是否可用。

---

### B-5：新增用户 API 配置存储端点

**文件**：`backend/app/api/v1/settings.py`

```
PUT /api/v1/settings/api-config
Body: {
    "provider": "xiaomi",
    "api_key": "tp-xxx",
    "api_base": "https://...",
    "general_model": "mimo-v2.5-pro",
    "vision_model": "mimo-v2.5"
}
Response: { "code": 0, "message": "配置已保存" }

GET /api/v1/settings/api-config
Response: {
    "code": 0,
    "data": {
        "provider": "xiaomi",
        "api_key_set": true,       // 不返回实际 Key，只返回是否已设置
        "api_base": "https://...",
        "general_model": "mimo-v2.5-pro",
        "vision_model": "mimo-v2.5"
    }
}
```

**存储**：加密后存入 `User` 表的新字段 `api_config_encrypted`（JSON 加密存储）。

---

### B-6：数据库 — User 表新增 api_config 字段

**文件**：`backend/app/models/user.py`

```python
api_config_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
# 存储格式：Fernet 加密后的 JSON 字符串
# {"provider":"xiaomi","api_key":"tp-xxx","api_base":"...","general_model":"...","vision_model":"..."}
```

需要新增 Alembic 迁移。

---

## 前端任务

### F-1：设置页 — 重构 API 配置区域

**文件**：`frontend/src/pages/settings/index.vue`

**当前**：只有一个开关（内置/自备）+ 一个 API Key 输入框。

**改为**：

```
┌─────────────────────────────────────┐
│  🔑 API 配置                        │
├─────────────────────────────────────┤
│  AI 模式                            │
│  ○ 系统内置（¥0.99/月）              │
│  ● 自备 API Key                     │
├─────────────────────────────────────┤
│  （自备模式下显示以下内容）            │
│                                     │
│  AI 平台                            │
│  ○ 小米 TokenPlan                   │
│  ○ DeepSeek                         │
│  ○ OpenAI 兼容                      │
│                                     │
│  API Key  [________________] [👁]    │
│  API 地址 [________________]         │
│                                     │
│  通用模型  [mimo-v2.5-pro    ▼]     │
│  图片模型  [mimo-v2.5        ▼]     │
│                                     │
│  [测试连接]                          │
│  ✅ 连接成功，模型 mimo-v2.5-pro     │
│     响应时间 1.2s                    │
└─────────────────────────────────────┘
```

**模型下拉选项**：

| 平台 | 通用模型选项 | 图片模型选项 |
|------|-------------|-------------|
| 小米 | mimo-v2.5-pro | mimo-v2.5 |
| DeepSeek | deepseek-v4-flash | DeepSeek-VL2 |
| OpenAI | gpt-4o, gpt-4o-mini, 自填 | gpt-4o, 自填 |

---

### F-2：新增 API 测试功能

**文件**：`frontend/src/pages/settings/index.vue` + `frontend/src/utils/service.ts`

**交互流程**：
1. 用户填完配置，点击"测试连接"
2. 前端调用 `POST /api/v1/settings/test-api`
3. 显示结果：成功（模型名 + 响应时间）或失败（错误信息）

**service.ts 新增**：
```ts
export async function testApiConfig(params: {
  provider?: string
  api_key?: string
  api_base?: string
  model?: string
  task_type: 'general' | 'vision'
}) {
  if (USE_MOCK) {
    await mock.delay(1500)
    return { code: 0, data: { success: true, model: 'mock-model', latency_ms: 500 } }
  }
  return request({ url: '/settings/test-api', method: 'POST', data: params })
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
  return request({ url: '/settings/api-config', method: 'POST', data: config })
}

export async function getApiConfig() {
  if (USE_MOCK) {
    return { code: 0, data: { provider: 'xiaomi', api_key_set: false } }
  }
  return request({ url: '/settings/api-config' })
}
```

---

### F-3：上传试卷时传递学科信息

**文件**：`frontend/src/utils/service.ts` 的 `uploadExam`

**当前**：`uploadExam` 已经传了 `subject`，但后端 OCR 服务没有用它。

**改动**：确保 `subject` 参数正确传递，后端 OCR 会根据学科调整识别 Prompt。

---

## 任务分配

### 后端（5 个任务）

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| B-1 | config.py 多平台多模型配置 | P0 | 基础，其他任务依赖这个 |
| B-2 | OCR 服务改用多模态 AI | P0 | 核心功能，解决"识别是假的"问题 |
| B-3 | AI 服务支持多平台切换 | P0 | 通用/视觉模型分离 |
| B-4 | API 测试端点 | P1 | 前端测试按钮依赖这个 |
| B-5 | 用户 API 配置存储端点 | P1 | 用户自备 Key 依赖这个 |
| B-6 | User 表新增字段 + 迁移 | P1 | B-5 依赖这个 |

### 前端（3 个任务）

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| F-1 | 设置页重构 API 配置区域 | P0 | 用户配置入口 |
| F-2 | API 测试功能 | P1 | 验证配置是否正确 |
| F-3 | 确保 subject 正确传递 | P1 | 配合后端 OCR |

---

## 验收标准

```
1. 系统内置模式：不填任何 Key，试卷识别走系统默认模型，返回真实识别结果（非 mock）
2. 自备 Key 模式：选择平台 → 填 Key → 选模型 → 测试连接 → 显示成功/失败
3. 试卷识别：上传数学试卷图片 → AI 返回题目内容 + 对错判断（不是随机数据）
4. 模型切换：切换到 DeepSeek → 测试连接成功 → 试卷识别走 DeepSeek-VL2
5. 通用/视觉分离：分析用 mimo-v2.5-pro，识别用 mimo-v2.5，互不影响
```
