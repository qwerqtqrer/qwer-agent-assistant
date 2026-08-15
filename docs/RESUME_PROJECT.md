# 简历项目描述：智慧校园 AI 智能体助手

## 一句话版本

基于 LangGraph 与 RAG 的校园场景 AI 智能体应用，提供知识库问答、工具调用、多模态识别与流式 API，覆盖从模型编排到测试部署的完整工程链路。

## 技术栈

Python、LangChain、LangGraph、Gradio、FastAPI、SQLite FTS5、MySQL、智谱 GLM、YOLO、pytest、Docker

## 项目背景

面向校园用户的多功能 AI 助手，需要把大模型对话能力与真实业务数据（天气、邮件、校园数据库、知识文档）结合起来，并保证应用可演示、可部署、可测试。

## 核心工作

- 使用 LangGraph 构建「检索 → 模型 → 工具循环」显式 Agent 图，注册 8 个可插拔工具，支持多轮会话恢复
- 实现完整 RAG 管线：PDF/Word/Excel/TXT/Markdown 解析、分段切块、SQLite FTS5 中文索引、可选向量重排、答案来源引用
- 开发 FastAPI 服务，提供 SSE 流式对话、会话管理、知识库管理与健康检查接口，Gradio 界面与 API 复用同一服务层
- 设计 MySQL/SQLite 双后端：无配置时零依赖演示模式，配置后自动切换 MySQL，会话与知识库数据持久化
- 加固工具安全：LLM 生成 SQL 只读白名单、多语句与系统表拦截、计算器 AST 白名单求值、邮件失败真实反馈
- 配套工程设施：pytest 单测、GitHub Actions CI、Docker Compose 一键部署、MySQL 初始化脚本与示例知识库

## 结果与亮点

- 零配置启动即可演示 RAG 问答，内置 4 份示例知识库文档
- 8 个 Agent 工具、15+ 条 SQL 危险关键字拦截规则、双数据库后端
- 20+ 测试用例覆盖安全、检索、会话、Agent 与 API
- Docker Compose 一条命令拉起 MySQL + 应用
- 所有密钥通过 `.env` 注入，仓库不含任何隐私配置

## 面试高频问题

### 为什么用 LangGraph 而不是直接调模型？

直接调模型只能完成单轮问答，无法自主决定调用哪些工具、无法把检索和工具执行编排成可靠流程。LangGraph 用显式状态机和节点表达「检索 → 决策 → 执行工具 → 再决策」的循环，工具执行结果会回到模型上下文，过程可观测、可测试。

### RAG 检索为什么选择 SQLite FTS5？

中文场景下需要本地可运行、无外部服务的检索方案。SQLite FTS5 的 trigram tokenizer 对中文子串有较好召回，配合查询拆分为三元组 OR 表达式，短查询也能命中；配置了智谱 embedding 后自动叠加向量重排，形成混合检索。

### 如何防止 LLM 生成的 SQL 破坏数据？

三层防护：默认只读模式仅允许 SELECT/WITH；关键字与多语句黑名单在 SQL 执行前校验；系统库、危险函数（SLEEP、BENCHMARK 等）与注释绕过均被拦截。生成 SQL 会随结果一起展示，方便审计。

### 演示模式是如何实现的？

未配置密钥时自动启用 SQLite 与确定性 DemoChatModel，Agent 图仍然完整运行，RAG 与持久化功能可离线演示；配置真实 LLM 后无需改代码即可切换到完整工具调用。
