"""启动引导：初始化存储，MySQL 不可用且未强制完整模式时自动降级。"""

import os

from app.core.logging import get_logger
from app.session import init_tables

logger = get_logger("app.bootstrap")


def bootstrap_storage() -> None:
    """初始化数据库；只有显式 DEMO_MODE=0 时才强制 MySQL 失败退出。"""
    try:
        init_tables()
        return
    except Exception as exc:
        explicit = os.getenv("DEMO_MODE", "").strip().lower()
        if explicit in {"1", "true", "yes", "on"}:
            logger.exception("SQLite 初始化失败")
            raise
        if explicit == "0":
            logger.exception("MySQL 初始化失败，且已显式指定 DEMO_MODE=0")
            raise
        logger.warning("数据库初始化失败（%s），自动切换 SQLite 演示模式", exc)
        os.environ["DEMO_MODE"] = "1"
        init_tables()
