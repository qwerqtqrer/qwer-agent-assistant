"""RAG 知识库统一入口。"""

from app.rag.chunker import split_text
from app.rag.embedding import EmbeddingService
from app.rag.ingest import ingest_file, restore_seed_documents
from app.rag.retriever import format_context, search
from app.rag.storage import RagStore

_store = None
_embedder = None


def get_store() -> RagStore:
    global _store
    if _store is None:
        _store = RagStore()
    return _store


def get_embedder() -> EmbeddingService:
    global _embedder
    if _embedder is None:
        _embedder = EmbeddingService()
    return _embedder


def reset_store() -> None:
    global _store, _embedder
    if _store is not None:
        _store.close()
    _store = None
    _embedder = None


def ensure_knowledge_base() -> dict:
    """首次启动时把 knowledge_base 目录下的示例文档写入索引。"""
    from app.rag.ingest import seed_knowledge_base

    return seed_knowledge_base(get_store(), get_embedder())


__all__ = [
    "EmbeddingService",
    "RagStore",
    "ensure_knowledge_base",
    "format_context",
    "get_embedder",
    "get_store",
    "ingest_file",
    "reset_store",
    "restore_seed_documents",
    "search",
    "split_text",
]
