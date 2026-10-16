import pytest
import requests

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


@pytest.mark.skipif(app is None, reason="fastapi not installed")
def test_directions_unexpected_error_returns_500(monkeypatch):
    def _fail_unexpected(payload):
        raise RuntimeError("Unexpected pipeline crash")

    monkeypatch.setattr(svc, "directions", _fail_unexpected)
    c = TestClient(app)
    body = {
        "product_name": "Bottle",
        "product_description": "d",
        "target_audience": "a",
        "campaign_goal": "Sales",
        "brand_tone": "Playful",
    }
    r = c.post("/directions", json=body)
    assert r.status_code == 500
    assert r.json()["detail"] == "An unexpected internal error occurred. Please try again later."
    assert "Unexpected pipeline crash" not in r.text


@pytest.mark.skipif(app is None, reason="fastapi not installed")
def test_upstream_failures_return_502(monkeypatch):
    c = TestClient(app)
    body = {
        "product_name": "Bottle",
        "product_description": "d",
        "target_audience": "a",
        "campaign_goal": "Sales",
        "brand_tone": "Playful",
    }

    # Test /directions with ConnectionError
    monkeypatch.setattr(
        svc,
        "directions",
        lambda payload: (_ for _ in ()).throw(requests.ConnectionError("Connection refused by upstream")),
    )
    r_dir = c.post("/directions", json=body)
    assert r_dir.status_code == 502
    assert r_dir.json()["detail"] == "Upstream service is currently unavailable. Please try again later."
    assert "Connection refused by upstream" not in r_dir.text

    # Test /content with Timeout
    content_body = {
        "user_input": body,
        "campaign_strategy": {"core_message": "cm"},
        "direction": {"name": "d"},
    }
    monkeypatch.setattr(
        svc,
        "content",
        lambda u, s, d: (_ for _ in ()).throw(requests.Timeout("Upstream timed out")),
    )
    r_cnt = c.post("/content", json=content_body)
    assert r_cnt.status_code == 502
    assert r_cnt.json()["detail"] == "Upstream service is currently unavailable. Please try again later."
    assert "Upstream timed out" not in r_cnt.text


@pytest.mark.skipif(app is None, reason="fastapi not installed")
def test_image_distinguishes_upstream_from_internal_error(monkeypatch):
    from app.services import colab_client

    image_body = {
        "product_name": "Bottle",
        "product_description": "d",
        "visual_concept": "Studio shot",
        "platform": "instagram",
    }
    c = TestClient(app)

    # Known upstream error -> 502
    monkeypatch.setattr(
        colab_client,
        "image",
        lambda payload: (_ for _ in ()).throw(requests.ConnectTimeout("Connect timeout to Colab")),
    )
    r_upstream = c.post("/image", json=image_body)
    assert r_upstream.status_code == 502
    assert r_upstream.json()["detail"] == "Upstream service is currently unavailable. Please try again later."
    assert "Connect timeout to Colab" not in r_upstream.text

    # Unexpected programming error -> 500
    monkeypatch.setattr(
        colab_client,
        "image",
        lambda payload: (_ for _ in ()).throw(KeyError("missing_field_bug")),
    )
    r_internal = c.post("/image", json=image_body)
    assert r_internal.status_code == 500
    assert r_internal.json()["detail"] == "An unexpected internal error occurred. Please try again later."
    assert "missing_field_bug" not in r_internal.text


@pytest.mark.skipif(app is None, reason="fastapi not installed")
def test_mock_secrets_never_leak_in_error_responses(monkeypatch):
    from app.services import colab_client

    secret_key = "AIzaSy_TEST_SECRET_KEY_12345"
    secret_url = f"https://user:{secret_key}@internal.colab.server/v1/generate"

    c = TestClient(app)
    body = {
        "product_name": "Bottle",
        "product_description": "d",
        "target_audience": "a",
        "campaign_goal": "Sales",
        "brand_tone": "Playful",
    }

    # Upstream failure on /directions
    monkeypatch.setattr(
        svc,
        "directions",
        lambda payload: (_ for _ in ()).throw(requests.ConnectionError(f"Failed to connect to {secret_url}")),
    )
    r_dir = c.post("/directions", json=body)
    assert r_dir.status_code == 502
    assert secret_key not in r_dir.text
    assert "internal.colab.server" not in r_dir.text

    # Unexpected error on /directions
    monkeypatch.setattr(
        svc,
        "directions",
        lambda payload: (_ for _ in ()).throw(RuntimeError(f"Database crash with secret={secret_key}")),
    )
    r_dir_int = c.post("/directions", json=body)
    assert r_dir_int.status_code == 500
    assert secret_key not in r_dir_int.text

    # Upstream failure on /image
    monkeypatch.setattr(
        colab_client,
        "image",
        lambda payload: (_ for _ in ()).throw(requests.HTTPError(f"502 from {secret_url}")),
    )
    r_img_up = c.post("/image", json={"product_name": "B", "visual_concept": "v"})
    assert r_img_up.status_code == 502
    assert secret_key not in r_img_up.text

    # Unexpected error on /image
    monkeypatch.setattr(
        colab_client,
        "image",
        lambda payload: (_ for _ in ()).throw(ValueError(f"Bug with token={secret_key}")),
    )
    r_img_int = c.post("/image", json={"product_name": "B", "visual_concept": "v"})
    assert r_img_int.status_code == 500
    assert secret_key not in r_img_int.text


@pytest.mark.skipif(app is None, reason="fastapi not installed")
def test_successful_endpoints_and_validation(monkeypatch):
    from app.services import colab_client

    monkeypatch.setattr(svc, "engine", lambda: "gemini")
    monkeypatch.setattr(svc, "directions", lambda payload: {"ok": True, "engine": "gemini", "echo": payload["product_name"]})
    monkeypatch.setattr(svc, "content", lambda u, s, d: {"ok": True, "engine": "gemini", "direction": d["name"]})
    monkeypatch.setattr(colab_client, "image", lambda payload: {"image": "data:image/png;base64,abc", "engine": "gemini"})

    c = TestClient(app)

    # 1. Successful requests
    dir_body = {
        "product_name": "Bottle",
        "product_description": "d",
        "target_audience": "a",
        "campaign_goal": "Sales",
        "brand_tone": "Playful",
    }
    r_dir = c.post("/directions", json=dir_body)
    assert r_dir.status_code == 200
    assert r_dir.json() == {"ok": True, "engine": "gemini", "echo": "Bottle"}

    cnt_body = {
        "user_input": dir_body,
        "campaign_strategy": {"core_message": "cm"},
        "direction": {"name": "Dir1"},
    }
    r_cnt = c.post("/content", json=cnt_body)
    assert r_cnt.status_code == 200
    assert r_cnt.json() == {"ok": True, "engine": "gemini", "direction": "Dir1"}

    img_body = {"product_name": "Bottle", "visual_concept": "Studio shot"}
    r_img = c.post("/image", json=img_body)
    assert r_img.status_code == 200
    assert r_img.json() == {"image": "data:image/png;base64,abc", "engine": "gemini"}

    # 2. Validation error handling (HTTP 422)
    r_val = c.post("/directions", json={"product_name": "Incomplete"})
    assert r_val.status_code == 422
    assert "detail" in r_val.json()
