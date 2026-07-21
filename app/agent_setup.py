"""LangChain Agent 组装"""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from app.config import config
from app.tools import ALL_TOOLS

llm = ChatOpenAI(
    model=config.LLM_MODEL,
    api_key=config.ZHIPUAI_API_KEY,
    base_url=config.ZHIPUAI_BASE_URL,
    temperature=config.LLM_TEMPERATURE,
    timeout=config.LLM_TIMEOUT,
)

agent = create_agent(
    model=llm,
    tools=ALL_TOOLS,
    checkpointer=InMemorySaver(),
)
