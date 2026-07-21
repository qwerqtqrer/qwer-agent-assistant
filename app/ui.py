"""Gradio UI 界面"""

import gradio as gr

from app.chat import (
    chat_fn,
    clear_chat,
    delete_current_session,
    new_session,
    switch_session,
)
from app.chat import _refresh_sessions as refresh_sessions
from app.image_utils import take_photo

CSS = """
:root {
  --primary: #4f46e5;
  --primary-hover: #4338ca;
  --surface: #ffffff;
  --bg: #f8fafc;
  --text: #1e293b;
  --border: #e2e8f0;
}
.gr-box { border-radius: 12px !important; }
"""


def build_ui():
    with gr.Blocks(title="智慧校园 - 智能助手") as demo:
        session_state = gr.State()

        # ── 顶部标题 ──
        gr.HTML("""
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--border);margin-bottom:12px">
          <span style="font-size:24px;font-weight:700;background:linear-gradient(135deg,#4f46e5,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent">
            🏫 智慧校园
          </span>
          <span style="color:#64748b;font-size:14px">AI 智能体助手</span>
          <span style="margin-left:auto;font-size:12px;color:#94a3b8" id="time-display"></span>
        </div>
        <script>
        function updateTime(){const n=new Date;document.getElementById('time-display').textContent=n.toLocaleString('zh-CN')}
        updateTime();setInterval(updateTime,1000)
        </script>
        """)

        with gr.Row():
            # ── 左侧侧边栏 ──
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
                    delete_session_btn = gr.Button("🗑 删除", size="sm", variant="stop")

                gr.Markdown("---")
                gr.Markdown("### 🛠 快捷指令")
                quick_commands = gr.Dataset(
                    label="点击快速输入",
                    components=[gr.Textbox(visible=False)],
                    samples=[
                        ["大理今天的天气怎么样？"],
                        ["发送邮件给 3482289265@qq.com，主题为实习通知，内容为请按时提交实习报告"],
                        ["查询所有水果信息"],
                        ["翻译 'Hello world' 为中文"],
                        ["计算 12.5 * 3 + (8 - 2) / 4"],
                    ],
                )

                gr.Markdown("---")
                gr.Markdown("### 文档上传")
                file_doc = gr.File(
                    label="上传文档（PDF/Word/Excel/TXT）",
                    file_types=[".pdf", ".docx", ".xlsx", ".txt"],
                )

            # ── 右侧聊天区 ──
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    height=520,
                    avatar_images=(None, None),
                    show_label=False,
                )

                chat_input = gr.Textbox(
                    label="输入指令",
                    placeholder="请输入您的问题，如：查看今天的天气、查询学生成绩…",
                    lines=1,
                )

                with gr.Row():
                    camera_img = gr.Image(label="拍照（优先处理）", type="pil", height=180, width=180)
                    image_upload = gr.Image(label="🖼 上传图片", type="pil", height=180, width=180)

                with gr.Row():
                    take_photo_btn = gr.Button("点击拍照", size="sm")
                    gr.Markdown("**提示**: 点击拍照后图片自动填入左侧📷框，发送时优先处理")

                with gr.Row():
                    submit_btn = gr.Button("发送", variant="primary", scale=2)
                    clear_btn = gr.Button("🗑 清空对话", variant="secondary", scale=1)

        # ── 事件绑定 ──
        submit_inputs = [chat_input, image_upload, camera_img, chatbot, session_state, file_doc]
        submit_outputs = [chat_input, image_upload, camera_img, chatbot, session_state, session_dropdown]

        chat_input.submit(fn=chat_fn, inputs=submit_inputs, outputs=submit_outputs)
        submit_btn.click(fn=chat_fn, inputs=submit_inputs, outputs=submit_outputs)

        take_photo_btn.click(fn=take_photo, outputs=[camera_img])

        def quick_send(sample):
            return sample[0] if sample else ""

        quick_commands.click(fn=quick_send, inputs=[quick_commands], outputs=[chat_input]).then(
            fn=chat_fn, inputs=submit_inputs, outputs=submit_outputs
        )

        new_session_btn.click(fn=new_session, outputs=[session_state, chatbot, session_dropdown])
        session_dropdown.change(fn=switch_session, inputs=[session_dropdown], outputs=[session_state, chatbot])
        delete_session_btn.click(
            fn=delete_current_session,
            inputs=[session_state],
            outputs=[session_state, chatbot, session_dropdown],
        )
        clear_btn.click(fn=clear_chat, outputs=[chatbot])

    return demo
