"""API 请求与响应模型。"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=8000)
    use_rag: bool = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=4, ge=1, le=20)


class HealthOut(BaseModel):
    status: str
    version: str
    demo_mode: bool
    llm_configured: bool
    embedding_available: bool
    database_ok: bool
    rag_chunks: int
