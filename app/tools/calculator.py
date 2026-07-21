"""计算器工具"""

import re

from langchain.tools import tool


@tool
def calculator(expression: str) -> str:
    """
    计算数学表达式（如 12.5 * 3 + (8 - 2) / 4）
    :param expression: 数学表达式字符串
    """
    safe_pattern = re.compile(r'^[\d\s\+\-\*\/\.\(\)\%]+$')
    if not safe_pattern.match(expression):
        return f"错误：表达式包含非法字符「{expression}」"

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"
