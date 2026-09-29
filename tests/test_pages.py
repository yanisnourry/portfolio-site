from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_docs_disabled():
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404
