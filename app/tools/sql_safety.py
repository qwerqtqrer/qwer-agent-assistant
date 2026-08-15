"""SQL 安全校验：只读白名单、禁用多语句与危险关键字。"""

import re

DML_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "replace",
)

DESTRUCTIVE_KEYWORDS = (
    "drop",
    "alter",
    "create",
    "truncate",
    "grant",
    "revoke",
    "call",
    "execute",
    "load_file",
    "into outfile",
    "information_schema",
    "mysql.user",
    "sleep",
    "benchmark",
)


def strip_comments(sql: str) -> str:
    """移除 SQL 注释，防止注释绕过关键字校验。"""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"(^|\s)--[^\n]*", " ", sql)
    sql = re.sub(r"(^|\s)#[^\n]*", " ", sql)
    return sql


def validate_select_sql(sql: str, allow_dml: bool = False):
    """校验 SQL 安全性，返回 (是否通过, 消息或规范化 SQL)。"""
    if not sql or not sql.strip():
        return False, "错误：生成的 SQL 为空。"

    cleaned = strip_comments(sql).strip().rstrip(";").strip()
    if ";" in cleaned:
        return False, "错误：禁止执行多条 SQL 语句。"

    lowered = cleaned.lower()
    if allow_dml:
        if not lowered.startswith(("select", "with", "insert", "update", "delete")):
            return False, "错误：SQL 必须以 SELECT/WITH/INSERT/UPDATE/DELETE 开头。"
    elif not lowered.startswith(("select", "with")):
        return False, "错误：系统只读模式仅允许 SELECT/WITH 查询。"

    forbidden = DESTRUCTIVE_KEYWORDS
    if not allow_dml:
        forbidden = DESTRUCTIVE_KEYWORDS + DML_KEYWORDS
    for keyword in forbidden:
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            return False, f"错误：SQL 包含禁止使用的关键字「{keyword}」。"
    if re.search(r"mysql\s*\.\s*\w+", lowered):
        return False, "错误：禁止访问 MySQL 系统库。"

    return True, cleaned
