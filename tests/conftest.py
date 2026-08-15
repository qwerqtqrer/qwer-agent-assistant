"""测试全局配置：阻断 .env 读取、强制演示模式、使用临时数据目录。"""

import os
import tempfile

import dotenv
import pytest

# 阻断 .env 读取，避免隐私信息进入测试进程
dotenv.load_dotenv = lambda *args, **kwargs: False

# 清理可能继承自宿主环境的敏感变量
for key in list(os.environ):
    upper = key.upper()
    if any(part in upper for part in ("ZHIPU", "OPENAI", "API_KEY", "AMAP", "MAIL_", "DB_PASSWORD")):
        os.environ.pop(key, None)

_TMP = tempfile.mkdtemp(prefix="qwer_test_")
os.environ["DEMO_MODE"] = "1"
os.environ["SQLITE_PATH"] = os.path.join(_TMP, "app.sqlite3")
os.environ["RAG_DB_PATH"] = os.path.join(_TMP, "rag.sqlite3")
os.environ["UPLOAD_CACHE_DIR"] = os.path.join(_TMP, "uploads")
os.environ["KNOWLEDGE_BASE_DIR"] = os.path.join(_TMP, "kb")


@pytest.fixture(scope="session", autouse=True)
def sample_knowledge_base():
    kb_dir = os.environ["KNOWLEDGE_BASE_DIR"]
    os.makedirs(kb_dir, exist_ok=True)
    with open(os.path.join(kb_dir, "guide.md"), "w", encoding="utf-8") as f:
        f.write(
            "# 校园指南\n\n"
            "图书馆周末开放时间为 9:00 至 17:00。\n\n"
            "实习申请需要提前一周提交材料。"
        )
    return kb_dir


@pytest.fixture(scope="session", autouse=True)
def database_tables():
    from app.session import init_tables

    init_tables()
    return True


@pytest.fixture(autouse=True)
def reset_singletons():
    yield
    from app.agent import reset_agent
    from app.rag import reset_store

    reset_store()
    reset_agent()
