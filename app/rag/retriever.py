"""检索与上下文格式化。"""

from typing import List, Tuple

from app.core.config import config
from app.rag.embedding import EmbeddingService
from app.rag.storage import RagStore


def search(
    store: RagStore,
    query: str,
    top_k: int | None = None,
    embedder: EmbeddingService | None = None,
) -> List[dict]:
    """执行混合检索：词法优先，向量可用时重排。"""
    top_k = top_k or config.rag_top_k
    vector = embedder.embed(query) if embedder and embedder.available else None
    return store.search(query, top_k=top_k, vector=vector)


def format_context(chunks: List[dict]) -> Tuple[str, List[str]]:
    """把检索结果格式化为带引用的上下文。"""
    if not chunks:
        return "", []
    lines = []
    sources = []
    seen = set()
    for index, chunk in enumerate(chunks, start=1):
        name = chunk.get("document_name") or chunk.get("name") or "未知来源"
        lines.append(f"[{index}] 来源《{name}》：{chunk['content']}")
        if name not in seen:
            sources.append(name)
            seen.add(name)
    return "\n\n".join(lines), sources
