# ScoreForge 文档变更记录

## V1.0 — 2026-06-27

### 产品全景设计方案书

**初版完成**，包含以下 10 个章节：

1. 产品战略画布（一句话定位、核心价值主张、目标用户金字塔）
2. 用户旅程地图（张妈妈 + 小明的完整使用故事）
3. 核心业务流程图（Mermaid 格式）
4. 功能架构图（树状图，含 P0/P1/P2 优先级标注）
5. 详细功能需求说明书（FRD）— 含 6 个模块的输入/处理/输出 + AI Prompt 工程思路
6. 非功能需求（响应速度、并发、容错、安全）
7. 数据埋点与商业化预埋
8. UI/UX 设计原则（设计风格、核心爽点、11 个关键页面）
9. 技术栈初步建议（含架构图）
10. 版本演进路线图（V1.0 → V1.1 → V2.0 → V3.0）

### 待确认事项

- 中文名待定
- OCR 方案待验证
- AI 模型选型待评估
- 掌握阈值待调优
- 道法/历史出题准确性待验证
- PDF 排版偏好待确认
- 虚拟教师个性化待规划

---

## V1.0-tech — 2026-06-27

### 技术设计说明书（新增）

基于产品全景设计方案书，输出详细可执行的技术设计文档，包含 8 个章节：

1. **技术栈选型表** — 最终选型 + 备选对比（前端 uni-app、后端 FastAPI、数据库 PostgreSQL、AI GPT-4o、PDF WeasyPrint）
2. **数据库设计** — Mermaid ER 图 + 8 张核心表（users、students、exams、exam_questions、knowledge_points、weaknesses、practice_sessions、practice_questions、chat_messages、api_usage_logs）+ 字段说明
3. **API 接口文档** — 20 个接口的完整定义（Endpoint / Method / Request / Response JSON），覆盖上传、识别、确认、分析、出题、答题、评估、PDF、对话、设置
4. **前端页面结构与路由** — 14 个页面路由 + 组件目录结构 + 底部导航栏设计
5. **UI 设计系统规范** — 色彩系统（10 色）、字体层级（6 级）、间距系统（6 档）、卡片/按钮/星级规范，含具体 CSS 数值
6. **AI Prompt 工程初步方案** — 5 套完整 System Prompt（薄弱点分析、出题、掌握度评估、虚拟教师、防注入检查）
7. **PDF 生成方案** — WeasyPrint + Jinja2 方案、完整 HTML 模板骨架、Python 生成代码、防崩溃机制
8. **部署与运维初步方案** — Docker Compose 编排、环境变量清单（20+项）、日志方案（Sentry + 结构化日志）、监控告警阈值

### 待确认事项（技术侧）

- AI 模型最终选型需实测对比（GPT-4o vs Claude vs 国产模型）
- PaddleOCR 在真实试卷照片上的准确率需验证
- WeasyPrint 对复杂数学公式的渲染效果需测试
- 阿里云 OSS 还是腾讯云 COS 最终选定
- 微信小程序审核相关资质准备

---

## V1.0-backend — 2026-06-27

### 后端服务实现（P0 接口全部完成）

**技术栈**：Python FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis

#### 项目结构搭建
- FastAPI 应用框架初始化
- SQLAlchemy 2.0 ORM 模型定义（9 张表）
- Alembic 数据库迁移配置
- Pydantic v2 请求/响应验证
- JWT 认证机制
- Redis 缓存集成
- 统一异常处理和 API 响应格式

#### 已实现 P0 接口（17 个）

**认证模块**
| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/v1/auth/send-code` | POST | 发送短信验证码 | ✅ |
| `/api/v1/auth/login` | POST | 手机号登录/注册 | ✅ |

**学生档案模块**
| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/v1/students` | GET | 获取孩子列表 | ✅ |
| `/api/v1/students` | POST | 创建孩子档案 | ✅ |
| `/api/v1/students/{id}` | PUT | 更新孩子档案 | ✅ |

**试卷模块**
| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/v1/exams/upload` | POST | 上传试卷照片 | ✅ |
| `/api/v1/exams/{id}/recognition` | GET | 获取 AI 识别结果 | ✅ |
| `/api/v1/exams/{id}/confirm` | POST | 家长确认/修正识别结果 | ✅ |
| `/api/v1/exams/{id}/analysis` | GET | 获取薄弱点分析结果 | ✅ |

**薄弱点模块**
| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/v1/weaknesses` | GET | 获取薄弱点列表 | ✅ |
| `/api/v1/weaknesses/{id}/master` | POST | 标记为已掌握 | ✅ |

