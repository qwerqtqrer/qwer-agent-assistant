"""统一日志配置。"""

import logging
import sys
from typing import Optional

_configured = False


def setup_logging(level: Optional[str] = None) -> None:
    global _configured
    if _configured:
        return
    _configured = True

    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel((level or "INFO").upper())


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
