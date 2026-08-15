"""RAG 文本切块测试。"""

from app.rag.chunker import split_text


def test_paragraph_merging():
    text = "第一段内容。" * 10 + "\n\n" + "第二段内容。" * 10
    chunks = split_text(text, chunk_size=120, overlap=0)
    assert len(chunks) >= 2
    assert all(len(c) <= 120 for c in chunks)


def test_long_paragraph_split():
    text = "今天天气很好。" * 60
    chunks = split_text(text, chunk_size=100, overlap=0)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_overlap_applied():
    text = "今天天气很好。" * 30
    chunks = split_text(text, chunk_size=80, overlap=20)
    assert len(chunks) > 1
    assert chunks[1].startswith(chunks[0][-20:])


def test_empty_text():
    assert split_text("") == []