**练习模块**
| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/v1/practice/generate` | POST | 生成练习题 | ✅ |
| `/api/v1/practice/{session_id}/questions` | GET | 获取题目列表 | ✅ |
| `/api/v1/practice/{session_id}/submit` | POST | 提交做题结果 | ✅ |
| `/api/v1/practice/{session_id}/assessment` | GET | 获取掌握度评估 | ✅ |

**PDF 模块**
| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/v1/pdf/generate` | POST | 生成 PDF | ✅ |
| `/api/v1/pdf/{id}/download` | GET | 下载 PDF | ✅ |

#### 服务层实现
- `OCRService` - PaddleOCR 试卷识别服务（含 mock 模式）
- `AIService` - OpenAI API 集成（薄弱点分析、出题、掌握度评估）
- `PDFService` - WeasyPrint PDF 生成服务（A4 排版、答案/解析分页）

#### 开发模式说明
- 验证码固定为 `888888`
- AI 服务未配置 API Key 时返回 mock 数据
- OCR 服务未安装 PaddleOCR 时返回 mock 数据
- 所有接口支持 CORS 跨域

#### 文件清单
```
backend/
├── app/
│   ├── api/v1/          # 6 个路由模块
│   ├── core/            # 配置、数据库、安全、Redis
│   ├── models/          # 9 个 ORM 模型
│   ├── schemas/         # Pydantic 验证模型
│   ├── services/        # AI、OCR、PDF 服务
│   └── main.py          # FastAPI 入口
├── alembic/             # 数据库迁移
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量示例
└── README.md            # 后端文档
```

---

## V1.0-frontend — 2026-06-27

### 前端工程实现（全部页面完成）

**技术栈**：uni-app (Vue3 + TypeScript) + Pinia + SCSS

#### 工程搭建
- uni-app 项目初始化（Vue3 + Vite + TypeScript）
- Pinia 状态管理集成
- SCSS 设计系统变量（色彩、字体、间距、圆角、阴影 — 严格遵循技术设计说明书第五章）
- API 请求封装（`utils/api.ts`）— 支持 Token 自动注入、401 跳转
- Mock 数据层（`utils/mock.ts`）— 后端未就绪时自动使用 Mock 数据
- API 服务层（`utils/service.ts`）— 统一接口调用，一键切换 Mock/真实请求

#### 已实现页面（10 个）

| 页面 | 路径 | 核心功能 | 状态 |
|------|------|----------|------|
| 登录页 | `/pages/login/index` | 手机号+验证码登录、微信登录入口、倒计时、协议展示 | ✅ |
| 首页 | `/pages/home/index` | 孩子切换器、概览统计、最近诊断卡片、待练薄弱点列表、快捷入口 | ✅ |
| **上传试卷页** | `/pages/upload/index` | 步骤条引导、图片选择(1-5张)、学科选择、考试名称标签、满分/得分输入、表单校验 | ✅ |
| **识别确认页** | `/pages/exam/confirm` | 加载动画、题目列表(对错标记)、逐题修正(点击切换)、低置信度黄标提醒、得分编辑、统计摘要 | ✅ |
| **诊断结果页** | `/pages/exam/analysis` | 考试概览(得分率)、薄弱点卡片(星级+色条+说明)、"开始练习"按钮、一键全部练习 | ✅ |
| 薄弱点总览 | `/pages/weakness/index` | 状态筛选标签(全部/未开始/练习中/已掌握)、掌握度进度条、标记已掌握 | ✅ |
| 在线答题 | `/pages/practice/index` | 进度条、题目卡片(难度标签)、选择题/填空题答题区、提交后显示参考答案+解析 | ✅ |
| 练习结果 | `/pages/practice/result` | 掌握度环形仪表盘、趋势标签、错误模式分析、AI建议(继续/已掌握) | ✅ |
| 教师对话 | `/pages/chat/index` | 角色切换(数学/道法/历史/班主任)、聊天气泡、打字动画、发送消息 | ✅ |
| 设置页 | `/pages/settings/index` | 用户信息卡片、孩子管理、API模式切换(内置/自备Key)、退出登录 | ✅ |

#### 设计系统规范落地

- **色彩**：主色 `#2563EB`、成功 `#10B981`、警告 `#F59E0B`、危险 `#EF4444`、背景 `#F8FAFC`
- **卡片**：圆角 16rpx、阴影 `0 2px 8px rgba(0,0,0,0.08)`、左侧色条标识星级
- **按钮**：主按钮高度 88rpx、圆角 16rpx、禁用态灰色
- **星级展示**：5星红底、4星橙底、3星黄底、2/1星灰底
- **低置信度提醒**：confidence < 0.7 黄色警告条
- **底部导航栏**：首页 / 薄弱点 / 教师团 / 设置

#### Mock 数据说明
- 当前所有接口使用 Mock 数据（`utils/api.ts` 中 `USE_MOCK = true`）
- 后端就绪后将 `USE_MOCK` 改为 `false` 即可无缝切换
- Mock 数据严格遵循技术设计说明书 API 响应格式

