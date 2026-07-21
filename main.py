"""智慧校园智能体 - 入口"""

import gradio as gr

from app.session import init_tables
from app.ui import CSS, build_ui

# 启动时初始化数据库表
init_tables()

demo = build_ui()

if __name__ == "__main__":
    demo.queue()
    demo.launch(debug=False, theme=gr.themes.Soft(), css=CSS)
