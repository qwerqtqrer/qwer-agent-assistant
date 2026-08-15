"""配置与安全默认值测试。"""

from app.core.config import config


def test_demo_mode_enabled():
    assert config.is_demo_mode is True


def test_llm_not_configured_in_ci():
    assert config.llm_configured is False


def test_sql_read_only_default():
    assert config.sql_read_only is True
