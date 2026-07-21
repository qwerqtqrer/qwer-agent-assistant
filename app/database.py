"""数据库连接与查询"""

import pymysql

from app.config import config


def get_conn(database=None):
    db = database or config.DB_DATABASE
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        port=config.DB_PORT,
        database=db,
        charset="utf8mb4",
    )


def execute_query(sql, params=None):
    """执行 SELECT 查询，返回格式化结果字符串"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        res = [" | ".join(cols), "-" * 50]
        for row in rows:
            res.append(" | ".join(str(x) for x in row))
        return "\n".join(res)
    finally:
        cursor.close()
        conn.close()


def execute_update(sql, params=None):
    """执行 INSERT / UPDATE / DELETE，返回受影响行数说明"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        conn.commit()
        return f"操作成功，影响 {cursor.rowcount} 行"
    finally:
        cursor.close()
        conn.close()


def execute_query_raw(sql, params=None):
    """执行 SELECT 查询，返回原始行数据的列表（每行为元组）"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def execute_raw(sql, params=None):
    """执行任意 SQL，根据首单词自动判断走查询还是更新"""
    if not sql or not sql.strip():
        return ""

    stripped = sql.strip().lower()
    if stripped.startswith("select"):
        return execute_query(sql, params)
    else:
        return execute_update(sql, params)
