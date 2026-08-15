"""Gradio 对话逻辑：图片/文档预处理 + ChatService 编排。"""

import os

import gradio as gr

from app.core.config import config
from app.core.logging import get_logger
from app.rag import ensure_knowledge_base, get_embedder, get_store, search
from app.rag.ingest import ingest_file
from app.services import chat_service
from app.session import (
    create_session,
    delete_session,
    load_messages,
    load_sessions,
    rename_session,
)

logger = get_logger("app.chat")


def _resolve_yolo_model() -> str:
    """按配置路径查找 YOLO 模型，找不到时回退到上级目录。"""
    candidates = [config.yolo_model_path, os.path.join("..", "yolo11n.pt")]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ""


def chat_fn(chat, image, camera_image, chatbot, session_id, file_doc):
    """核心对话函数。"""
    session_id = session_id or create_session("新会话")
    image = camera_image if camera_image is not None else image
    chat = (chat or "").strip()

    extra_parts = []
    image_path = None

    if image is not None:
        try:
            from app.image_utils import pre_recognize_image, save_pil_image
            import yolo_info

            pil_info = save_pil_image(image)
            image_path = pil_info["full_path"]

            image_desc = pre_recognize_image(image)
            if image_desc:
                extra_parts.append(f"图片识别结果：{image_desc}")

            yolo_path = _resolve_yolo_model()
            if yolo_path:
                yolo_result = yolo_info.get_yolo_info(yolo_path, image_path)
                if yolo_result:
                    extra_parts.append(f"YOLO 检测结果：{yolo_result}")
            else:
                gr.Warning("未找到 YOLO 模型文件，已跳过目标检测")
        except Exception as exc:
            logger.warning("图片处理失败：%s", exc)
            gr.Warning(f"图片处理失败：{exc}")

    if file_doc is not None:
        try:
            doc_result = ingest_file(file_doc)
            extra_parts.append(
                f"[文档已加入知识库]《{doc_result['name']}》共 {doc_result['chunk_count']} 个分块，"
                "回答时请优先检索并引用该文档。"
            )
        except Exception as exc:
            logger.warning("文档入库失败：%s", exc)
            gr.Warning(f"文档入库失败：{exc}")

    full_message = chat
    if extra_parts:
        full_message = "\n\n".join(extra_parts) + f"\n\n用户的问题：{chat}"

    user_content = []
    if chat:
        user_content.append({"type": "text", "text": chat})
    if image_path:
        user_content.append({"type": "image", "path": image_path})
    chatbot.append({"role": "user", "content": user_content or chat})

    extra_json = {"image_path": image_path} if image_path else None

    try:
        result = chat_service.run(
            session_id,
            full_message,
            use_rag=True,
            display_text=chat,
            extra_json=extra_json,
        )
    except Exception as exc:
        logger.exception("Agent 调用失败")
        result = None
        answer = f"抱歉，我暂时无法处理您的请求，请稍后再试。错误：{exc}"
        chatbot.append({"role": "assistant", "content": answer})
        choices = _refresh_sessions()
        return (
            "",
            None,
            None,
            chatbot,
            session_id,
            gr.Dropdown(choices=choices, value=session_id),
            "",
            None,
        )

    chatbot.append({"role": "assistant", "content": result.answer})
    sources_md = _sources_markdown(result.sources)
    choices = _refresh_sessions()
    return (
        "",
        None,
        None,
        chatbot,
        result.session_id,
        gr.Dropdown(choices=choices, value=result.session_id),
        sources_md,
        None,
    )


def _sources_markdown(sources) -> str:
    if not sources:
        return ""
    unique = list(dict.fromkeys(sources))
    lines = ["**知识库引用来源：**"]
    lines.extend(f"- {name}" for name in unique)
    return "\n".join(lines)


def _refresh_sessions():
    try:
        return [(s["title"], s["id"]) for s in load_sessions()]
    except Exception:
        logger.warning("会话列表加载失败，界面以空列表启动", exc_info=True)
        return []


def new_session():
    sid = create_session()
    choices = _refresh_sessions()
    return sid, [], gr.Dropdown(choices=choices, value=sid), ""


def switch_session(session_id):
    if not session_id:
        return session_id, [], ""
    msgs = load_messages(session_id)
    chatbot = [_chatbot_message(m) for m in msgs]
    return session_id, chatbot, ""


def _chatbot_message(message: dict):
    """把持久化消息还原为 Gradio 气泡，图片随 extra_json 一并展示。"""
    extra = message.get("extra_json") or {}
    image_path = extra.get("image_path")
    if image_path and os.path.exists(image_path):
        content = []
        if message["content"]:
            content.append({"type": "text", "text": message["content"]})
        content.append({"type": "image", "path": image_path})
        return {"role": message["role"], "content": content}
    return {"role": message["role"], "content": message["content"]}


def delete_current_session(session_id):
    if session_id:
        delete_session(session_id)
    return new_session()


def clear_chat():
    return [], ""


def upload_kb_file(file):
    if not file:
        return "请先选择文件", _list_kb_documents()
    try:
        result = ingest_file(file)
        mode = "向量索引" if result["embedded"] else "词法索引"
        return f"入库成功：{result['name']}，共 {result['chunk_count']} 个分块（{mode}）", _list_kb_documents()
    except Exception as exc:
        return f"入库失败：{exc}", _list_kb_documents()


def seed_kb():
    result = ensure_knowledge_base()
    return f"示例知识库初始化完成：新增 {result['seeded']} 个文档", _list_kb_documents()


def restore_deleted_kb():
    from app.rag import restore_seed_documents

    result = restore_seed_documents()
    return (
        f"已恢复 {result['restored']} 个被删除的示例文档，本次新增入库 {result['seeded']} 个",
        _list_kb_documents(),
    )


def _list_kb_documents():
    docs = get_store().list_documents()
    if not docs:
        return "知识库为空。"
    lines = ["| ID | 文档 | 分块数 | 入库时间 |", "|---|---|---|---|"]
    for doc in docs:
        lines.append(f"| `{doc['id']}` | {doc['name']} | {doc['chunk_count']} | {doc['created_at'][:19]} |")
    return "\n".join(lines)


def delete_kb_document(doc_id):
    if not doc_id or not doc_id.strip():
        return "请先粘贴知识库列表中的完整文档 ID", _list_kb_documents()
    doc_id = doc_id.strip()
    store = get_store()
    deleted = store.delete_document(doc_id)
    if not deleted:
        matches = store.find_document_by_prefix(doc_id)
        if len(matches) == 1:
            deleted = store.delete_document(matches[0]["id"])
        elif len(matches) > 1:
            return f"该 ID 前缀匹配到 {len(matches)} 个文档，请使用列表中的完整 ID", _list_kb_documents()
    return ("文档已删除" if deleted else "文档不存在"), _list_kb_documents()


def search_kb(query):
    query = (query or "").strip()
    if not query:
        return "请输入检索关键词"
    chunks = search(get_store(), query, embedder=get_embedder())
    if not chunks:
        return "未找到相关内容"
    lines = []
    for index, chunk in enumerate(chunks, start=1):
        name = chunk.get("document_name", "未知来源")
        lines.append(f"**[{index}] {name}（分块 {chunk['chunk_index']}，{chunk['matched_by']}）**\n{chunk['content'][:300]}")
    return "\n\n".join(lines)
