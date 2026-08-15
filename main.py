"""智慧校园 AI 智能体 - 统一入口（FastAPI + Gradio UI）。"""

import uvicorn

from app.api.server import create_app
from app.core.config import config
from app.core.logging import setup_logging
from app.rag import ensure_knowledge_base
from app.session import init_tables

setup_logging(config.log_level)


def main():
    init_tables()
    ensure_knowledge_base()
    app = create_app(mount_ui=True)
    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
