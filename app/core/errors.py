"""应用级异常定义。"""


class AppError(Exception):
    """应用基础异常。"""


class ConfigError(AppError):
    """配置缺失或不合法。"""


class DatabaseError(AppError):
    """数据库连接或执行异常。"""


class RagError(AppError):
    """RAG 知识库异常。"""


class ToolError(AppError):
    """Agent 工具执行异常。"""
