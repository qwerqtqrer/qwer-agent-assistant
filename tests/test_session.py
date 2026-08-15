"""会话持久化（SQLite 演示模式）测试。"""

from app.session import (
    create_session,
    delete_session,
    init_tables,
    load_messages,
    load_sessions,
    rename_session,
    save_message,
)


def test_session_lifecycle():
    init_tables()
    session_id = create_session("初始标题")
    save_message(session_id, "user", "你好")
    save_message(session_id, "assistant", "你好！")

    messages = load_messages(session_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"

    rename_session(session_id, "新标题")
    sessions = load_sessions()
    session = next(item for item in sessions if item["id"] == session_id)
    assert session["title"] == "新标题"

    delete_session(session_id)
    assert load_messages(session_id) == []
