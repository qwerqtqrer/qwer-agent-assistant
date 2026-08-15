"""仅启动 Gradio UI（不启动 FastAPI）的备用入口。"""

import gradio as gr

from app.core.logging import setup_logging
from app.rag import ensure_knowledge_base
from app.session import init_tables
from app.ui import build_ui


def main():
    setup_logging()
    init_tables()
    ensure_knowledge_base()
    demo = build_ui()
    demo.queue()
    demo.launch(debug=False)


if __name__ == "__main__":
    main()
