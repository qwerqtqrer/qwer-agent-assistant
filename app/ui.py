"""Gradio UI：智能对话 + 知识库管理。"""

import gradio as gr

from app.chat import (
    _refresh_sessions as refresh_sessions,
)
from app.chat import (
    chat_fn,
    clear_chat,
    delete_current_session,
    delete_kb_document,
    new_session,
    search_kb,
    seed_kb,
    switch_session,
    upload_kb_file,
)
from app.image_utils import take_photo

CSS = """
:root {
  --primary: #4f46e5;
  --surface: #ffffff;
  --bg: #f8fafc;
  --text: #1e293b;
  --border: #e2e8f0;
}
.gr-box { border-radius: 10px !important; }
"""


def build_ui():
    with gr.Blocks(title="智慧校园 AI 智能体助手", theme=gr.themes.Soft(), css=CSS) as demo:
        session_state = gr.State()

        with gr.Tabs():
            # ── 智能对话 ──
            with gr.Tab("智能对话"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=260):
                        gr.Markdown("### 会话管理")
                        session_dropdown = gr.Dropdown(
                            label="选择会话",
                            choices=refresh_sessions(),
                            interactive=True,
                            value=None,
                        )
                        with gr.Row():
                            new_session_btn = gr.Button("新会话", size="sm", variant="primary")
                            delete_session_btn = gr.Button("删除", size="sm", variant="stop")

                        gr.Markdown("---")
                        gr.Markdown("### 快捷指令")
                        quick_commands = gr.Dataset(
                            label="点击快速输入",
                            components=[gr.Textbox(visible=False)],
                            samples=[
                                ["大理今天的天气怎么样？"],
                                ["查询所有水果信息"],
                                ["翻译 'Hello world' 为中文"],
                                ["计算 12.5 * 3 + (8 - 2) / 4"],
                                ["图书馆周末几点关门？"],
                            ],
                        )

                        gr.Markdown("---")
                        gr.Markdown("### 文档上传")
                        file_doc = gr.File(
                            label="上传文档（自动加入知识库）",
                            file_types=[".pdf", ".docx", ".xlsx", ".txt", ".md"],
                        )

                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            height=460,
                            avatar_images=(None, None),
                            show_label=False,
                        )
                        sources_md = gr.Markdown()

                        chat_input = gr.Textbox(
                            label="输入指令",
                            placeholder="请输入您的问题，如：查看今天的天气、查询学生成绩…",
                            lines=1,
                        )

                        with gr.Row():
                            camera_img = gr.Image(
                                label="拍照（优先处理）",
                                type="pil",
                                height=180,
                                width=180,
                            )
                            image_upload = gr.Image(
                                label="上传图片",
                                type="pil",
                                height=180,
                                width=180,
                            )

                        with gr.Row():
                            take_photo_btn = gr.Button("点击拍照", size="sm")
                            gr.Markdown("**提示**: 点击拍照后图片自动填入左侧拍照框，发送时优先处理")

                        with gr.Row():
                            submit_btn = gr.Button("发送", variant="primary", scale=2)
                            clear_btn = gr.Button("清空对话", variant="secondary", scale=1)

            # ── 知识库管理 ──
            with gr.Tab("知识库"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=280):
                        gr.Markdown("### 文档入库")
                        kb_file = gr.File(
                            label="上传文档（PDF/Word/Excel/TXT/Markdown）",
                            file_types=[".pdf", ".docx", ".xlsx", ".txt", ".md"],
                        )
                        seed_btn = gr.Button("初始化示例知识库", variant="secondary")
                        kb_status = gr.Markdown("尚未上传文档。")

                    with gr.Column(scale=2):
                        gr.Markdown("### 知识库列表")
                        kb_list = gr.Markdown("知识库为空。")
                        with gr.Row():
                            delete_id_input = gr.Textbox(label="要删除的文档 ID", scale=3)
                            delete_doc_btn = gr.Button("删除文档", variant="stop", scale=1)
                        gr.Markdown("---")
                        gr.Markdown("### 检索测试")
                        with gr.Row():
                            kb_search_input = gr.Textbox(label="检索关键词", scale=3)
                            kb_search_btn = gr.Button("检索", scale=1)
                        kb_search_output = gr.Markdown()

        # ── 事件绑定 ──
        submit_inputs = [chat_input, image_upload, camera_img, chatbot, session_state, file_doc]
        submit_outputs = [
            chat_input,
            image_upload,
            camera_img,
            chatbot,
            session_state,
            session_dropdown,
            sources_md,
        ]

        chat_input.submit(fn=chat_fn, inputs=submit_inputs, outputs=submit_outputs)
        submit_btn.click(fn=chat_fn, inputs=submit_inputs, outputs=submit_outputs)
        take_photo_btn.click(fn=take_photo, outputs=[camera_img])

        def quick_send(sample):
            return sample[0] if sample else ""

        quick_commands.click(fn=quick_send, inputs=[quick_commands], outputs=[chat_input]).then(
            fn=chat_fn, inputs=submit_inputs, outputs=submit_outputs
        )

        new_session_btn.click(
            fn=new_session,
            outputs=[session_state, chatbot, session_dropdown, sources_md],
        )
        session_dropdown.change(
            fn=switch_session,
            inputs=[session_dropdown],
            outputs=[session_state, chatbot, sources_md],
        )
        delete_session_btn.click(
            fn=delete_current_session,
            inputs=[session_state],
            outputs=[session_state, chatbot, session_dropdown, sources_md],
        )
        clear_btn.click(fn=clear_chat, outputs=[chatbot, sources_md])

        kb_file.change(
            fn=upload_kb_file,
            inputs=[kb_file],
            outputs=[kb_status, kb_list],
        )
        seed_btn.click(fn=seed_kb, outputs=[kb_status, kb_list])
        delete_doc_btn.click(
            fn=delete_kb_document,
            inputs=[delete_id_input],
            outputs=[kb_status, kb_list],
        )
        kb_search_btn.click(
            fn=search_kb,
            inputs=[kb_search_input],
            outputs=[kb_search_output],
        )

    return demo
