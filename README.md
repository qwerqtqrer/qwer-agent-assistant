# 智慧校园 AI 智能体助手

使用 **LangGraph 显式编排 Agent 闭环**，集成 **RAG 混合检索**、**GLM-4V 图片理解**、**YOLO 目标检测**、**FastAPI SSE 流式接口**、**Gradio 可视化界面**与 **MySQL/SQLite 双后端**。它不是一个单一模型 Demo，而是一套可部署、可扩展、具备安全边界的 AI 应用工程。

---

## 项目简介

本项目面向校园业务场景，提供一个多功能 AI 智能体：

- 基于本地知识库回答校园问题，答案自动引用来源文档
- 通过 Agent 工具调用获取天气、课程、成绩、通知等实时数据
- 支持上传图片/拍照，图片直接显示在会话气泡中，识别结果作为模型上下文
- 支持多会话持久化、历史恢复、SSE 流式输出与 Docker 部署

项目核心不依赖单一模型，而是把「检索 → 推理 → 工具调用 → 再次推理」组织成可观测的 LangGraph 状态机，覆盖了 AI 应用开发中最关键的工程链路。

---

## 核心亮点

- **LangGraph 显式 Agent 编排**：`retrieve → agent → tools → agent` 循环，8 个可插拔工具（天气、邮件、SQL 查询、课程、成绩、通知、翻译、计算器），工具结果回流模型继续决策
- **完整 RAG 管线**：PDF/Word/Excel/TXT/Markdown 解析、段落切块与重叠、SQLite FTS5 trigram 中文检索、可选智谱 embedding 向量重排、答案来源引用
- **多模态输入**：图片直接展示在聊天记录中，GLM-4V 生成图片理解、YOLO 做目标检测，识别结果只进入模型上下文，不污染用户界面
- **双后端持久化**：未配置 MySQL 时自动切换 SQLite 演示模式，配置后无缝切换 MySQL，会话与知识库独立存储
- **流式 API + UI 双入口**：FastAPI SSE 事件流（start/token/done/error）与 Gradio 共用同一服务层，避免双份业务逻辑
- **安全工程实践**：LLM 生成 SQL 默认只读、危险关键字与多语句拦截、计算器 AST 白名单、邮件收件人校验、密钥全部通过 `.env` 注入
- **工程化交付**：Docker Compose 一键拉起 MySQL + 应用，GitHub Actions 语法检查，含简历面试版项目描述文档

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 接入层 | Gradio 6、FastAPI、SSE、OpenAPI |
| Agent | LangGraph、LangChain、LangChain-OpenAI |
| RAG | SQLite FTS5（trigram）、智谱 embedding-3、pdfplumber / python-docx / openpyxl |
| 多模态 | 智谱 GLM-4V、Ultralytics YOLO、OpenCV |
| 存储 | MySQL 8、SQLite |
| 部署 | Docker、docker-compose、GitHub Actions |
| 配置 | pydantic-settings、python-dotenv |

---

## 功能一览

- RAG 知识库问答：文档上传、示例知识库初始化、删除/恢复、检索测试
- Agent 工具调用：实时天气、校园课程/成绩/通知查询、SQL 只读查询、翻译、计算器、邮件发送
- 多模态会话：上传图片或拍照后图片展示在聊天气泡，GLM-4V 与 YOLO 结果作为模型上下文
- 会话管理：新建、切换、删除、历史恢复
- 开发者 API：SSE 流式对话、会话 CRUD、知识库 CRUD、健康检查

---

## 快速开始

### 环境要求

- Python 3.10+
- 可选：MySQL 8、Docker

### 方式一：演示模式（无需任何密钥）

```bash
python -m pip install -r requirements.txt
python main.py
```

访问 `http://127.0.0.1:8000`（自动跳转 `/ui`），API 文档在 `http://127.0.0.1:8000/api/docs`。

只启动 Gradio 界面：

```bash
python gradio_app.py
```

### 方式二：完整模式（LLM + MySQL）

1. 复制环境模板：`cp .env.example .env`（Windows 使用 `copy .env.example .env`）
2. 在 `.env` 中填写 `zhipuai_api_key`，配置 MySQL 连接，并将 `DEMO_MODE` 设为 `0`
3. 初始化数据库：`mysql -u root -p < scripts/init_db.sql`
4. 启动应用：`python main.py`

