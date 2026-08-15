"""对话编排服务：历史恢复、Agent 调用、持久化。"""

from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from app.core.config import config
from app.core.logging import get_logger
from app.session import create_session, load_messages, rename_session, save_message

logger = get_logger("app.services.chat")


@dataclass
class ChatResult:
    session_id: str
    answer: str
    sources: List[str] = field(default_factory=list)
    rag_context: str = ""
    tool_steps: int = 0


class ChatService:
    def __init__(self, agent=None):
        self._agent = agent

    @property
    def agent(self):
        if self._agent is None:
            from app.agent import get_agent

            self._agent = get_agent()
        return self._agent

    def _history_messages(self, session_id: str) -> List:
        history = load_messages(session_id)
        history = history[-config.history_limit :]
        messages = []
        for item in history:
            if item["role"] == "user":
                extra = item.get("extra_json") or {}
                content = extra.get("prompt") or item["content"]
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=item["content"]))
        return messages

    @staticmethod
    def _title(text: str) -> str:
        text = (text or "").strip()
        return text[:20] + ("..." if len(text) > 20 else "")

    def run(
        self,
        session_id: Optional[str],
        message: str,
        use_rag: bool = True,
        display_text: Optional[str] = None,
        extra_json: Optional[dict] = None,
    ) -> ChatResult:
        """非流式对话：恢复历史 -> 检索 -> Agent 推理 -> 持久化。"""
        sid = session_id or create_session()
        history = self._history_messages(sid)
        user_text = display_text if display_text is not None else message
        user_meta = dict(extra_json or {})
        user_meta.setdefault("prompt", message)
        save_message(sid, "user", user_text, extra_json=user_meta)

        result = self.agent.invoke(
            {
                "messages": [*history, HumanMessage(content=message)],
                "use_rag": use_rag,
            }
        )
        answer = str(result["messages"][-1].content)
        sources = list(result.get("sources") or [])
        save_message(sid, "assistant", answer)
        rename_session(sid, self._title(user_text or message))
        return ChatResult(
            session_id=sid,
            answer=answer,
            sources=sources,
            rag_context=str(result.get("rag_context") or ""),
        )

    def stream(
        self,
        session_id: Optional[str],
        message: str,
        use_rag: bool = True,
        display_text: Optional[str] = None,
        extra_json: Optional[dict] = None,
    ) -> Iterator[dict]:
        """流式对话：边推理边产出 token，结束后保存会话。"""
        sid = session_id or create_session()
        history = self._history_messages(sid)
        user_text = display_text if display_text is not None else message
        user_meta = dict(extra_json or {})
        user_meta.setdefault("prompt", message)
        save_message(sid, "user", user_text, extra_json=user_meta)

        answer_parts = []
        last_agent_answer = ""
        sources: List[str] = []
        tool_steps = 0
        try:
            events = self.agent.stream(
                {
                    "messages": [*history, HumanMessage(content=message)],
                    "use_rag": use_rag,
                },
                stream_mode=["messages", "updates"],
            )
            for mode, payload in events:
                if mode == "messages":
                    chunk, _meta = payload
                    if isinstance(chunk, AIMessageChunk) and isinstance(chunk.content, str) and chunk.content:
                        answer_parts.append(chunk.content)
                        yield {"type": "token", "content": chunk.content}
                elif mode == "updates":
                    for node, update in payload.items():
                        if node == "retrieve":
                            sources = list(update.get("sources") or [])
                        elif node == "tools":
                            tool_steps += 1
                        elif node == "agent":
                            for item in update.get("messages") or []:
                                if isinstance(item, AIMessage) and item.content:
                                    last_agent_answer = str(item.content)
        except Exception as exc:
            logger.exception("Agent 流式调用失败")
            answer = f"抱歉，我暂时无法处理您的请求。错误：{exc}"
            save_message(sid, "assistant", answer)
            rename_session(sid, self._title(user_text or message))
            yield {"type": "error", "content": answer}
            return

        answer = "".join(answer_parts).strip()
        if not answer and last_agent_answer:
            answer = last_agent_answer.strip()
        if not answer and tool_steps == 0:
            fallback = self.agent.invoke(
                {
                    "messages": [*history, HumanMessage(content=message)],
                    "use_rag": use_rag,
                }
            )
            answer = str(fallback["messages"][-1].content).strip()
            if answer:
                yield {"type": "token", "content": answer}
        if not answer:
            answer = "抱歉，我暂时无法处理您的请求，请稍后再试。"
        save_message(sid, "assistant", answer)
        rename_session(sid, self._title(user_text or message))
        yield {
            "type": "done",
            "session_id": sid,
            "answer": answer,
            "sources": sources,
            "tool_steps": tool_steps,
        }
