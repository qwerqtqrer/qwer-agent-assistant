"""FastAPI 路由：对话流式接口、会话管理、知识库管理、健康检查。"""

import json
import uuid
from pathlib import Path
from typing import Iterator

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.schemas import ChatRequest, SearchRequest
from app.core.config import config
from app.database import ping
from app.rag import ensure_knowledge_base, get_embedder, get_store, restore_seed_documents
from app.rag.ingest import ingest_file
from app.rag.retriever import search
from app.services import chat_service
from app.session import create_session, delete_session, load_messages, load_sessions

router = APIRouter()

_ALLOWED_EXTS = {".pdf", ".docx", ".xlsx", ".txt", ".md", ".markdown"}


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/health", response_model=dict)
def health():
    store = get_store()
    return {
        "status": "ok",
        "version": config.version,
        "demo_mode": config.is_demo_mode,
        "llm_configured": config.llm_configured,
        "embedding_available": get_embedder().available,
        "database_ok": ping(),
        "rag_chunks": store.count_chunks(),
    }


@router.post("/chat")
def chat(request: ChatRequest):
    """SSE 流式对话：token / done / error 三种事件。"""

    def event_stream() -> Iterator[str]:
        yield _sse({"type": "start", "session_id": request.session_id})
        for event in chat_service.stream(request.session_id, request.message):
            yield _sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/sessions")
def list_sessions():
    return {"sessions": load_sessions()}


@router.post("/sessions")
def new_session():
    session_id = create_session()
    return {"session_id": session_id, "title": "新会话"}


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    return {"messages": load_messages(session_id)}


@router.delete("/sessions/{session_id}")
def remove_session(session_id: str):
    delete_session(session_id)
    return {"ok": True}


@router.post("/rag/documents")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "upload.txt"
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型：{ext}")

    content = await file.read()
    max_bytes = config.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大支持 {config.max_upload_size_mb}MB",
        )

    target_dir = Path(config.upload_cache_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid.uuid4().hex}{ext}"
    try:
        target.write_bytes(content)
        return ingest_file(str(target), name=filename)
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"文档解析失败：{exc}") from exc


@router.get("/rag/documents")
def list_documents():
    return {"documents": get_store().list_documents()}


@router.delete("/rag/documents/{document_id}")
def remove_document(document_id: str):
    deleted = get_store().delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"ok": True}


@router.post("/rag/search")
def search_documents(request: SearchRequest):
    chunks = search(get_store(), request.query, top_k=request.top_k, embedder=get_embedder())
    return {"chunks": chunks}


@router.post("/rag/seed")
def seed_knowledge_base_endpoint():
    return ensure_knowledge_base()


@router.post("/rag/restore")
def restore_seed_documents_endpoint():
    return restore_seed_documents()
