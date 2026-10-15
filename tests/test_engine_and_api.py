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


def test_text_only_image_fallback(monkeypatch):
    import base64
    from types import SimpleNamespace
    from unittest.mock import MagicMock
    from app.services import colab_client

    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")

    def _fail_post(path, payload):
        raise RuntimeError("Colab unavailable")

    monkeypatch.setattr(colab_client, "_post", _fail_post)

    raw_bytes = b"fake-rendered-image-bytes"
    expected_b64 = base64.b64encode(raw_bytes).decode()

    part = SimpleNamespace(inline_data=SimpleNamespace(data=raw_bytes, mime_type="image/png"))
    candidate = SimpleNamespace(content=SimpleNamespace(parts=[part]))
    fake_response = SimpleNamespace(candidates=[candidate])

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    import google.genai
    monkeypatch.setattr(google.genai, "Client", lambda api_key: fake_client)

    payload = {
        "product_name": "Test Bottle",
        "product_description": "A reusable bottle",
        "visual_concept": "Studio shot of bottle on wooden table",
        "product_photo": None,
    }

    result = colab_client.image(payload)

    assert result["mode"] == "gemini_fallback"
    assert result["engine"] == "gemini"
    assert result["image"] == f"data:image/png;base64,{expected_b64}"

