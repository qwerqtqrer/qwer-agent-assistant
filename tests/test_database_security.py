"""数据库安全回归测试：只读绕过、敏感字段脱敏、SQL 提示词约束。"""

from app.database import execute_query, execute_raw, execute_update
from app.tools.sql_query import SQL_SYSTEM_PROMPT


def test_read_only_blocks_cte_dml():
    message = execute_raw("WITH cte AS (SELECT 1) UPDATE users SET name='x'")
    assert "只读" in message


def test_read_only_blocks_direct_delete():
    message = execute_raw("DELETE FROM school.courses")
    assert "只读" in message


def test_sensitive_columns_redacted():
    try:
        execute_update(
            "CREATE TABLE IF NOT EXISTS test_sensitive "
            "(id INTEGER PRIMARY KEY, password TEXT)"
        )
        execute_update("DELETE FROM test_sensitive")
        execute_update("INSERT INTO test_sensitive (id, password) VALUES (1, 'secret123')")

        result = execute_query("SELECT id, password FROM test_sensitive")
        assert "***" in result
        assert "secret123" not in result
    finally:
        execute_update("DROP TABLE IF EXISTS test_sensitive")


def test_sql_prompt_forbids_password_fields():
    assert "password" in SQL_SYSTEM_PROMPT
    assert "禁止" in SQL_SYSTEM_PROMPT
    assert "敏感" in SQL_SYSTEM_PROMPT
