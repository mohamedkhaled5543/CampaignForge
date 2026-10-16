from contextlib import contextmanager
import logging
import re
import urllib.error

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError
import requests

from app.config import ROOT
from app.services import campaign_service as svc
from app.services import colab_client

log = logging.getLogger("campaignforge.routes")
router = APIRouter()

UPSTREAM_ERRORS: tuple[type[Exception], ...] = (
    requests.RequestException,
    ConnectionError,
    TimeoutError,
    urllib.error.URLError,
)

try:
    from google.genai.errors import APIError as GenAIAPIError
    UPSTREAM_ERRORS = UPSTREAM_ERRORS + (GenAIAPIError,)
except ImportError:
    pass

try:
    import httpx
    UPSTREAM_ERRORS = UPSTREAM_ERRORS + (httpx.HTTPError,)
except ImportError:
    pass

UPSTREAM_ERROR_DETAIL = "Upstream service is currently unavailable. Please try again later."
INTERNAL_ERROR_DETAIL = "An unexpected internal error occurred. Please try again later."


def _sanitize(text: str) -> str:
    cleaned = re.sub(r'(https?://)[^/@\s]+@', r'\1***@', text)
    cleaned = re.sub(
        r'([?&](?:token|key|api_?key|secret|auth|password)=)[^&\s]+',
        r'\1***',
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r'\bAIza[0-9A-Za-z-_]{35}\b', '***', cleaned)
    cleaned = re.sub(r'\bBearer\s+[a-zA-Z0-9._-]+\b', 'Bearer ***', cleaned)
    return cleaned


def _is_upstream_error(exc: BaseException) -> bool:
    if isinstance(exc, UPSTREAM_ERRORS):
        return True
    if exc.__cause__ and isinstance(exc.__cause__, UPSTREAM_ERRORS):
        return True
    return False


def _safe_validation_detail(exc: ValidationError) -> list[dict]:
    return [
        {
            "loc": err.get("loc", ()),
            "msg": _sanitize(str(err.get("msg", "Invalid value"))),
            "type": err.get("type", "value_error"),
        }
        for err in exc.errors()
    ]


def _log_error(route_name: str, exc: Exception, is_upstream: bool) -> None:
    if exc.args:
        try:
            exc.args = tuple(_sanitize(str(a)) if isinstance(a, str) else a for a in exc.args)
        except Exception:
            pass

    sanitized_msg = _sanitize(str(exc))
    if is_upstream:
        log.error("Upstream failure on %s: %s", route_name, sanitized_msg, exc_info=True)
    else:
        log.error("Unexpected error on %s: %s", route_name, sanitized_msg, exc_info=True)


@contextmanager
def handle_route_errors(route_name: str):
    try:
        yield
    except HTTPException:
        raise
    except ValidationError as e:
        log.warning("Validation error on %s: %s", route_name, _sanitize(str(e)))
        raise HTTPException(status_code=422, detail=_safe_validation_detail(e))
    except Exception as e:
        if _is_upstream_error(e):
            _log_error(route_name, e, is_upstream=True)
            raise HTTPException(status_code=502, detail=UPSTREAM_ERROR_DETAIL)
        _log_error(route_name, e, is_upstream=False)
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR_DETAIL)


class CampaignInput(BaseModel):
    product_name: str
    product_description: str
    target_audience: str
    campaign_goal: str
    brand_tone: str
    language: str = "English"
    custom_tone: str | None = None
    offer_or_price: str | None = None
    key_differentiator: str | None = None


class ContentRequest(BaseModel):
    user_input: CampaignInput
    campaign_strategy: dict
    direction: dict


class ImageRequest(BaseModel):
    product_name: str
    product_description: str = ""
    visual_concept: str
    platform: str = "instagram"
    product_photo: str | None = None


@router.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")


@router.get("/health")
def health():
    return {"status": "ok", "engine": svc.engine()}


@router.post("/directions")
def directions_api(req: CampaignInput):
    with handle_route_errors("/directions"):
        return svc.directions(req.model_dump())


@router.post("/content")
def content_api(req: ContentRequest):
    with handle_route_errors("/content"):
        return svc.content(
            req.user_input.model_dump(),
            req.campaign_strategy,
            req.direction,
        )


@router.post("/image")
def image_api(req: ImageRequest):
    with handle_route_errors("/image"):
        return colab_client.image(req.model_dump())
