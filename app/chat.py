"""核心对话逻辑"""

import gradio as gr
from langchain_core.messages import HumanMessage

from app.agent_setup import agent
from app.config import config
from app.document import parse_document
from app.image_utils import build_chat_image_content, pre_recognize_image, save_pil_image
from app.session import (
    create_session,
    load_messages,
    load_sessions,
    rename_session,
    save_message,
)
import yolo_info


def chat_fn(chat, image, camera_image, chatbot, session_id, file_doc):
    """核心对话函数"""
    session_id = session_id or create_session("新会话")

    # 优先级：拍照 > 上传图片
    image = camera_image if camera_image is not None else image

    # 图片预处理
    image_desc = pre_recognize_image(image)

    # 图片 + YOLO
    pil_img_info = None
    yolo_result = None
    if image is not None:
        try:
            pil_img_info = save_pil_image(image)
            yolo_result = yolo_info.get_yolo_info("yolo11n.pt", pil_img_info["full_path"])
        except Exception as e:
            print(f"图片处理失败: {e}")
            gr.Warning(f"图片处理失败: {e}")

    # 文档解析
    doc_text = ""
    if file_doc is not None:
        try:
            doc_text = parse_document(file_doc)
            if len(doc_text) > config.DOC_MAX_LENGTH:
                doc_text = doc_text[: config.DOC_MAX_LENGTH] + "\n\n...（文档过长已截断）"
        except Exception as e:
            print(f"文档解析失败: {e}")
            gr.Warning(f"文档解析失败: {e}")

    # 组装最终用户输入
    extra_parts = []
    if image_desc:
        extra_parts.append(f"图片识别结果：{image_desc}")
    if yolo_result:
        extra_parts.append(f"YOLO 检测结果：{yolo_result}")
    if doc_text:
        extra_parts.append(f"用户上传的文档内容：\n{doc_text}")

    if extra_parts:
        full_user_content = "\n\n".join(extra_parts) + f"\n\n用户的问题：{chat}\n\n请根据上述信息回答用户的问题。"
    else:
        full_user_content = chat

    # 保存用户消息
    save_message(session_id, "user", chat)

    # 聊天框展示
    content_list = [{"type": "text", "text": chat}]
    if image is not None:
        try:
            content_list.extend(build_chat_image_content(image))
        except Exception as e:
            print(f"保存临时图片失败: {e}")

    chatbot.append({"role": "user", "content": content_list})

    # Agent 调用
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=full_user_content)]},
            config={"configurable": {"thread_id": session_id}},
        )
        result = result["messages"][-1].content
    except Exception as e:
        print(f"Agent 调用失败: {e}")
        result = "抱歉，我暂时无法处理您的请求，请稍后再试。"

    # 保存助手消息
    save_message(session_id, "assistant", result)
    chatbot.append({"role": "assistant", "content": result})

    # 自动重命名会话
    session_title = chat[:20] + ("..." if len(chat) > 20 else "")
    rename_session(session_id, session_title)

    choices = _refresh_sessions()
    return "", None, None, chatbot, session_id, gr.Dropdown(choices=choices, value=session_id)


def _refresh_sessions():
    sessions = load_sessions()
    return [(s["title"], s["id"]) for s in sessions]


def new_session():
    sid = create_session()
    choices = _refresh_sessions()
    return sid, [], gr.Dropdown(choices=choices, value=sid)


def switch_session(session_id):
    if not session_id:
        return session_id, []
    msgs = load_messages(session_id)
    chatbot = []
    for m in msgs:
        chatbot.append({"role": m["role"], "content": m["content"]})
    return session_id, chatbot


def delete_current_session(session_id):
    if session_id:
        from app.session import delete_session as _delete

        _delete(session_id)
    return new_session()


def clear_chat():
    return []
