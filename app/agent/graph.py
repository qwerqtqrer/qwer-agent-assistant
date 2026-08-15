"""LangGraph Agent 编排：检索 -> 模型 -> 工具循环。"""

from typing import Annotated, Callable, List, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.core.llm import build_llm
from app.core.logging import get_logger
from app.rag import format_context, get_embedder, get_store, search
from app.tools import ALL_TOOLS

logger = get_logger("app.agent.graph")


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    rag_context: str
    sources: List[str]


def _system_prompt(rag_context: str) -> str:
    base = (
        "你是「智慧校园 AI 智能体助手」。你负责回答校园相关问题，并可以调用工具获取实时数据。"
        "回答要简洁、准确、友好；工具调用失败时如实说明原因，不要编造结果。"
    )
    if rag_context:
        base += (
            "\n\n以下内容来自校园知识库，回答与用户问题相关时请优先采用，"
            "并在句末标注来源编号，例如 [1][2]：\n"
            f"{rag_context}"
        )
    return base


def _default_retriever(state: AgentState) -> dict:
    query = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            query = str(msg.content)
            break
    chunks = search(get_store(), query, embedder=get_embedder())
    context, sources = format_context(chunks)
    return {"rag_context": context, "sources": sources}


def build_agent(llm=None, tools=None, retriever: Optional[Callable] = None):
    """构建显式的检索 -> Agent -> 工具循环图。"""
    model = llm or build_llm()
    tool_list = ALL_TOOLS if tools is None else tools
    tool_node = ToolNode(tool_list)
    retrieve_node = retriever or _default_retriever

    def agent_node(state: AgentState) -> dict:
        system = SystemMessage(content=_system_prompt(state.get("rag_context", "")))
        response = model.bind_tools(tool_list).invoke([system, *state["messages"]])
        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["continue", "end"]:
        last = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", None) or []
        return "continue" if tool_calls else "end"

    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "agent")
    graph.add_conditional_edges("agent", should_continue, {"continue": "tools", "end": END})
    graph.add_edge("tools", "agent")
    return graph.compile()
