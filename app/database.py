"""数据库访问层：MySQL 与 SQLite 演示模式双后端。"""

import sqlite3
from pathlib import Path
from typing import Optional, Sequence

import pymysql

from app.core.config import config
from app.core.errors import DatabaseError
from app.core.logging import get_logger

logger = get_logger("app.database")


def is_demo_mode() -> bool:
    return config.is_demo_mode


def _ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_conn(database: Optional[str] = None):
    """返回数据库连接；演示模式使用 SQLite，生产模式使用 MySQL。"""
    if config.is_demo_mode:
        _ensure_parent(config.sqlite_path)
        conn = sqlite3.connect(config.sqlite_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    db = database or config.db_database
    try:
        return pymysql.connect(
            host=config.db_host,
            user=config.db_user,
            password=config.db_password,
            port=config.db_port,
            database=db,
            charset="utf8mb4",
        )
    except Exception as exc:  # pragma: no cover - 依赖外部服务
        raise DatabaseError(f"MySQL 连接失败：{exc}") from exc


def _adapt_sql(sql: str) -> str:
    """SQLite 使用 ? 占位符，MySQL 使用 %s。"""
    if config.is_demo_mode:
        return sql.replace("%s", "?")
    return sql


def _execute(cursor, sql: str, params: Optional[Sequence] = None):
    sql = _adapt_sql(sql)
    if params:
        cursor.execute(sql, tuple(params))
    else:
        cursor.execute(sql)


def _rows_to_text(cols, rows, limit: int) -> str:
    limited = rows[:limit]
    res = [" | ".join(cols), "-" * 50]
    for row in limited:
        res.append(" | ".join(str(x) for x in row))
    if len(rows) > limit:
        res.append(f"...（共 {len(rows)} 行，仅展示前 {limit} 行）")
    return "\n".join(res)


def execute_query(sql: str, params: Optional[Sequence] = None) -> str:
    """执行 SELECT 查询，返回格式化结果字符串。"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        _execute(cursor, sql, params)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        return _rows_to_text(cols, rows, config.sql_max_rows)
    finally:
        cursor.close()
        conn.close()


def execute_update(sql: str, params: Optional[Sequence] = None) -> str:
    """执行 INSERT / UPDATE / DELETE，返回受影响行数说明。"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        _execute(cursor, sql, params)
        conn.commit()
        return f"操作成功，影响 {cursor.rowcount} 行"
    finally:
        cursor.close()
        conn.close()


def execute_query_raw(sql: str, params: Optional[Sequence] = None):
    """执行 SELECT 查询，返回原始行数据列表。"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        _execute(cursor, sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def execute_raw(sql: str, params: Optional[Sequence] = None) -> str:
    """执行任意 SQL；默认只读模式下拒绝非查询语句。"""
    if not sql or not sql.strip():
        return ""

    stripped = sql.strip().lower()
    if config.sql_read_only and not stripped.startswith(("select", "with")):
        return "错误：系统处于只读模式，仅允许 SELECT 查询。"
    if stripped.startswith(("select", "with")):
        return execute_query(sql, params)
    return execute_update(sql, params)


def ping() -> bool:
    """健康检查：确认数据库可连接。"""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(_adapt_sql("SELECT 1"))
            cursor.fetchone()
            return True
        finally:
            cursor.close()
            conn.close()
    except Exception:
        logger.exception("数据库健康检查失败")
        return False
