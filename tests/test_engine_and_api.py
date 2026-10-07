import pytest

from app.services import campaign_service as svc

try:
    from fastapi.testclient import TestClient
    from app.main import app
except ImportError:      # fastapi not installed
    app = None


def test_engine_selection(monkeypatch):
    monkeypatch.setenv("COLAB_API_URL", "https://x.ngrok-free.dev")
    monkeypatch.setattr(svc.colab_client, "alive", lambda timeout=3: True)
    monkeypatch.setenv("PROVIDER", "auto");   assert svc.engine() == "colab"
    monkeypatch.setenv("PROVIDER", "gemini"); assert svc.engine() == "gemini"
    monkeypatch.setenv("PROVIDER", "auto")
    monkeypatch.setattr(svc.colab_client, "alive", lambda timeout=3: False)
    assert svc.engine() == "gemini"


@pytest.mark.skipif(app is None, reason="fastapi not installed")
def test_api_routes(monkeypatch):
    monkeypatch.setattr(svc, "engine", lambda: "gemini")
    monkeypatch.setattr(svc, "directions", lambda payload: {"ok": True, "engine": "gemini", "echo": payload["product_name"]})
    c = TestClient(app)
    assert c.get("/health").json() == {"status": "ok", "engine": "gemini"}
    body = {"product_name": "Bottle", "product_description": "d", "target_audience": "a", "campaign_goal": "Sales", "brand_tone": "Playful"}
    assert c.post("/directions", json=body).json()["echo"] == "Bottle"
    assert c.get("/").status_code == 200
