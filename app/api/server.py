"""FastAPI 应用组装：REST API + Gradio UI 挂载。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes import router
from app.core.config import config


def create_app(mount_ui: bool = True) -> FastAPI:
    app = FastAPI(
        title="智慧校园 AI 智能体 API",
        version=config.version,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/ui")

    if mount_ui:
        import gradio as gr

        from app.ui import CSS, build_ui

        demo = build_ui()
        gr.mount_gradio_app(
            app,
            demo,
            path="/ui",
            theme=gr.themes.Soft(),
            css=CSS,
            ssr_mode=False,
        )
    return app
