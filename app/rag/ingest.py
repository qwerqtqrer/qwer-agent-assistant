"""文档入库：解析 -> 切块 -> 存储（可选向量化）。"""

import os
from pathlib import Path
from typing import Optional

from app.core.config import config
from app.core.errors import RagError
from app.core.logging import get_logger
from app.document import parse_document
from app.rag.chunker import split_text
from app.rag.embedding import EmbeddingService
from app.rag.storage import RagStore

logger = get_logger("app.rag.ingest")


def ingest_file(
    file_path: str,
    name: Optional[str] = None,
    store: Optional[RagStore] = None,
    embedder: Optional[EmbeddingService] = None,
) -> dict:
    """把一个本地文件写入知识库，返回索引摘要。"""
    from app.rag import get_embedder, get_store

    store = store or get_store()
    embedder = embedder or get_embedder()
    text = parse_document(file_path)
    if not text or not text.strip():
        raise RagError("文档内容为空，无法建立索引")

    chunks = split_text(text, config.rag_chunk_size, config.rag_chunk_overlap)
    if not chunks:
        raise RagError("未能从文档中提取有效内容")

    embeddings = None
    if embedder.available:
        embeddings = embedder.embed_many(chunks)

    doc_name = name or os.path.basename(file_path)
    doc_id = store.add_document(doc_name, source=file_path, chunks=chunks, embeddings=embeddings)
    logger.info("已入库文档 %s：%d 个分块（向量 %s）", doc_name, len(chunks), bool(embeddings))
    return {
        "document_id": doc_id,
        "name": doc_name,
        "chunk_count": len(chunks),
        "embedded": bool(embeddings),
    }


def seed_knowledge_base(
    store: Optional[RagStore] = None,
    embedder: Optional[EmbeddingService] = None,
) -> dict:
    """扫描 knowledge_base 目录，把示例文档首次入库。"""
    from app.rag import get_embedder, get_store

    store = store or get_store()
    embedder = embedder or get_embedder()
    kb_dir = Path(config.knowledge_base_dir)
    if not kb_dir.exists():
        return {"seeded": 0, "skipped": 0, "documents": []}

    results = []
    for path in sorted(kb_dir.glob("*.md")) + sorted(kb_dir.glob("*.txt")):
        if store.has_document(path.name):
            continue
        try:
            results.append(ingest_file(str(path), name=path.name, store=store, embedder=embedder))
        except Exception:
            logger.exception("示例文档入库失败：%s", path)
    return {
        "seeded": len(results),
        "skipped": len(list(kb_dir.glob("*.md"))) + len(list(kb_dir.glob("*.txt"))) - len(results),
        "documents": results,
    }
