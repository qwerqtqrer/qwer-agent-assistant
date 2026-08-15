# 架构设计说明

## 1. 分层设计

项目按「接入层 → 服务层 → Agent 层 → RAG/工具层 → 基础设施层」组织，层与层之间通过 Python 包边界解耦。

- 接入层：`app/ui.py`（Gradio）、`app/api/`（FastAPI），共享同一个 `ChatService`
- 服务层：`app/services/chat.py` 负责会话创建、历史恢复、Agent 调用、结果持久化
- Agent 层：`app/agent/graph.py` 使用 LangGraph 显式编排节点与边
- RAG 层：`app/rag/` 提供解析、切块、索引、检索、入库
- 工具层：`app/tools/` 每个工具一个模块，统一注册到 `ALL_TOOLS`
- 基础设施层：`app/core/`（配置/日志/LLM 工厂）、`app/database.py`（双后端）、`app/session.py`

## 2. Agent 图

```
START → retrieve → agent ──有工具调用──→ tools ──→ agent
                      │
                      └──无工具调用──→ END
```

- `retrieve`：取最近一条用户消息，调用 RAG 检索并把上下文写入 state
- `agent`：系统提示词携带 RAG 上下文，模型决定是直接回答还是调用工具
- `tools`：`ToolNode` 执行工具并回传结果，循环直到模型不再产生工具调用

未配置 LLM 时，`app/core/llm.py` 返回确定性 `DemoChatModel`，图仍可运行，便于离线演示和 CI。

## 3. RAG 流程

1. 文档上传（Gradio 或 `/api/rag/documents`）
2. `parse_document` 按扩展名解析为纯文本
3. `split_text` 按段落合并、长段按句拆分，生成带重叠的 chunk
4. `RagStore.add_document` 写入 SQLite，FTS5 虚拟表通过触发器同步
5. 配置了向量服务时，chunk 同时保存 embedding 向量
6. 检索时先做 FTS5 中文检索，向量可用时再按余弦相似度重排，合并去重

SQLite FTS5 使用 `trigram` tokenizer，配合查询拆分为三元组 OR 表达式，中文短查询也能召回。

## 4. 双后端数据库

`config.is_demo_mode` 决定后端：

- 演示模式：SQLite（`data/app.sqlite3`），无外部依赖
- 生产模式：MySQL 8，表名带 `DB_DATABASE` 前缀

内部 SQL 统一使用 `%s` 占位符，`app/database.py` 在 SQLite 下自动转换为 `?`，上层代码无需关心后端差异。

## 5. 流式协议

`POST /api/chat` 返回 `text/event-stream`，事件类型：

- `start`：会话开始，携带 `session_id`
- `token`：模型增量输出
- `error`：Agent 调用失败
- `done`：结束，携带最终答案、引用来源与工具调用次数

Gradio 界面的知识库 Tab 与 API 共用同一套 RAG 服务，避免逻辑重复。
