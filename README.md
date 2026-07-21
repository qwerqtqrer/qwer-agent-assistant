# 智慧校园 AI 智能体助手

基于 **LangChain + Gradio** 构建的多功能 AI Agent 应用，集成大语言模型（GLM）、RAG、多模态识别、自然语言转 SQL 等能力，提供一站式的校园场景智能交互体验。

## 项目亮点

- **AI Agent 架构** — 基于 LangChain 的 ReAct Agent，具备工具调用、多轮对话记忆、动态推理能力
- **自然语言驱动的功能编排** — 用户通过自然语言触发天气查询、邮件发送、数据库查询等操作，由 LLM 自主决策工具调用链
- **多模态输入支持** — 集成 GLM-4V 视觉模型与 YOLO 目标检测，支持图片理解与拍照识别
- **模块化工程体系** — 清晰的分层架构（UI → 业务 → Agent → 工具 → 基础设施），低耦合、易扩展

## 核心能力

| 能力 | 技术实现 | 场景 |
|------|----------|------|
| AI Agent 对话 | LangChain Agent + ReAct + InMemorySaver | 智能问答、任务编排 |
| 自然语言 → SQL | ChatOpenAI 调用 GLM 生成 SQL | 查询课程、成绩、通知 |
| 图片理解 | GLM-4V 多模态模型 | 识别图片内容 |
| 目标检测 | YOLO | 图片中物体检测 |
| 文档解析 | pdfplumber / python-docx / openpyxl | PDF、Word、Excel 内容提取 |
| 天气查询 | 实时天气与出行建议 |
| 邮件发送 | QQ SMTP (SSL) | 发送文本邮件 |
| 翻译 / 计算器 | LLM 调用 + 安全沙箱 | 多语言翻译、数学计算 |
| 多会话管理 | MySQL 持久化 | 会话创建、切换、删除、历史消息回溯 |

## 后端工程体系

### 分层架构

```
┌──────────────────────────────────────────┐
│            UI 层 (app/ui.py)             │
│     Gradio 组件布局 + 事件绑定            │
├──────────────────────────────────────────┤
│         业务层 (app/chat.py)             │
│     对话流程编排、输入预处理、状态管理      │
├──────────────────────────────────────────┤
│        Agent 层 (app/agent_setup.py)      │
│    LangChain Agent + LLM + 记忆 + 工具    │
├──────────────────────────────────────────┤
│          工具层 (app/tools/*)             │
│    @tool 装饰器注册，每个工具独立模块       │
├──────────────────────────────────────────┤
│     基础设施层 (app/database.py 等)       │
│     MySQL 连接、文档解析、图片处理          │
├──────────────────────────────────────────┤
│         配置层 (app/config.py)            │
│     基于 .env 的统一配置管理               │
└──────────────────────────────────────────┘
```

### 工程特性

- **配置与代码分离** — 密钥、API Key 等敏感信息统一由 `.env` 管理，不侵入代码
- **延迟加载** — 重型依赖（pdfplumber, ZhipuAI SDK）在调用时按需导入，优化启动速度
- **安全防护** — SQL 参数化查询防注入、计算器正则白名单 + 沙箱、SQL 语句正则校验
- **可扩展设计** — 新增工具只需创建一个模块 + 在 `tools/__init__.py` 注册一行即可接入 Agent
- **幂等初始化** — 数据库建表使用 `IF NOT EXISTS`，重复启动安全

## 快速开始

### 环境要求

- Python 3.9+
- MySQL 8.0+

### 安装

```bash
pip install -r requirements.txt
```

### 配置

创建 `.env` 文件，填写以下配置项：

```ini
# 智谱 AI（必填）
zhipuai_api_key=your_api_key_here
zhipuai_base_url=https://open.bigmodel.cn/api/paas/v4

# MySQL（必填）
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here

# QQ 邮箱 SMTP（选填）
MAIL_HOST=smtp.qq.com
MAIL_USER=you@qq.com
MAIL_PASS=your_smtp_auth_code

# 高德地图 API（选填）
AMAP_API_KEY=your_amap_key_here
```

### 启动

```bash
python main.py
```

启动后浏览器访问 `http://127.0.0.1:7860` 即可使用。

## 数据流

```
用户输入（文本/图片/文档）
        │
        ▼
app/ui.py ──► app/chat.py ──► 预处理（图片识别 / YOLO / 文档解析）
                                   │
                                   ▼
                            app/agent_setup.py (Agent 推理)
                                   │
                                   ▼
                            app/tools/*（工具执行）
                                   │
                                   ▼
                            返回结果 ──► 存入 MySQL ──► 更新 UI
```
