"""AI Sentinel — smoke tests for the API skeleton (no DB required)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "ai-sentinel-backend"


def test_openapi_loads():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    # all expected routes registered
    expected = [
        "/api/v1/items",
        "/api/v1/rivalry",
        "/api/v1/trends",
        "/api/v1/research",
        "/api/v1/ask",
        "/api/v1/files",
        "/api/v1/bulletins",
        "/api/v1/alerts",
        "/api/v1/watch",
        "/api/v1/library",
    ]
    for p in expected:
        assert p in paths, f"missing route {p}"


def test_rivalry_route_registered():
    """Verify registration without requiring a running PostgreSQL instance."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "/api/v1/rivalry" in r.json()["paths"]
