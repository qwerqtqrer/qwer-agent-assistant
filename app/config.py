"""兼容旧入口：新配置实现位于 app.core.config。"""

from app.core.config import Settings, config

Config = Settings

__all__ = ["Config", "config"]
