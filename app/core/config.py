"""统一配置管理：环境变量 + .env 文件，不把任何密钥写进代码。"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _mysql_configured() -> bool:
    return bool(os.getenv("DB_HOST") and os.getenv("DB_USER") and os.getenv("DB_DATABASE"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )

    # 应用
    app_name: str = "qwer-agent-assistant"
    version: str = "2.0.0"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # 大模型（GLM / OpenAI 兼容接口）
    zhipuai_api_key: str = ""
    zhipuai_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    llm_model: str = "glm-5.2"
    llm_temperature: float = 0.1
    llm_timeout: int = 30
    llm_max_tokens: int = 2048

    # 数据库（MySQL；未配置时自动切换 SQLite 演示模式）
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_database: str = "oa_demo"
    sqlite_path: str = "./data/app.sqlite3"
    sql_max_rows: int = 200
    sql_read_only: bool = True
    sql_allow_dml: bool = False

    # RAG 知识库
    rag_db_path: str = "./data/rag.sqlite3"
    rag_chunk_size: int = 600
    rag_chunk_overlap: int = 80
    rag_top_k: int = 4
    rag_embedding_model: str = "embedding-3"
    rag_embedding_enabled: bool = True
    knowledge_base_dir: str = "./knowledge_base"
    history_limit: int = 20

    # 邮件
    mail_host: str = "smtp.qq.com"
    mail_port: int = 465
    mail_user: str = ""
    mail_pass: str = ""
    mail_sender: str = ""

    # 高德地图
    amap_api_key: str = ""

    # 图片与文件
    upload_cache_dir: str = "./upload_cache"
    doc_max_length: int = 30000
    yolo_model_path: str = "./yolo11n.pt"

    @property
    def is_demo_mode(self) -> bool:
        """显式配置 DEMO_MODE 时以它为准；否则按是否配置 MySQL 自动判断。"""
        if os.getenv("DEMO_MODE") is not None:
            return _env_bool("DEMO_MODE")
        return not _mysql_configured()

    @property
    def llm_configured(self) -> bool:
        return bool(self.zhipuai_api_key and self.zhipuai_base_url)

    @property
    def embedding_configured(self) -> bool:
        return self.llm_configured and self.rag_embedding_enabled and bool(self.rag_embedding_model)


config = Settings()
