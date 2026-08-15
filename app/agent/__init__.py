"""LangGraph Agent 统一入口。"""

from app.agent.graph import AgentState, build_agent

_agent = None


def get_agent():
    """懒加载 Agent 单例，避免无 LLM 环境下导入即初始化。"""
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def reset_agent() -> None:
    global _agent
    _agent = None


__all__ = ["AgentState", "build_agent", "get_agent", "reset_agent"]