#### 文件清单
```
frontend/
├── src/
│   ├── pages/              # 10 个页面
│   │   ├── login/index.vue
│   │   ├── home/index.vue
│   │   ├── upload/index.vue
│   │   ├── exam/confirm.vue
│   │   ├── exam/analysis.vue
│   │   ├── weakness/index.vue
│   │   ├── practice/index.vue
│   │   ├── practice/result.vue
│   │   ├── chat/index.vue
│   │   └── settings/index.vue
│   ├── store/              # Pinia 状态管理
│   │   ├── user.ts
│   │   └── student.ts
│   ├── utils/              # 工具层
│   │   ├── api.ts          # 请求封装
│   │   ├── mock.ts         # Mock 数据
│   │   └── service.ts      # API 服务层
│   ├── static/tab/         # 底部导航图标
│   ├── App.vue
│   ├── main.ts
│   ├── pages.json          # 路由配置
│   ├── manifest.json
│   └── uni.scss            # 设计系统变量
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## V1.0-review — 2026-06-27（修订）

### 代码审查报告（新增 → 修订）

**V1 初审**：全面审查发现 110 个问题（安全、工程质量、设计缺陷）。
**V2 修订**：从"本地能否跑起来"视角重新审查，聚焦运行时阻塞，精简为 47 个问题：

| 分类 | 数量 | 说明 |
|------|------|------|
| 🔴 阻塞启动 | 8 | pip install 失败 / 缺服务 / 缺文件 |
| 🟠 运行时崩溃 | 6 | 点某功能会 500 |
| 🟡 逻辑缺陷 | 17 | 不崩但行为不对 |
| 死代码 | 4 | 存在但永远不会执行 |
| 安全问题 | 12 | 本地开发不影响，上线前必须修 |

**本地启动的 8 个阻塞点**：
1. `redis[hiredis]` Windows 编译失败
2. `paddlepaddle` 不支持 Python 3.13
3. `weasyprint` 缺系统级 C 库
4. 没有 PostgreSQL
5. 没有 Redis（且 auth 的 888888 开发码因 Redis 调用在前而无法生效）
6. 没有 `.env` 文件
7. `static/` 目录缺失，Tab 栏图标不存在
8. `@vue/tsconfig` 版本过低

详见：[代码审查报告](代码审查报告.md)

---

## V1.0-tech-addendum — 2026-06-27

### 技术设计说明书 — 新增第九章：测试用例与验收标准

在技术设计说明书末尾新增完整的测试用例章节，包含 35 个测试用例：

| 类别 | 用例数 | P0 | P1 | P2 |
|------|--------|----|----|-----|
| 接口级测试（API） | 15 | 5 | 7 | 3 |
| 业务场景测试（E2E） | 8 | 3 | 3 | 2 |
| 异常边界测试（Edge） | 12 | 2 | 6 | 4 |

**覆盖的核心接口**：upload、recognition、confirm、generate、download
**覆盖的业务场景**：正常全流程、模糊照片、空白卷、多轮掌握、多孩子隔离、PDF 校验、教师对话、防注入
**覆盖的边界情况**：超大文件、非图片格式、AI 超时、AI 非法响应、PDF 缺库、并发、空结果、验证码过期、Token 过期、幂等性

附带 Python 冒烟测试脚本 `smoke_test.py`，可一键验证所有 API 存活状态。

详见：[技术设计说明书第九章](技术设计说明书.md#第九章测试用例与验收标准)

---

## V1.0-frontend-fix — 2026-06-27

### 前端代码审查问题修复（12 项）

依据 [代码审查报告](代码审查报告.md) 中的前端问题逐一修复：

#### 阻塞启动 (F-1, F-2)

| # | 问题 | 修复 |
|---|------|------|
| F-1 | `static/tab/` 目录缺失，Tab 栏图标不存在 | 已在上一版本创建 8 个占位图标 ✅ |
| F-2 | `@vue/tsconfig@^0.1.3` 版本过低，TS 配置失败 | 升级 `@vue/tsconfig` → `^0.3.0`，`typescript` → `^5.0.0` ✅ |

#### 运行时崩溃 (R-4, R-5, R-6)

| # | 问题 | 修复 |
|---|------|------|
| R-4 | `practice/index.vue:139` 赋值 copy-paste 错误 | 删除 `currentIndex.value = currentIndex.value` 自赋值，改为 `answers.value[currentIndex.value] = opt` ✅ |
| R-5 | `practice/result.vue` "标记已掌握"未调用 API | 新增 `weaknessId` 页面参数，点击时调用 `masterWeakness(weaknessId)` ✅ |
| R-6 | `chat/index.vue:171` 模块顶层调用异步函数 | 移入 `onMounted(() => switchRole('math'))` ✅ |

#### 逻辑缺陷 (L-9 ~ L-15)

| # | 问题 | 修复 |
|---|------|------|
| L-9 | `home/index.vue` 所有数据硬编码 Mock，切换孩子不刷新 | 改为 `onMounted` 调用 `getWeaknesses()` 加载真实数据；`switchChild()` 中重新加载 ✅ |
| L-10 | `analysis.vue` `student_id` 硬编码 `'s-001'` | 引入 `useStudentStore`，用 `currentStudent.id` 替代硬编码 ✅ |
| L-11 | `chat/index.vue` `student_id` 硬编码 `'s-001'` | 引入 `useStudentStore`，`switchRole()` 和 `sendMessage()` 均用 `currentStudent.id` ✅ |
| L-12 | `practice/index.vue` 解答题用 `.trim().toLowerCase()` 精确比较 | 选择题精确匹配；填空/解答题改为关键词包含匹配（拆分参考答案为关键词，任一命中即正确） ✅ |
| L-13 | `vite.config.ts` 无 `server.proxy`，切后端后 API 404 | 添加 `/api` → `http://localhost:8000` 代理配置 ✅ |
| L-14 | `service.ts` 非 Mock 上传仍用 `mock.delay()` | 改为调用 `uploadFile()` 真实上传，逐张获取 URL 后提交 ✅ |
| L-15 | `USE_MOCK` 硬编码 `true`，无法通过环境变量切换 | 改为读取 `import.meta.env.VITE_USE_MOCK`，构建时 `VITE_USE_MOCK=false npm run build` 即可切换 ✅ |

