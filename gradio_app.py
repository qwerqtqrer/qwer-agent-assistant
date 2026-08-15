"""仅启动 Gradio UI（不启动 FastAPI）的备用入口。"""

import gradio as gr

from app.bootstrap import bootstrap_storage
from app.core.logging import setup_logging
from app.rag import ensure_knowledge_base
from app.ui import CSS, build_ui


def main():
    setup_logging()
    bootstrap_storage()
    ensure_knowledge_base()
    demo = build_ui()
    demo.queue()
    demo.launch(debug=False, theme=gr.themes.Soft(), css=CSS)


if __name__ == "__main__":
    main()
