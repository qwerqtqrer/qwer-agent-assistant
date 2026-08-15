"""向量化服务：通过 OpenAI 兼容接口（智谱 embedding-3）生成向量。"""

import json
from typing import List, Optional

from app.core.config import config
from app.core.logging import get_logger

logger = get_logger("app.rag.embedding")


class EmbeddingService:
    """未配置 API Key 时 available=False，检索自动退化为词法匹配。"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        enabled: Optional[bool] = None,
    ):
        self.model = model or config.rag_embedding_model
        self.available = bool(
            config.llm_configured
            and (config.rag_embedding_enabled if enabled is None else enabled)
            and self.model
        )
        self._client = None
        if self.available:
            from langchain_openai import OpenAIEmbeddings

            self._client = OpenAIEmbeddings(
                model=self.model,
                api_key=api_key or config.zhipuai_api_key,
                base_url=base_url or config.zhipuai_base_url,
                timeout=config.llm_timeout,
                tiktoken_enabled=False,
                check_embedding_ctx_length=False,
            )
            logger.debug("向量服务已启用：%s", self.model)
        else:
            logger.info("向量服务未启用，RAG 使用词法检索")

    def embed(self, text: str) -> Optional[List[float]]:
        if not self.available:
            return None
        try:
            return self._client.embed_query(text)
        except Exception as exc:
            logger.warning("向量化失败（%s），降级为词法检索", exc)
            return None

    def embed_many(self, texts: List[str]) -> Optional[List[List[float]]]:
        if not self.available:
            return None
        try:
            return self._client.embed_documents(texts)
        except Exception as exc:
            logger.warning("批量向量化失败（%s），降级为词法检索", exc)
            return None

    @staticmethod
    def serialize(vector: Optional[List[float]]) -> Optional[str]:
        return json.dumps(vector, ensure_ascii=False) if vector is not None else None

    @staticmethod
    def deserialize(raw: Optional[str]) -> Optional[List[float]]:
        return json.loads(raw) if raw else None
