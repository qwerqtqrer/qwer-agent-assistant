"""Agent 编排与对话服务测试（演示模型 + RAG）。"""

from app.rag import ensure_knowledge_base
from app.services import chat_service


def test_rag_chat_returns_sources():
    ensure_knowledge_base()
    result = chat_service.run(None, "图书馆周末几点关门？")
    assert result.session_id
    assert result.answer
    assert "guide.md" in result.sources


def test_stream_returns_done_event():
    ensure_knowledge_base()
    events = list(chat_service.stream(None, "图书馆周末几点关门？"))
    assert events[-1]["type"] == "done"
    assert events[-1]["sources"] == ["guide.md"]
