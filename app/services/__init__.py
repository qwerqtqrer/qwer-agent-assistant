"""业务服务层。"""

from app.services.chat import ChatResult, ChatService

chat_service = ChatService()

__all__ = ["ChatResult", "ChatService", "chat_service"]