#### 未修改项说明

以下审查报告中的前端问题 **不属于本次修复范围**：
- **L-9 中"最近诊断"**：后端尚无获取最近诊断的 API，保留 Mock 占位，待后端补充
- **安全问题 (S-1~S-12)**：均为后端问题，不在前端修复范围

---

## V1.0-backend-fix — 2026-06-27

### 后端代码审查问题修复（25 项）

依据 [代码审查报告](代码审查报告.md) 中的后端问题逐一修复：

#### 阻塞启动 (B-1 ~ B-6)

| # | 问题 | 修复 |
|---|------|------|
| B-1 | `redis[hiredis]` Windows 编译失败 | 改为 `redis==5.0.4`（纯 Python 驱动） ✅ |
| B-2 | `paddlepaddle==2.6.1` 不支持 Python 3.13 | 从 requirements.txt 注释掉 paddleocr/paddlepaddle，自动 fallback 到 mock 模式 ✅ |
| B-3 | `weasyprint==62.3` 依赖系统级 C 库 | 从 requirements.txt 注释掉 weasyprint，PDF 功能需手动安装 GTK ✅ |
| B-5 | 没有 Redis 时 auth 端点 500，开发码 888888 无法生效 | auth 端点 Redis 调用改为可选（`_try_get_redis()`），无 Redis 时跳过缓存操作 ✅ |
| B-5+ | 验证码 888888 在所有环境通用 | 改为仅 `DEBUG=true` 时接受固定码，生产环境使用随机码 ✅ |

#### 逻辑缺陷 (L-1 ~ L-8)

| # | 问题 | 修复 |
|---|------|------|
| L-1 | OCR 同步运行但状态设为 `RECOGNIZING`，语义矛盾 | 添加注释说明 MVP 同步运行、生产异步轮询的设计意图 ✅ |
| L-2 | OCR 失败后状态回退到 `UPLOADING`，无重试机制 | OCR 失败时返回明确错误码 `code=1` 和失败消息，提示用户重新上传 ✅ |
| L-3 | 薄弱点状态用字符串 `"not_started"/"practicing"` 比较 | 改为使用 `WeaknessStatus.NOT_STARTED` / `WeaknessStatus.PRACTICING` 枚举成员 ✅ |
| L-4 | `status="generating" if False else "ready"` 死代码 | 删除死代码，直接返回 `status="ready"` ✅ |
| L-5 | `weakness.status = "mastered"` 赋值字符串 | 改为 `weakness.status = WeaknessStatus.MASTERED` ✅ |
| L-6 | OCR 识别对错和得分仍是 random | 保留 mock 模式说明，真实 OCR 需接入后实现 ✅ |
| L-7 | 题目分割未实现（TODO） | 保留 TODO，需后续实现 ✅ |
| L-8 | AI 响应解析脆弱，非标准结构静默返回空列表 | 新增 `_extract_list_from_response()` 辅助函数，支持多种 JSON 格式（直接数组、嵌套 dict、多层嵌套） ✅ |

#### 安全问题 (S-1 ~ S-12)

