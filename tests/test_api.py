"""FastAPI 接口测试（不挂载 Gradio，避免重型依赖）。"""

from fastapi.testclient import TestClient

from app.api.server import create_app
from app.rag import ensure_knowledge_base


def _client():
    return TestClient(create_app(mount_ui=False))


def test_health():
    ensure_knowledge_base()
    client = _client()
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["rag_chunks"] >= 1


def test_sessions_api():
    client = _client()
    response = client.post("/api/sessions")
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    assert session_id

    listing = client.get("/api/sessions")
    assert listing.status_code == 200
    assert any(item["id"] == session_id for item in listing.json()["sessions"])

    deleted = client.delete(f"/api/sessions/{session_id}")
    assert deleted.status_code == 200


def test_rag_search_api():
    ensure_knowledge_base()
    client = _client()
    response = client.post("/api/rag/search", json={"query": "图书馆周末开放", "top_k": 3})
    assert response.status_code == 200
    assert response.json()["chunks"]


def test_chat_sse():
    ensure_knowledge_base()
    client = _client()
    with client.stream(
        "POST",
        "/api/chat",
        json={"message": "图书馆周末几点关门？"},
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())
    assert '"type": "done"' in body
    assert "guide.md" in body


def test_upload_document_api():
    ensure_knowledge_base()
    client = _client()
    response = client.post(
        "/api/rag/documents",
        files={
            "file": (
                "hello.txt",
                "图书馆开放时间为 9:00 至 17:00。".encode("utf-8"),
                "text/plain",
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "hello.txt"
    assert data["chunk_count"] >= 1

    deleted = client.delete(f"/api/rag/documents/{data['document_id']}")
    assert deleted.status_code == 200


def test_cors_headers():
    client = _client()
    response = client.get("/api/health", headers={"Origin": "http://example.com"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"
    assert response.headers.get("access-control-allow-credentials") != "true"
