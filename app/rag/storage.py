"""RAG 存储：SQLite + FTS5 词法检索，可选向量重排。"""

import json
import math
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.core.config import config
from app.rag.embedding import EmbeddingService


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _trigrams(text: str, size: int = 3, limit: int = 24) -> List[str]:
    return [text[i : i + size] for i in range(max(0, len(text) - size + 1))][:limit]


class RagStore:
    """知识库索引，FTS5 使用 trigram tokenizer，兼容中文检索。"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.rag_db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._lock = threading.RLock()
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS deleted_docs (
                name TEXT PRIMARY KEY,
                deleted_at TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content,
                content='chunks',
                content_rowid='id',
                tokenize='trigram'
            );
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
            END;
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', old.id, old.content);
            END;
            """
        )
        self._conn.commit()

    def add_document(
        self,
        name: str,
        source: str,
        chunks: List[str],
        embeddings: Optional[List[Optional[List[float]]]] = None,
    ) -> str:
        with self._lock:
            doc_id = uuid.uuid4().hex
            with self._conn:
                self._conn.execute(
                    "INSERT INTO documents (id, name, source, created_at) VALUES (?, ?, ?, ?)",
                    (doc_id, name, source, _now()),
                )
                for index, content in enumerate(chunks):
                    embedding = (
                        EmbeddingService.serialize(embeddings[index])
                        if embeddings and index < len(embeddings)
                        else None
                    )
                    self._conn.execute(
                        "INSERT INTO chunks (document_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
                        (doc_id, index, content, embedding),
                    )
            return doc_id

    def delete_document(self, doc_id: str) -> bool:
        with self._lock:
            with self._conn:
                row = self._conn.execute(
                    "SELECT name FROM documents WHERE id = ?", (doc_id,)
                ).fetchone()
                cursor = self._conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                if cursor.rowcount > 0 and row:
                    self._conn.execute(
                        "INSERT OR IGNORE INTO deleted_docs (name, deleted_at) VALUES (?, ?)",
                        (row["name"], _now()),
                    )
                return cursor.rowcount > 0

    def list_documents(self) -> List[dict]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT d.id, d.name, d.source, d.created_at, COUNT(c.id) AS chunk_count
                FROM documents d
                LEFT JOIN chunks c ON c.document_id = d.id
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def find_document_by_prefix(self, prefix: str) -> List[dict]:
        """按 ID 前缀查找文档，用于界面删除时兼容短 ID。"""
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, name FROM documents WHERE id LIKE ? ORDER BY id LIMIT 20",
                (f"{prefix}%",),
            ).fetchall()
            return [dict(row) for row in rows]

    def count_chunks(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()
            return int(row["n"])

    def has_document(self, name: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM documents WHERE name = ? LIMIT 1", (name,)
            ).fetchone()
            return row is not None

    def is_deleted(self, name: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM deleted_docs WHERE name = ? LIMIT 1", (name,)
            ).fetchone()
            return row is not None

    def list_deleted(self) -> List[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT name FROM deleted_docs ORDER BY deleted_at DESC"
            ).fetchall()
            return [row["name"] for row in rows]

    def restore_document(self, name: str) -> bool:
        with self._lock:
            with self._conn:
                cursor = self._conn.execute(
                    "DELETE FROM deleted_docs WHERE name = ?", (name,)
                )
                return cursor.rowcount > 0

    def _search_lexical(self, query: str, top_k: int) -> List[dict]:
        if len(query) < 3:
            escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            rows = self._conn.execute(
                """
                SELECT c.id, c.document_id, d.name AS document_name, c.chunk_index, c.content
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.content LIKE ? ESCAPE '\\'
                ORDER BY c.id
                LIMIT ?
                """,
                (f"%{escaped}%", top_k),
            ).fetchall()
            return [
                {**dict(row), "score": 1.0, "matched_by": "keyword"}
                for row in rows
            ]

        grams = _trigrams(query)
        fts_query = " OR ".join(
            f'"{gram.replace(chr(34), chr(34) * 2)}"' for gram in grams
        )
        try:
            rows = self._conn.execute(
                """
                SELECT c.id, c.document_id, d.name AS document_name, c.chunk_index,
                       c.content, bm25(chunks_fts) AS rank
                FROM chunks_fts
                JOIN chunks c ON c.id = chunks_fts.rowid
                JOIN documents d ON d.id = c.document_id
                WHERE chunks_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, top_k * 2),
            ).fetchall()
            results = [
                {
                    **dict(row),
                    "score": round(1 / (1 + abs(row["rank"])), 4),
                    "matched_by": "fts",
                }
                for row in rows
            ]
            if results:
                return results
        except sqlite3.OperationalError:
            pass
        return self._search_lexical(query[:2], top_k)

    def _search_vector(self, query_embedding: List[float], top_k: int) -> List[dict]:
        rows = self._conn.execute(
            """
            SELECT c.id, c.document_id, d.name AS document_name, c.chunk_index,
                   c.content, c.embedding
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
            """
        ).fetchall()
        scored = []
        for row in rows:
            vector = EmbeddingService.deserialize(row["embedding"])
            score = _cosine(query_embedding, vector or [])
            if score > 0:
                scored.append(
                    {
                        **dict(row),
                        "score": round(score, 4),
                        "matched_by": "vector",
                    }
                )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        vector: Optional[List[float]] = None,
    ) -> List[dict]:
        with self._lock:
            top_k = top_k or config.rag_top_k
            query = (query or "").strip()
            if not query:
                return []

            lexical = self._search_lexical(query, top_k)
            vector_hits = self._search_vector(vector, top_k) if vector else []

            merged = {}
            for item in [*lexical, *vector_hits]:
                item_id = item["id"]
                if item_id not in merged or item["score"] > merged[item_id]["score"]:
                    merged[item_id] = item
            return sorted(merged.values(), key=lambda item: item["score"], reverse=True)[:top_k]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
