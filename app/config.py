"""应用配置：所有密钥/敏感信息从环境变量加载"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 基于 config.py 所在位置定位项目根目录
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")


class Config:
    # LLM
    ZHIPUAI_API_KEY: str = os.getenv("zhipuai_api_key", "")
    ZHIPUAI_BASE_URL: str = os.getenv("zhipuai_base_url", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "glm-5.2")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))

    # 数据库
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_DATABASE: str = os.getenv("DB_DATABASE", "oa_demo")

    # 邮件 (QQ SMTP)
    MAIL_HOST: str = os.getenv("MAIL_HOST", "smtp.qq.com")
    MAIL_USER: str = os.getenv("MAIL_USER", "")
    MAIL_PASS: str = os.getenv("MAIL_PASS", "")
    MAIL_SENDER: str = os.getenv("MAIL_SENDER", "")

    # 高德地图 API
    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY", "")

    # 其他
    UPLOAD_CACHE_DIR: str = os.getenv("UPLOAD_CACHE_DIR", "./upload_cache")
    DOC_MAX_LENGTH: int = int(os.getenv("DOC_MAX_LENGTH", "30000"))


config = Config()
