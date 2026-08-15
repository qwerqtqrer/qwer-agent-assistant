"""LLM 工厂：优先使用配置的 GLM 接口，未配置时提供可运行的演示模型。"""

from typing import List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI

from app.core.config import config
from app.core.logging import get_logger

logger = get_logger("app.core.llm")

_DEMO_REPLY = (
    "当前处于演示模式（未检测到 LLM API Key），我只能基于本地知识库和固定规则作答。"
    "请配置 zhipuai_api_key 后重启，即可获得完整的 Agent 工具调用能力。"
)


class DemoChatModel(BaseChatModel):
    """无 API Key 时的确定性聊天模型，便于离线演示与测试。"""

    @property
    def _llm_type(self) -> str:
        return "demo-chat-model"

    def bind_tools(self, tools, **kwargs):  # noqa: ANN001
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):  # noqa: ANN001
        text = self._render(messages)
        message = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _render(self, messages: List[BaseMessage]) -> str:
        rag_context = ""
        for msg in reversed(messages):
            if isinstance(msg, SystemMessage) and "知识库" in msg.content:
                rag_context = msg.content
                break
        human_texts = [m.content for m in messages if isinstance(m, HumanMessage)]
        last_human = str(human_texts[-1]) if human_texts else ""
        if rag_context:
            return (
                "演示模式下我检索到了相关资料：\n\n"
                f"{rag_context[:800]}\n\n"
                "请配置真实大模型后，我可以基于资料继续深入回答。"
            )
        return f"{_DEMO_REPLY}\n\n你刚才的问题是：{last_human[:200]}"


def build_llm() -> BaseChatModel:
    """返回配置的 ChatOpenAI（兼容 GLM），未配置时返回演示模型。"""
    if config.llm_configured:
        logger.debug("使用配置的 LLM：%s", config.llm_model)
        return ChatOpenAI(
            model=config.llm_model,
            api_key=config.zhipuai_api_key,
            base_url=config.zhipuai_base_url,
            temperature=config.llm_temperature,
            timeout=config.llm_timeout,
            max_tokens=config.llm_max_tokens,
        )
    logger.warning("未配置 LLM API Key，启用演示模型（DemoChatModel）")
    return DemoChatModel()


def build_sql_llm() -> BaseChatModel:
    """SQL 生成使用低温度模型，未配置时同样返回演示模型。"""
    if config.llm_configured:
        return ChatOpenAI(
            model=config.llm_model,
            api_key=config.zhipuai_api_key,
            base_url=config.zhipuai_base_url,
            temperature=0.0,
            timeout=config.llm_timeout,
            max_tokens=config.llm_max_tokens,
        )
    return DemoChatModel()