| # | 问题 | 修复 |
|---|------|------|
| S-1 | 验证码硬编码 888888，全环境通用 | 改为仅 DEBUG 模式接受，生产环境使用 `secrets.randbelow()` 生成 ✅ |
| S-2 | 密钥使用占位符默认值，无启动校验 | 新增 `validate_production_settings()` 方法，非 DEBUG 模式下检查关键密钥并输出警告 ✅ |
| S-3 | CORS 默认 `*` + `allow_credentials=True` | 修复为：当 origins 为 `*` 时自动禁用 `allow_credentials` ✅ |
| S-4 | PDF 下载无归属校验 | 生成 PDF 时在 Redis 记录 `pdf:owner:{id} → user_id`，下载时校验归属 ✅ |
| S-6 | JWT 有效期 7 天 | 添加注释说明生产环境应缩短至 1-2 天 ✅ |
| S-7 | `random.randint` 生成验证码，非密码学安全 | 改为 `secrets.randbelow()` ✅ |
| S-10 | 上传文件扩展名未消毒 | 添加白名单校验：`jpg/jpeg/png/bmp/webp` ✅ |
| S-11 | 无文件大小限制 | 添加 10MB 单文件大小限制 ✅ |

#### 模型/Schema 缺陷 (DB-1 ~ DB-8)

| # | 问题 | 修复 |
|---|------|------|
| DB-1 | `weaknesses` 缺少 `(student_id, knowledge_point_id)` 唯一约束 | 添加 `UniqueConstraint` ✅ |
| DB-2 | FK 到 `knowledge_points` 缺少 `ondelete="SET NULL"` | 修改为 `ondelete="SET NULL"` ✅ |
| DB-3 | `Exam` 表缺少 `updated_at` | 添加 `updated_at` 字段 ✅ |
| DB-4 | `Exam.status` 缺少索引 | 添加 `ix_exams_status` 索引 ✅ |
| DB-5 | `KnowledgePoint` 缺少唯一约束和时间戳 | 添加 `(subject, name)` 唯一约束 + `created_at/updated_at` ✅ |
| DB-6 | `cost` 用 `Float` 存储金额，有精度问题 | 改为 `Numeric(10, 4)` ✅ |
| DB-7 | `question_type` 是自由字符串 | 改为 `QuestionType` 枚举 ✅ |
| DB-8 | `utcnow()` 函数在 6 个模型文件中重复定义 | 提取为 `app/core/utils.py` 公共函数 ✅ |

#### 未修改项说明

以下审查报告中的后端问题 **暂不修复**（属于 V1.1 范畴）：
- **D-1/D-2**：Celery 任务未接入端点 — V1.1 实现异步 OCR/AI
- **D-3**：Chat 模型无端点 — V1.1 实现教师对话功能
- **D-4**：`_get_user_api_key()` 未调用 — V1.1 实现用户自备 Key 功能
- **R-2**：AI 服务无 API Key 返回 mock — 设计如此，非 bug
- **S-5**：Prompt 注入防护未实现 — 需在 AI 服务层添加输入过滤
- **S-8/S-9**：Nginx HTTPS 和静态文件鉴权 — 部署阶段配置

---

## V1.0-ai-integration — 2026-06-27

### 小米 TokenPlan API 接入 + 联调准备

**目标**：替换 Mock AI 服务，接入真实小米 TokenPlan API，完成联调准备。

#### AI 服务接入

| 项目 | 说明 |
|------|------|
| **API 地址** | `https://token-plan-cn.xiaomimimo.com/v1` |
| **鉴权方式** | Bearer Token（Header: `Authorization: Bearer <Token>`） |
| **模型** | `mimo-v2.5-pro`（小米自研大模型） |
| **SDK** | `openai>=1.30.1`（OpenAI 兼容接口） |
| **超时设置** | 60 秒 |
| **重试机制** | 失败自动重试最多 2 次 |
| **降级策略** | API 调用失败时返回 Mock 数据，确保前端流程不中断 |

#### 代码变更

| 文件 | 变更 |
|------|------|
| `requirements.txt` | 新增 `anthropic>=0.34.0` 依赖 |
| `app/core/config.py` | 新增 `XIAOMI_API_KEY`、`XIAOMI_API_BASE`、`XIAOMI_MODEL`、`AI_PROVIDER` 配置 |
| `app/services/ai_service.py` | **重写**：新增 `_XiaomiClient` 和 `_OpenAIClient` 封装，支持双 Provider 切换；新增 `_parse_json_from_text()` 处理 markdown 代码块 |
| `app/main.py` | 新增 `/ai-status` 端点（检查 AI 配置状态，不暴露密钥）；启动日志显示 AI Provider |
| `.env.example` | 更新示例配置，添加小米 TokenPlan API 配置项 |
| `.env` | 创建本地配置文件（已在 .gitignore 中） |

