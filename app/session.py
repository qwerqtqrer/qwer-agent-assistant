"""数据库持久化会话管理"""

import uuid

from app.database import execute_update, execute_query_raw

SESSIONS_TABLE = "oa_demo.chat_sessions"
MESSAGES_TABLE = "oa_demo.chat_messages"


def init_tables():
    execute_update(f"""
        CREATE TABLE IF NOT EXISTS {SESSIONS_TABLE} (
            id VARCHAR(64) PRIMARY KEY,
            title VARCHAR(200) NOT NULL DEFAULT '新会话',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    execute_update(f"""
        CREATE TABLE IF NOT EXISTS {MESSAGES_TABLE} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(64) NOT NULL,
            role VARCHAR(20) NOT NULL,
            content TEXT,
            extra_json TEXT COMMENT '图片路径等附加信息',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session (session_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


def load_sessions():
    """返回所有会话列表（最新在前）"""
    rows = execute_query_raw(
        f"SELECT id, title FROM {SESSIONS_TABLE} ORDER BY updated_at DESC"
    )
    return [{"id": row[0], "title": row[1]} for row in rows]


def create_session(title="新会话"):
    sid = str(uuid.uuid4())
    execute_update(
        f"INSERT INTO {SESSIONS_TABLE} (id, title) VALUES (%s, %s)",
        (sid, title),
    )
    return sid


def delete_session(session_id):
    execute_update(
        f"DELETE FROM {MESSAGES_TABLE} WHERE session_id = %s",
        (session_id,),
    )
    execute_update(
        f"DELETE FROM {SESSIONS_TABLE} WHERE id = %s",
        (session_id,),
    )


def rename_session(session_id, title):
    execute_update(
        f"UPDATE {SESSIONS_TABLE} SET title = %s, updated_at = NOW() WHERE id = %s",
        (title, session_id),
    )


def load_messages(session_id):
    """载入某会话所有历史消息（时间正序）"""
    rows = execute_query_raw(
        f"SELECT role, content, extra_json FROM {MESSAGES_TABLE} WHERE session_id = %s ORDER BY id ASC",
        (session_id,),
    )
    return [
        {"role": row[0], "content": row[1] if row[1] else ""}
        for row in rows
    ]


def save_message(session_id, role, content, extra_json=None):
    execute_update(
        f"INSERT INTO {MESSAGES_TABLE} (session_id, role, content, extra_json) VALUES (%s, %s, %s, %s)",
        (session_id, role, content, extra_json),
    )
