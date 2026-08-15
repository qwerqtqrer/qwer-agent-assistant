"""Agent 编排与对话服务测试（演示模型 + RAG）。"""

from langchain_core.messages import AIMessage, AIMessageChunk

from app.rag import ensure_knowledge_base
from app.services import ChatService, chat_service


def test_rag_chat_returns_sources():
    ensure_knowledge_base()
    result = chat_service.run(None, "图书馆周末几点关门？")
    assert result.session_id
    assert result.answer
    assert "guide.md" in result.sources


def test_stream_returns_done_event():
    ensure_knowledge_base()
    events = list(chat_service.stream(None, "图书馆周末几点关门？"))
    assert any(event["type"] == "token" for event in events)
    assert events[-1]["type"] == "done"
    assert events[-1]["sources"] == ["guide.md"]


def test_run_without_rag_returns_no_sources():
    ensure_knowledge_base()
    result = chat_service.run(None, "图书馆周末几点关门？", use_rag=False)
    assert result.answer
    assert result.sources == []


class _TooledFakeAgent:
    """模拟已执行工具但未产出文字 token 的 Agent，用于回归测试。"""

    def __init__(self):
        self.invoke_calls = 0

    def stream(self, state, stream_mode=None):
        yield ("messages", (AIMessageChunk(content=""), {}))
        yield (
            "updates",
            {
                "tools": {"messages": [AIMessage(content="")]},
                "agent": {"messages": [AIMessage(content="处理完成，未重复执行工具")]},
            },
        )

    def invoke(self, state):
        self.invoke_calls += 1
        return {"messages": [AIMessage(content="不应走这里")], "sources": []}


def test_stream_does_not_reinvoke_after_tool_steps():
    fake = _TooledFakeAgent()
    service = ChatService(agent=fake)
    events = list(service.stream(None, "执行一次"))
    assert fake.invoke_calls == 0
    assert events[-1]["type"] == "done"
    assert "未重复执行工具" in events[-1]["answer"]
    assert events[-1]["tool_steps"] == 1


class _NoTokenFakeAgent:
    """模拟无工具、无 token 的 Agent，验证安全兜底路径。"""

    def __init__(self):
        self.invoke_calls = 0

    def stream(self, state, stream_mode=None):
        yield ("messages", (AIMessageChunk(content=""), {}))

    def invoke(self, state):
        self.invoke_calls += 1
        return {"messages": [AIMessage(content="兜底答案")], "sources": []}


def test_stream_fallback_only_without_tool_steps():
    fake = _NoTokenFakeAgent()
    service = ChatService(agent=fake)
    events = list(service.stream(None, "你好"))
    assert fake.invoke_calls == 1
    assert events[-1]["type"] == "done"
    assert "兜底答案" in events[-1]["answer"]