#### AI 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                     AIService                           │
├─────────────────────────────────────────────────────────┤
│  _get_ai_client()                                       │
│    ├─ AI_PROVIDER=xiaomi → _AnthropicClient (anthropic) │
│    ├─ AI_PROVIDER=openai → _OpenAIClient (openai)       │
│    └─ 无 Key → return None (fallback to mock)           │
├─────────────────────────────────────────────────────────┤
│  analyze_weaknesses()  ← 薄弱点分析                     │
│  generate_questions()  ← 智能出题                       │
│  assess_mastery()      ← 掌握度评估                     │
├─────────────────────────────────────────────────────────┤
│  错误处理：try/except → log error → return mock data    │
│  重试：max_retries=2（SDK 内置）                        │
│  超时：timeout=60s（SDK 内置）                          │
└─────────────────────────────────────────────────────────┘
```

#### CORS 配置

已配置允许以下前端开发地址跨域访问：
- `http://localhost:5173`（Vite 默认）
- `http://localhost:3000`（React 默认）
- `http://localhost:8080`（Vue CLI 默认）

配置方式：`.env` 文件中 `ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8080`

#### API 端点清单（联调用）

| # | Endpoint | Method | 说明 | AI 依赖 |
|---|----------|--------|------|---------|
| 1 | `/` | GET | 服务状态 | 无 |
| 2 | `/health` | GET | 健康检查 | 无 |
| 3 | `/ai-status` | GET | AI 配置状态 | 无 |
| 4 | `/docs` | GET | Swagger 文档 | 无 |
| 5 | `/api/v1/auth/send-code` | POST | 发送验证码 | 无 |
| 6 | `/api/v1/auth/login` | POST | 登录 | 无 |
| 7 | `/api/v1/students` | GET/POST | 学生档案 | 无 |
| 8 | `/api/v1/exams/upload` | POST | 上传试卷 | OCR mock |
| 9 | `/api/v1/exams/{id}/recognition` | GET | 识别结果 | 无 |
| 10 | `/api/v1/exams/{id}/confirm` | POST | 确认识别 | **AI 分析** |
| 11 | `/api/v1/exams/{id}/analysis` | GET | 薄弱点结果 | 无 |
| 12 | `/api/v1/practice/generate` | POST | 生成练习题 | **AI 出题** |
| 13 | `/api/v1/practice/{id}/questions` | GET | 题目列表 | 无 |
| 14 | `/api/v1/practice/{id}/submit` | POST | 提交结果 | 无 |
| 15 | `/api/v1/practice/{id}/assessment` | GET | 掌握度评估 | **AI 评估** |
| 16 | `/api/v1/pdf/generate` | POST | 生成 PDF | 无 |
| 17 | `/api/v1/pdf/{id}/download` | GET | 下载 PDF | 无 |

#### 环境变量说明

```bash
# AI Provider 切换
AI_PROVIDER=xiaomi          # 使用小米 TokenPlan
# AI_PROVIDER=openai        # 使用 OpenAI API

# 小米 TokenPlan（必须设置）
XIAOMI_API_KEY=tp-xxx       # Token（禁止硬编码，仅在 .env 中）
XIAOMI_API_BASE=https://token-plan-cn.xiaomimimo.com/anthropic
XIAOMI_MODEL=claude-3-5-sonnet-20241022

# CORS（必须设置，逗号分隔）
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8080
```

#### 自测清单

- [ ] 启动服务：`cd backend && uvicorn app.main:app --reload --port 8000`
- [ ] 访问 `http://localhost:8000/health` 确认服务正常
- [ ] 访问 `http://localhost:8000/ai-status` 确认 AI 配置正确
- [ ] 访问 `http://localhost:8000/docs` 查看 Swagger 文档
- [ ] 测试登录流程：`POST /api/v1/auth/send-code` → `POST /api/v1/auth/login`
- [ ] 测试上传试卷：`POST /api/v1/exams/upload`
- [ ] 测试确认分析：`POST /api/v1/exams/{id}/confirm`（触发 AI 分析）
- [ ] 测试生成题目：`POST /api/v1/practice/generate`（触发 AI 出题）
- [ ] 测试掌握度评估：`POST /api/v1/practice/{id}/submit` → `GET /api/v1/practice/{id}/assessment`
- [ ] 测试 PDF 生成：`POST /api/v1/pdf/generate` → `GET /api/v1/pdf/{id}/download`

---

## V1.0-frontend-integration — 2026-06-27

### 前后端联调对接

**目标**：前端 `service.ts` 与后端 API 格式完全对齐，支持 Mock/真实接口双模式无缝切换。

#### 格式对齐修复（6 处）

| # | 接口 | 问题 | 修复 |
|---|------|------|------|
| 1 | `POST /auth/login` | 后端返回 `{token, user_id, nickname, user_level}`，前端期望 `{token, user: {...}}` | `service.ts` login 函数增加响应格式转换 |
| 2 | `GET /students` | 后端返回 `{students: [...]}`，前端期望 `[...]` | `service.ts` getStudents 解包 `students` 数组 |
| 3 | `POST /exams/upload` | 后端期望 multipart/form-data 文件上传，前端原用 JSON | 改用 `uni.uploadFile` 发送 multipart 请求 |
| 4 | `GET /weaknesses` | 后端必须传 `student_id` 查询参数，返回 `{weaknesses: [...]}` | `service.ts` getWeaknesses 增加 studentId 参数并解包响应 |
| 5 | `POST/GET /chat/*` | 后端无 chat 端点 | 前端降级：sendChatMessage 返回固定提示，getChatHistory 返回空数组 |
| 6 | 页面层调用 | home/weakness 页面未传 studentId | 更新 `loadHomeData()` 和 `onMounted` 传入当前学生 ID |

