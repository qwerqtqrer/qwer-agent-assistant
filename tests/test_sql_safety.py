"""SQL 只读安全校验测试。"""

from app.tools.sql_safety import validate_select_sql


def test_valid_select():
    ok, sql = validate_select_sql("SELECT * FROM school.courses")
    assert ok is True
    assert sql.startswith("SELECT")


def test_dml_blocked_by_default():
    ok, message = validate_select_sql("DELETE FROM school.courses")
    assert ok is False
    assert "只读" in message


def test_multi_statement_blocked():
    ok, _ = validate_select_sql("SELECT 1; DROP TABLE school.courses")
    assert ok is False


def test_system_table_blocked():
    ok, _ = validate_select_sql("SELECT * FROM mysql.user")
    assert ok is False


def test_forbidden_keyword_blocked():
    ok, _ = validate_select_sql("SELECT SLEEP(10) FROM school.courses")
    assert ok is False


def test_dml_allowed_when_configured():
    ok, sql = validate_select_sql("UPDATE school.courses SET location='x' WHERE id=1", allow_dml=True)
    assert ok is True
    assert sql.startswith("UPDATE")
