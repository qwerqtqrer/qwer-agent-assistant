"""Gradio 对话函数回归测试：发送后清空已上传文档，避免重复入库。"""

from app.chat import chat_fn
from app.services import ChatResult


def test_chat_fn_clears_uploaded_file(monkeypatch, tmp_path):
    doc = tmp_path / "guide.md"
    doc.write_text("图书馆开放时间为 9:00 至 17:00。", encoding="utf-8")

    class _FakeService:
        def run(self, session_id, message, use_rag=True):
            return ChatResult(
                session_id=session_id or "fake-session",
                answer="好的",
                sources=["guide.md"],
            )

    monkeypatch.setattr("app.chat.chat_service", _FakeService())
    result = chat_fn("你好", None, None, [], None, str(doc))
    assert result[7] is None
    assert result[3][-1]["content"] == "好的"
