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