### 方式三：Docker Compose

```bash
docker compose up --build
```

Compose 会自动启动 MySQL、执行初始化 SQL、挂载数据目录并运行应用。

---

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | SSE 流式对话（start / token / done / error） |
| GET | `/api/health` | 健康检查：LLM、数据库、RAG 索引 |
| GET / POST / DELETE | `/api/sessions` | 会话列表、创建、删除 |
| GET | `/api/sessions/{id}/messages` | 会话历史消息 |
| POST | `/api/rag/documents` | 上传文档入库 |
| GET / DELETE | `/api/rag/documents` | 文档列表 / 删除 |
| POST | `/api/rag/search` | 知识库检索测试 |
| POST | `/api/rag/seed` | 初始化示例知识库 |
| POST | `/api/rag/restore` | 恢复被删除的示例文档 |

SSE 事件示例：

```text
data: {"type": "start", "session_id": "..."}
data: {"type": "token", "content": "图书馆"}
data: {"type": "done", "answer": "...", "sources": ["campus_guide.md"]}
```

---

## 项目结构

```text
app/
  core/        配置、日志、错误、LLM 工厂
  rag/         文档解析、切块、索引、检索、入库
  agent/       LangGraph Agent 编排
  services/    对话服务与持久化
  api/         FastAPI 路由与组装
  tools/       Agent 工具（含安全校验）
  ui.py        Gradio 界面
  bootstrap.py 启动引导与存储初始化
main.py        FastAPI + Gradio 统一入口
gradio_app.py  Gradio 独立入口
yolo_info.py   YOLO 目标检测封装
knowledge_base/  示例知识库文档
scripts/init_db.sql  MySQL 初始化脚本
```

---

## 架构简述

```text
Gradio UI ─┐
           ├─ ChatService → LangGraph → RAG 检索 → LLM → 工具循环 → 回答
FastAPI ───┘
                │
                └─ MySQL / SQLite（会话历史 + 知识库索引）
```

- `retrieve`：根据用户问题检索知识库，写入 RAG 上下文
- `agent`：模型结合上下文决定直接回答或调用工具
- `tools`：ToolNode 执行工具并回传结果，循环直到模型不再产生工具调用

未配置 LLM 时，系统自动使用确定性 `DemoChatModel`，Agent 图与 RAG 流程仍可完整运行，便于离线演示和接口自检。

---

## 注意事项

- 演示模式不会真正调用大模型和外部工具，只会基于本地知识库和固定规则作答；要完整体验 Agent 能力，必须配置 `zhipuai_api_key`。
- `.env` 已被 `.gitignore` 排除，仓库只提交 `.env.example`。上传 GitHub 前不要提交真实密钥，部署环境也建议使用密钥管理服务。
- 当 `DEMO_MODE=0` 时，应用必须能连接到已初始化的 MySQL，否则启动会直接报错；本地没有 MySQL 时请保持 `DEMO_MODE=1`。
- LLM 生成的 SQL 默认只读（仅允许 SELECT / WITH），DML 需要显式开启；SQL 执行前会经过多语句、危险关键字与系统库拦截。
- YOLO 模型文件（如 `yolo11n.pt`）不在仓库中，需要自行放置到项目根目录或通过 `YOLO_MODEL_PATH` 配置；缺失时自动跳过目标检测。
- 文档上传支持 PDF/Word/Excel/TXT/Markdown，单文件上限 50MB。
- Docker Compose 中 `DB_PASSWORD` 的默认值只用于本地开发，部署时务必通过 `.env` 设置强密码。
- 会话与知识库数据默认写入 `data/`，该目录已被 gitignore；需要长期保留时请自行备份。

---

## 面向面试官的说明

这个项目体现的能力不只是「调用一次大模型」，而是：

- 能把 LLM 应用拆成可维护的分层架构，并保持 UI、API、服务层逻辑复用
- 能设计并实现 RAG、工具调用、多模态输入等真实业务链路
- 能处理持久化、流式传输、并发访问、错误降级等工程问题
- 具备安全意识，在 LLM 生成代码、SQL、文件上传等场景主动加防护

简历项目描述见 [docs/RESUME_PROJECT.md](docs/RESUME_PROJECT.md)，架构细节见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。
