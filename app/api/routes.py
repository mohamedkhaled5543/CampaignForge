from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError

from app.config import ROOT
from app.services import campaign_service as svc
from app.services import colab_client

router = APIRouter()


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
    try:
        return svc.directions(req.model_dump())
    except ValidationError as e:
        raise HTTPException(422, str(e))


@router.post("/content")
def content_api(req: ContentRequest):
    try:
        return svc.content(
            req.user_input.model_dump(),
            req.campaign_strategy,
            req.direction
        )
    except ValidationError as e:
        raise HTTPException(422, str(e))


@router.post("/image")
def image_api(req: ImageRequest):
    try:
        return colab_client.image(req.model_dump())
    except Exception as e:
        raise HTTPException(502, f"Image generation unavailable: {e}")
