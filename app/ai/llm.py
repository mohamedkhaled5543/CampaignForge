import os
from app.config import settings


def gemini_ready():
    return bool(os.getenv("GOOGLE_API_KEY"))


def get_llm(max_tokens=1500):
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=0.3,
        max_output_tokens=max_tokens,
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )
