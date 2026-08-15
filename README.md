# 智慧校园 AI 智能体助手

基于 **LangGraph + LangChain + Gradio + FastAPI** 的 AI 应用开发实习项目。系统面向校园场景提供 RAG 知识库问答、Agent 工具调用（天气、邮件、SQL 查询、翻译、计算器）、多模态图片识别（GLM-4V + YOLO）与多会话持久化，并配套测试、Docker 部署与流式 API。

> 本项目不包含任何密钥。所有敏感配置通过 `.env` 注入，仓库只提供 `.env.example`。

## 项目亮点

- **RAG 知识库问答**：文档解析（PDF/Word/Excel/TXT/Markdown）→ 切块 → SQLite FTS5 中文检索 → 可选向量重排（智谱 embedding-3），回答带来源引用
- **LangGraph Agent 编排**：显式图结构（检索 → 模型 → 工具循环），8 个可插拔工具，支持多轮历史恢复与失败降级
- **双后端存储**：未配置 MySQL 时自动使用 SQLite 演示模式，零配置即可本地运行；配置 MySQL 后自动切换，会话与知识库互不干扰
- **工程化交付**：FastAPI SSE 流式接口、Gradio 双 Tab 界面、pytest 单测、Docker Compose、GitHub Actions CI、初始化 SQL
- **安全加固**：LLM 生成 SQL 默认只读白名单、禁止多语句与系统表、计算器 AST 白名单求值、邮件失败返回真实错误

## 技术栈

| 层次 | 技术 |
------|------|
| 前端 | Gradio 6 |
| API | FastAPI + SSE |
| Agent | LangGraph + LangChain + LangChain-OpenAI |
| RAG | SQLite FTS5（trigram）+ 可选 OpenAI 兼容 Embedding |
| 大模型 | 智谱 GLM（OpenAI 兼容接口） |
| 数据库 | MySQL 8 / SQLite |
| 工程 | pytest、Docker、docker-compose、GitHub Actions |

## 架构总览

```
┌────────────────────────────────────────────────────────────┐
│                      接入层                                │
│   Gradio UI（/ui）           FastAPI（/api/*，SSE 流式）    │
├────────────────────────────────────────────────────────────┤
│                   服务层（app/services）                    │
│        会话恢复 → Agent 编排 → 结果持久化 → 引用返回          │
├────────────────────────────────────────────────────────────┤
│                   Agent 层（app/agent）                    │
│   LangGraph: retrieve → agent → tools 循环 → end            │
├────────────────────────────────────────────────────────────┤
│          RAG 层（app/rag）        工具层（app/tools）        │
│   解析 / 切块 / 索引 / 检索       天气 / 邮件 / SQL / 翻译    │
│   SQLite FTS5 + Embedding       计算器 / 校园数据            │
├────────────────────────────────────────────────────────────┤
│   基础设施（app/core、app/database、app/session）           │
│   配置 / 日志 / LLM 工厂 / MySQL-SQLite 双后端 / 会话持久化   │
└────────────────────────────────────────────────────────────┘
```

## 快速开始

### 方式一：演示模式（无需任何密钥）

未配置 `.env` 或只配置部分项时，应用自动使用 SQLite 与演示模型运行，知识库会自动载入 `knowledge_base/` 下的示例文档。

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python main.py
```

访问 `http://127.0.0.1:8000`（自动跳转 `/ui`），API 文档在 `http://127.0.0.1:8000/api/docs`。

只启动 Gradio 界面：

```bash
python gradio_app.py
```

### 方式二：完整模式（LLM + MySQL）

1. 复制环境模板并填写：`cp .env.example .env`
2. 初始化数据库：`mysql -u root -p < scripts/init_db.sql`
3. 在 `.env` 中填写 `zhipuai_api_key` 与 MySQL 连接信息，并将 `DEMO_MODE` 设为 `0`
4. 启动：`python main.py`

### 方式三：Docker Compose

```bash
docker compose up --build
```

Compose 会启动 MySQL 并执行初始化脚本，应用监听 `8000` 端口。

## API 概览

| 方法 | 路径 | 说明 |
------|------|------|
| POST | `/api/chat` | SSE 流式对话（token / done / error） |
| GET | `/api/health` | 健康检查：LLM、数据库、RAG 索引 |
| GET / POST / DELETE | `/api/sessions` | 会话列表、创建、删除 |
| GET | `/api/sessions/{id}/messages` | 会话历史消息 |
| POST | `/api/rag/documents` | 上传文档入库 |
| GET / DELETE | `/api/rag/documents` | 文档列表 / 删除 |
| POST | `/api/rag/search` | 知识库检索测试 |
| POST | `/api/rag/seed` | 初始化示例知识库 |

SSE 事件示例：

```text
data: {"type": "start", "session_id": "..."}
data: {"type": "token", "content": "图书馆"}
data: {"type": "done", "answer": "...", "sources": ["campus_guide.md"]}
```

## 项目结构

```text
app/
  core/        配置、日志、错误、LLM 工厂
  rag/         文档解析、切块、存储、检索、入库
  agent/       LangGraph 编排
  services/    对话服务
  api/         FastAPI 路由与组装
  tools/       Agent 工具（含安全校验）
  session.py   会话持久化
  ui.py        Gradio 界面
knowledge_base/  示例知识库文档
scripts/init_db.sql   MySQL 初始化脚本
tests/         pytest 测试
```

## 安全设计

- 密钥只从环境变量读取，`.env` 已被 gitignore
- SQL 工具默认只读：仅允许 `SELECT` / `WITH`，拦截多语句、注释绕过、系统库与危险函数
- 计算器使用 AST 节点白名单求值，禁用 `eval`
- 邮件工具校验收件人格式，失败时返回真实错误，不再伪装成功
- 检索查询经 FTS5 安全短语包装，避免特殊字符注入

## 测试

```bash
python -m pytest -q
```

测试覆盖计算器安全、SQL 白名单、RAG 切块与检索、会话持久化、Agent 流式与非流式对话、FastAPI 接口。

## 简历项目描述

可直接用于简历与面试准备的版本见 [docs/RESUME_PROJECT.md](docs/RESUME_PROJECT.md)，架构细节见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。
