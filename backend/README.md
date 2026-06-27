# ScoreForge Backend

基于 FastAPI 的后端服务。

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

### 3. 启动 PostgreSQL 和 Redis

```bash
# 使用 Docker
docker run -d --name postgres -e POSTGRES_DB=scoreforge -e POSTGRES_USER=scoreforge -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:16-alpine
docker run -d --name redis -p 6379:0 redis:7-alpine
```

### 4. 运行数据库迁移

```bash
alembic upgrade head
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
backend/
├── app/
│   ├── api/           # API 路由
│   │   ├── v1/        # API v1 版本
│   │   └── deps.py    # 依赖注入
│   ├── core/          # 核心模块
│   │   ├── config.py  # 配置管理
│   │   ├── database.py # 数据库连接
│   │   ├── redis.py   # Redis 连接
│   │   ├── security.py # JWT、加密
│   │   └── exceptions.py # 自定义异常
│   ├── models/        # SQLAlchemy ORM 模型
│   ├── schemas/       # Pydantic 请求/响应模型
│   ├── services/      # 业务逻辑服务
│   │   ├── ai_service.py    # AI 调用服务
│   │   ├── ocr_service.py   # OCR 识别服务
│   │   └── pdf_service.py   # PDF 生成服务
│   └── main.py        # FastAPI 应用入口
├── alembic/           # 数据库迁移
├── requirements.txt   # Python 依赖
└── .env.example       # 环境变量示例
```

## API 接口

### P0 接口（已实现）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/send-code` | POST | 发送短信验证码 |
| `/api/v1/auth/login` | POST | 手机号登录/注册 |
| `/api/v1/students` | GET | 获取孩子列表 |
| `/api/v1/students` | POST | 创建孩子档案 |
| `/api/v1/students/{id}` | PUT | 更新孩子档案 |
| `/api/v1/exams/upload` | POST | 上传试卷照片 |
| `/api/v1/exams/{id}/recognition` | GET | 获取 AI 识别结果 |
| `/api/v1/exams/{id}/confirm` | POST | 家长确认/修正识别结果 |
| `/api/v1/exams/{id}/analysis` | GET | 获取薄弱点分析结果 |
| `/api/v1/weaknesses` | GET | 获取薄弱点列表 |
| `/api/v1/weaknesses/{id}/master` | POST | 标记为已掌握 |
| `/api/v1/practice/generate` | POST | 生成练习题 |
| `/api/v1/practice/{id}/questions` | GET | 获取题目列表 |
| `/api/v1/practice/{id}/submit` | POST | 提交做题结果 |
| `/api/v1/practice/{id}/assessment` | GET | 获取掌握度评估 |
| `/api/v1/pdf/generate` | POST | 生成 PDF |
| `/api/v1/pdf/{id}/download` | GET | 下载 PDF |

### 开发模式

- 验证码固定为 `888888`
- AI 服务未配置时返回 mock 数据
- OCR 服务未安装时返回 mock 数据
