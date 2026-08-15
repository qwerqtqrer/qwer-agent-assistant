"""数据库持久化会话管理（MySQL / SQLite 双后端）。"""

import uuid

from app.core.config import config
from app.database import execute_query_raw, execute_update

SESSIONS_TABLE = "chat_sessions"
MESSAGES_TABLE = "chat_messages"


def _table(name: str) -> str:
    if config.is_demo_mode:
        return name
    return f"{config.db_database}.{name}"


def _auto_increment() -> str:
    return "AUTOINCREMENT" if config.is_demo_mode else "AUTO_INCREMENT"


def init_tables():
    execute_update(
        f"""
        CREATE TABLE IF NOT EXISTS {_table(SESSIONS_TABLE)} (
            id VARCHAR(64) PRIMARY KEY,
            title VARCHAR(200) NOT NULL DEFAULT '新会话',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
        """
    )
    execute_update(
        f"""
        CREATE TABLE IF NOT EXISTS {_table(MESSAGES_TABLE)} (
            id INTEGER PRIMARY KEY {_auto_increment()},
            session_id VARCHAR(64) NOT NULL,
            role VARCHAR(20) NOT NULL,
            content TEXT,
            extra_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def load_sessions():
    """返回所有会话列表（最新在前）。"""
    rows = execute_query_raw(
        f"SELECT id, title FROM {_table(SESSIONS_TABLE)} ORDER BY COALESCE(updated_at, created_at) DESC"
    )
    return [{"id": row[0], "title": row[1]} for row in rows]


def create_session(title: str = "新会话"):
    sid = str(uuid.uuid4())
    execute_update(
        f"INSERT INTO {_table(SESSIONS_TABLE)} (id, title) VALUES (%s, %s)",
        (sid, title),
    )
    return sid


def delete_session(session_id: str):
    execute_update(
        f"DELETE FROM {_table(MESSAGES_TABLE)} WHERE session_id = %s",
        (session_id,),
    )
    execute_update(
        f"DELETE FROM {_table(SESSIONS_TABLE)} WHERE id = %s",
        (session_id,),
    )


def rename_session(session_id: str, title: str):
    execute_update(
        f"UPDATE {_table(SESSIONS_TABLE)} SET title = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (title, session_id),
    )


def load_messages(session_id: str):
    """载入某会话所有历史消息（时间正序）。"""
    rows = execute_query_raw(
        f"SELECT role, content, extra_json FROM {_table(MESSAGES_TABLE)} "
        "WHERE session_id = %s ORDER BY id ASC",
        (session_id,),
    )
    return [
        {"role": row[0], "content": row[1] if row[1] else ""}
        for row in rows
    ]


def save_message(session_id: str, role: str, content: str, extra_json=None):
    execute_update(
        f"INSERT INTO {_table(MESSAGES_TABLE)} (session_id, role, content, extra_json) "
        "VALUES (%s, %s, %s, %s)",
        (session_id, role, content, extra_json),
    )
