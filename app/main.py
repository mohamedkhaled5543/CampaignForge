from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import ROOT

app = FastAPI(title="CampaignForge AI")
app.include_router(router)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
