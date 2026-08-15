"""文本切块：按段落合并、长段拆分，支持重叠上下文。"""

import re


def _split_sentences(paragraph: str) -> list:
    parts = re.split(r"(?<=[。！？!?；;])\s*", paragraph)
    return [p.strip() for p in parts if p.strip()]


def _split_long_text(text: str, chunk_size: int) -> list:
    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    chunks = []
    current = ""
    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(sentence), chunk_size):
                chunks.append(sentence[i : i + chunk_size])
            continue
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current}{sentence}" if current else sentence
        else:
            chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def _apply_overlap(chunks: list, overlap: int) -> list:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    result = [chunks[0]]
    for chunk in chunks[1:]:
        prev_tail = result[-1][-overlap:]
        if prev_tail and not chunk.startswith(prev_tail):
            result.append(prev_tail + chunk)
        else:
            result.append(chunk)
    return result


def split_text(text: str, chunk_size: int = 600, overlap: int = 80) -> list:
    """把文档文本拆成适合检索的块。"""
    if not text or not text.strip():
        return []
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(para) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_text(para, chunk_size))
            continue
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return _apply_overlap(chunks, overlap)
