"""计算器工具：AST 白名单求值，替代存在风险的 eval。"""

import ast
import operator

from langchain.tools import tool

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class _SafeEvaluator(ast.NodeVisitor):
    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            if abs(node.value) > 1e15:
                raise ValueError("数值过大")
            return node.value
        raise ValueError(f"不支持的字面量：{type(node.value).__name__}")

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise ValueError("不支持的运算")
        if isinstance(node.op, ast.Pow) and right > 100:
            raise ValueError("指数过大，已拦截")
        return op(left, right)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise ValueError("不支持的运算")
        return op(operand)

    def generic_visit(self, node):
        raise ValueError(f"不支持的语法节点：{type(node).__name__}")


def safe_eval(expression: str):
    """仅允许数字与 + - * / % ** () 的表达式求值。"""
    tree = ast.parse(expression, mode="eval")
    return _SafeEvaluator().visit(tree)


def _format_result(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.10g}"


@tool
def calculator(expression: str) -> str:
    """
    计算数学表达式（如 12.5 * 3 + (8 - 2) / 4）
    :param expression: 数学表达式字符串
    """
    try:
        result = safe_eval(expression)
        return f"{expression} = {_format_result(result)}"
    except Exception as exc:
        return f"计算错误：{exc}"
