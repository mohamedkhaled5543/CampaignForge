import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


class Settings:
    """Reads environment variables at call time (easy to override in tests)."""

    @property
    def provider(self):  # auto | gemini | colab
        return os.getenv("PROVIDER", "auto").lower()

    @property
    def gemini_model(self):
        return os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    @property
    def colab_url(self):
        return os.getenv("COLAB_API_URL", "").rstrip("/")

    @property
    def kb_path(self):
        return os.getenv(
            "KB_PATH",
            str(ROOT / "knowledge_base" / "CampaignForge_Marketing_Knowledge_Base.pdf")
        )

    @property
    def index_dir(self):
        return os.getenv(
            "INDEX_DIR",
            str(ROOT / ".cache" / "faiss_index")
        )


settings = Settings()