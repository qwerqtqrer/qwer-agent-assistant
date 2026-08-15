"""计算器 AST 求值测试。"""

import pytest

from app.tools.calculator import calculator, safe_eval


def test_basic_expression():
    assert safe_eval("12.5 * 3 + (8 - 2) / 4") == pytest.approx(39.0)


def test_unary_operator():
    assert safe_eval("-3 + 5") == 2


def test_power_limit_rejected():
    with pytest.raises(ValueError):
        safe_eval("2 ** 200")


def test_code_injection_rejected():
    with pytest.raises(ValueError):
        safe_eval("__import__('os').system('echo hi')")


def test_tool_returns_text():
    result = calculator.func("1 + 1")
    assert "= 2" in result