#### 新增文件

- `docs/前端联调指南.md` — 完整联调文档，含启动命令、环境变量、接口清单、格式对齐说明

#### 切换模式

```bash
# Mock 模式（默认）
cd frontend && npm run dev:h5

# 真实接口模式
cd frontend && VITE_USE_MOCK=false npm run dev:h5
```

#### 联调验证结果

- ✅ 登录流程：`send-code` → `login` → token 存储 → 跳转首页
- ✅ 学生列表：从 store 加载，切换孩子刷新数据
- ✅ 试卷上传：multipart/form-data 格式正确发送
- ✅ 识别确认：题目列表展示 + 逐题修正 + 提交
- ✅ 诊断分析：薄弱点卡片展示 + 星级排序
- ✅ 薄弱点列表：student_id 参数传递 + 数据解包
- ✅ 在线答题：生成题目 → 答题 → 提交 → 掌握度评估
- ✅ Chat：降级为 mock 提示，不报错
- ⚠️ PDF：后端已实现，前端页面待 V1.1

---

## V1.0-frontend-tasks — 2026-06-27

### 前端修复任务清单完成（P0 + P1 全部）

依据 [前端修复任务清单](前端修复任务清单.md) 逐项修复：

#### P0 — 阻塞联调（6/6 完成）

| # | 任务 | 状态 |
|---|------|------|
| 1 | 创建 `.env` 文件，`VITE_USE_MOCK=false` | ✅ |
| 2 | Vite 开发代理 `/api` → `localhost:8000` | ✅ 已有 |
| 3 | `uploadExam` 真实上传（`uni.uploadFile`） | ✅ 已修 |
| 4 | `static/tab/` 8 个图标文件 | ✅ 已有 |
| 5 | 硬编码 `student_id: 's-001'`（3 处） | ✅ 已修 |
| 6 | 首页数据硬编码 → API 加载 + 切孩子刷新 | ✅ 已修 |

#### P1 — 联调后尽快修（6/6 完成）

| # | 任务 | 修复内容 |
|---|------|----------|
| 7 | "标记已掌握"按钮未调用 API | ✅ 已修（调用 `masterWeakness`） |
| 8 | chat 模块顶层异步调用 | ✅ 已修（移入 `onMounted`） |
| 9 | 全局错误处理 | ✅ `main.ts` 添加 `app.config.errorHandler` |
| 10 | 路由守卫 | ✅ `App.vue` `onLaunch` 检查 token，无 token 跳转登录 |
| 11 | 401 未清理 store | ✅ `api.ts` 401 时调用 `useUserStore().logout()` |
| 12 | practice 赋值错误 | ✅ 已修 |

#### 修改文件清单

| 文件 | 改动 |
|------|------|
| `frontend/.env` | **新增**，`VITE_USE_MOCK=false` |
| `frontend/src/main.ts` | 添加 `app.config.errorHandler` |
| `frontend/src/App.vue` | 添加路由守卫：`onLaunch` 检查登录状态 |
| `frontend/src/utils/api.ts` | 401 时调用 `useUserStore().logout()` 清理完整状态 |

#### 验收标准

- [x] `npm run dev:h5` 启动无编译错误
- [x] 未登录访问首页 → 自动跳转登录页
- [x] 输入手机号 + 888888 登录 → 跳转首页
- [x] 首页数据从 API 加载，非硬编码
- [x] 切换孩子 → 首页数据刷新
- [x] 上传试卷 → 确认识别 → 查看薄弱点，全流程走通
- [x] Token 过期（401）→ 清理 store → 跳转登录页

---

## V1.0-integration-audit — 2026-06-27

### 全链路联调审查 + 前端任务清单更新

对后端全部 17 个 API 进行实际调用测试，发现并记录前后端对接的所有断点。

#### 测试结果

| 测试项 | 状态 | 说明 |
|--------|------|------|
| 登录流程 | ✅ | send-code → login → token |
| 学生 CRUD | ✅ | create / list / update |
| 试卷上传 | ✅ | multipart/form-data 格式正确 |
| 识别结果 | ✅ | 含 mock 数据 |
| 确认识别 | ✅ | 触发 AI 分析（mock） |
| 薄弱点列表 | ✅ | 需 student_id 查询参数 |
| 薄弱点页面 | ❌ | `student_id` 未注入 + 响应缺字段 |
| 孩子管理 | ❌ | 只有 toast 占位，未实现 |
| 出题 | ❌ | `student_id` 为 undefined |
| 首页 | ❌ | 硬编码 mock 数据 |
| 教师对话 | ❌ | 后端无接口，前端硬编码 |
| 标记已掌握 | ❌ | 按钮未调 API |

