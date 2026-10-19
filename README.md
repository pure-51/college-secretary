# 大学生秘书智能助手

一个面向大学生日常事务管理的本地优先智能助手：把群消息、通知、政策文件和课程材料集中到一处，用 LLM 完成分类、提取、归档与问答，所有数据保存在本机。

- 前端：Flutter（Windows / macOS / Linux / Android / iOS / Web）
- 后端：Python FastAPI + SQLite
- 模型：任意 OpenAI 兼容接口（默认 DeepSeek）
- 新增数据默认写入本机，后端只监听 `127.0.0.1`

---

## 功能

| 模块 | 说明 |
|---|---|
| **收件箱** | 导入群消息、图片或链接，自动分类并提取待办、考试安排；确认后归档 |
| **知识库** | 上传 PDF / Word 政策文件，支持全文检索、原文引用问答与新旧版本对比 |
| **日程** | 汇总待办与考试，提供日历视图 |
| **生涯档案官** | 材料归档、证据链追溯、简历生成，每一行内容都可回溯到原材料 |
| **科研论文库** | 论文导入、元数据提取、摘要与综述辅助 |
| **班务助理** | 通知文案生成、接龙/报名统计、活动台账与月度简报 |
| **AI 汇报** | 主动生成今日简报、待办汇总与提醒 |
| **AI 咨询** | 基于知识库的政策问答，回答附带原文出处 |
| **OCR** | 图片文字识别（EasyOCR），用于截图与票据 |
| **演示模式** | 一键载入虚构示例数据，可随时清空，便于体验与二次开发 |

## 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Flutter 3.44 / Dart 3.12、Provider |
| 后端 | FastAPI、SQLAlchemy 2（async）、Uvicorn |
| 数据库 | SQLite（aiosqlite） |
| 文档解析 | PyMuPDF、python-docx、BeautifulSoup |
| OCR | EasyOCR |
| 模型 | OpenAI 兼容 Chat Completions 接口 |

## 快速开始

### 环境要求

- Python 3.11+
- Flutter 3.44+（桌面端或 Web）
- 一个可用的 LLM API Key

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt

# 配置环境变量
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# 编辑 .env，至少填入 LLM_API_KEY
python run.py
```

后端默认运行在 `http://127.0.0.1:8002`，健康检查：`GET /api/health`。

首次启动会自动生成 `backend/data/local_token.txt`，前端通过 `/api/config` 获取本地令牌，后续请求自动携带 `X-Local-Token`。

### 2. 启动前端

```bash
cd frontend
flutter pub get
flutter run -d windows     # 或 chrome / macos / linux
```

前端默认连接 `http://127.0.0.1:8002`，可在 `lib/config/api_config.dart` 中修改。

## 配置

所有配置通过 `backend/.env` 或环境变量提供：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `LLM_API_KEY` | 空 | **必填**，模型 API Key |
| `LLM_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容接口地址 |
| `LLM_MODEL` | `deepseek-chat` | 模型名称 |
| `HOST` / `PORT` | `127.0.0.1` / `8002` | 后端监听地址 |
| `DATABASE_URL` | 本机 SQLite | 留空使用默认路径 |
| `OCR_ENABLED` | `true` | 是否启用 OCR |
| `LOCAL_TOKEN` | 自动生成 | 本地访问令牌 |
| `ENABLE_TOKEN` | `true` | 是否校验本地令牌 |
| `RATE_LIMIT_PER_MIN` | `60` | 每分钟请求上限 |
| `DEMO_MODE` | `false` | 演示模式开关 |

`.env` 已被 `.gitignore` 忽略，不会被提交。

## 演示模式

演示数据全部为虚构内容，用于快速体验各模块：

```bash
# 载入示例数据
curl -X POST http://127.0.0.1:8002/api/admin/seed

# 清空示例数据
curl -X POST http://127.0.0.1:8002/api/admin/clear

# 查看状态
curl http://127.0.0.1:8002/api/admin/demo-status
```

演示数据带有 `is_demo` 标记，清空时只删除这些记录，不影响正式数据。

## 测试

```bash
cd backend
pytest
```

测试使用 Mock LLM，不消耗 API 额度，也不需要真实 Key。

## 目录结构

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置
│   │   ├── database.py          # 数据库连接
│   │   ├── models/              # 数据模型
│   │   ├── routers/             # API 路由
│   │   ├── schemas/             # 请求/响应模型
│   │   ├── security/            # 令牌、脱敏、审计
│   │   ├── services/            # LLM、OCR、解析、检索、导出
│   │   └── seed_data/           # 演示数据
│   ├── tests/
│   ├── scripts/
│   ├── run.py
│   └── requirements.txt
├── frontend/
│   ├── lib/
│   │   ├── config/              # 主题与接口地址
│   │   ├── models/              # 数据模型
│   │   ├── providers/           # 状态管理
│   │   ├── services/            # API 封装
│   │   ├── pages/               # 页面
│   │   └── widgets/             # 通用组件
│   ├── test/
│   └── pubspec.yaml
├── docs/
│   ├── ADR/                     # 架构决策记录
│   └── 规划/                    # 功能与实现规划
├── requirements.txt
└── README.md
```

## 隐私与安全

- 后端默认只绑定 `127.0.0.1`，不接受外部连接
- 所有业务数据保存在本机 SQLite，不上传第三方
- 请求携带本地令牌，CORS 限制为 loopback
- 敏感字段（成绩、金额、证件号、手机号等）在传输前可配置脱敏
- `.env`、数据库、上传文件、构建产物均已加入 `.gitignore`

调用 LLM 时，相关文本会发送到你在 `LLM_BASE_URL` 中配置的服务商。若处理的是真实个人材料，请自行评估服务商的数据政策。

## 许可证

[MIT](LICENSE)
