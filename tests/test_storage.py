"""RAG SQLite + FTS5 存储测试。"""

from app.rag.storage import RagStore


def test_add_search_delete(tmp_path):
    store = RagStore(str(tmp_path / "rag.sqlite3"))
    doc_id = store.add_document(
        "guide.md",
        "/tmp/guide.md",
        [
            "图书馆周末开放时间为 9:00 至 17:00。",
            "实习申请需要提前一周提交材料。",
        ],
    )

    hits = store.search("图书馆几点关门")
    assert hits
    assert hits[0]["document_name"] == "guide.md"
    assert store.count_chunks() == 2
    assert store.list_documents()[0]["chunk_count"] == 2
    assert store.has_document("guide.md") is True

    assert store.delete_document(doc_id) is True
    assert store.count_chunks() == 0


def test_short_query_fallback(tmp_path):
    store = RagStore(str(tmp_path / "rag2.sqlite3"))
    store.add_document("a.md", "a", ["校园网免费使用。"])
    hits = store.search("校园网")
    assert hits