#### 根因分析

1. **`student_id` 断链**：后端 `GET /weaknesses` 不返回 `student_id` 字段，前端 `Weakness` 接口需要该字段，导致 `startPractice` 传 `undefined`
2. **孩子管理未实现**：`goStudentManage` 是 stub 函数
3. **首页未接 API**：`stats`/`recentExam`/`pendingWeaknesses` 全部硬编码
4. **chat 硬编码**：`student_id: 's-001'` 写死

#### 更新的文档

- [前端修复任务清单](前端修复任务清单.md) — 完全重写，从 15 个任务精简为按实际测试结果组织的 15 个任务，每个任务含具体的后端接口格式对照

---

## V1.0-ai-refactor-frontend — 2026-06-27

### 前端 AI 模型重构任务（3/3 完成）

依据 [AI模型重构任务清单](AI模型重构任务清单.md) 中的前端任务逐项实现：

| # | 任务 | 优先级 | 状态 | 说明 |
|---|------|--------|------|------|
| F-1 | 设置页重构 API 配置区域 | P0 | ✅ | 完整重写：AI 模式切换、平台选择（小米/DeepSeek/OpenAI）、API Key 输入、API 地址、通用/视觉模型下拉选择、测试连接、保存配置 |
| F-2 | API 测试功能 | P1 | ✅ | `service.ts` 新增 `getApiConfig`/`saveApiConfig`/`testApiConfig` 三个函数；设置页集成测试按钮 + 结果展示 |
| F-3 | 确保 subject 正确传递 | P1 | ✅ | `uploadExam` 已在 formData 中传递 `subject`，无需改动 |

#### 设置页新功能

```
🔑 API 配置
├── AI 模式：系统内置 / 自备 API Key（单选）
└── 自备模式下：
    ├── AI 平台：小米 TokenPlan / DeepSeek / OpenAI 兼容（标签选择）
    ├── API Key：密码输入 + 显隐切换
    ├── API 地址：自动填充平台默认地址
    ├── 通用模型：下拉选择（分析/出题/评估）
    ├── 图片识别模型：下拉选择（试卷识别）
    ├── [测试连接] → 调用 POST /settings/test-api → 显示成功/失败/响应时间
    └── [保存配置] → 调用 PUT /settings/api-config
```

#### 新增 service.ts 函数

| 函数 | 后端接口 | 说明 |
|------|----------|------|
| `getApiConfig()` | `GET /settings/api-config` | 获取当前用户 API 配置 |
| `saveApiConfig(config)` | `PUT /settings/api-config` | 保存 API 配置 |
| `testApiConfig(params)` | `POST /settings/test-api` | 测试 API Key + 模型是否可用 |

---

## V1.0-math-upload-fix — 2026-06-27

### 数学符号渲染 + 多图上传修复（前端 3/3 完成）

依据 [数学渲染与多图上传修复清单](数学渲染与多图上传修复清单.md) 中的前端任务逐项实现：

| # | 任务 | 优先级 | 状态 | 说明 |
|---|------|--------|------|------|
| F-1 | 新建 `utils/math.ts` LaTeX→Unicode 转换函数 | P0 | ✅ | 支持上标/下标/分数/根号/希腊字母/比较符号等 30+ 种 LaTeX 命令转换 |
| F-2 | 题目显示时调用 `latexToText()` | P0 | ✅ | `practice/index.vue`（题目+答案+解析）、`exam/confirm.vue`（题目）均已接入 |
| F-3 | 修改 `uploadExam` 支持多图上传 | P0 | ✅ | 改为两步流程：①逐张上传到 `/exams/upload-image` 获取 URL ②调用 `/exams/upload` 提交 URL 列表 |

#### 新增文件

- `frontend/src/utils/math.ts` — `latexToText(text)` 函数，处理 `$...$` 格式中的 LaTeX 命令，转换为 Unicode 数学符号

#### 修改文件

| 文件 | 改动 |
|------|------|
| `frontend/src/utils/service.ts` | `uploadExam` 重写：新增 `uploadSingleImage` 辅助函数，逐张上传 → 收集 URL → 提交试卷 |
| `frontend/src/pages/practice/index.vue` | 引入 `latexToText`，题目/答案/解析显示时转换 |
| `frontend/src/pages/exam/confirm.vue` | 引入 `latexToText`，题目显示时转换 |

#### 转换示例

| LaTeX 输入 | Unicode 输出 |
|------------|-------------|
| `$x \geq 6$` | `x ≥ 6` |
| `$x^2 + 1$` | `x² + 1` |
| `$\frac{1}{2}$` | `1/2` |
| `$\sqrt{x}$` | `√(x)` |
| `$x_1, x_2$` | `x₁, x₂` |
