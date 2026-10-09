
import logging

from app import schemas
from app.ai.guardrails import find_violations
from app.ai.llm import gemini_ready
from app.config import settings
from app.rag.sources import format_knowledge_sources
from app.services import colab_client
from app.services.recommend import recommend_direction

log = logging.getLogger("campaignforge")


# ---------- engine selection ----------
def use_colab():
    p = settings.provider
    if p == "colab":
        return True
    if p == "gemini":
        return False
    return bool(settings.colab_url) and colab_client.alive()


def engine():
    return "colab" if use_colab() else "gemini"


# ---------- helpers ----------
def _base(ui):
    return {
        "product_name": ui.product_name,
        "product_description": ui.product_description,
        "target_audience": ui.target_audience,
        "campaign_goal": ui.campaign_goal.value,
        "brand_tone": ui.brand_tone.value,
        "language": ui.language,
        "offer_or_price": ui.offer_or_price or "Not provided",
        "key_differentiator": ui.key_differentiator or "Not provided",
    }


def _strategy_fields(s):
    return {
        "core_message": s.core_message,
        "value_proposition": s.value_proposition,
        "emotional_angle": s.emotional_angle,
        "cta": s.cta,
        "content_pillars": s.content_pillars,
    }


# ---------- Gemini pipeline ----------
def generate_directions(ui):
    from app.ai import chains
    from app.rag.retriever import retrieve_knowledge

    base = _base(ui)
    docs = retrieve_knowledge(ui)
    product = chains.product_chain().invoke(base)

    und = {
        "features": product.features,
        "benefits": product.benefits,
        "pain_points": product.pain_points,
        "customer_desires": product.customer_desires,
        "product_positioning": product.product_positioning,
    }

    context = "\n\n".join(d.page_content for d in docs)

    strategy = chains.strategy_chain().invoke(
        {**base, **und, "marketing_knowledge": context}
    )

    directions = chains.directions_chain().invoke(
        {**base, **und, **_strategy_fields(strategy)}
    )

    return {
        "product_understanding": product.model_dump(),
        "campaign_strategy": strategy.model_dump(),
        "campaign_directions": directions.model_dump(),
        "knowledge_used": format_knowledge_sources(docs),
        "recommended": recommend_direction(base["campaign_goal"]),
        "engine": "gemini",
    }


def generate_content(ui, strategy, direction):
    from app.ai import chains

    inputs = {
        **_base(ui),
        **_strategy_fields(strategy),
        "direction_name": direction.name,
        "strategic_angle": direction.strategic_angle,
        "key_message": direction.key_message,
        "recommended_cta": direction.recommended_cta,
        "content_approach": direction.content_approach,
    }

    allowed = " ".join(
        filter(
            None,
            [
                ui.offer_or_price,
                ui.product_description,
                ui.key_differentiator,
            ],
        )
    )

    best, best_v = None, None

    for _ in range(2):
        platform = chains.platform_chain().invoke(inputs)
        v = find_violations(platform.model_dump(), allowed)

        if best is None or len(v) < len(best_v):
            best, best_v = platform, v

        if not v:
            break

    final = schemas.FinalCampaign(
        product_name=ui.product_name,
        campaign_goal=ui.campaign_goal.value,
        brand_tone=ui.brand_tone.value,
        campaign_strategy=strategy,
        selected_direction=direction,
        instagram=best.instagram,
        tiktok=best.tiktok,
    )

    return {
        **final.model_dump(),
        "warnings": best_v,
        "engine": "gemini",
    }


# ---------- entry points used by the routes ----------
def directions(payload):
    if use_colab():
        try:
            return colab_client.directions(payload)
        except Exception as e:
            log.warning("Colab engine failed (%s)", e)
            if not gemini_ready():
                raise

    return generate_directions(schemas.UserInput(**payload))


def content(user_input, strategy, direction):
    if use_colab():
        try:
            return colab_client.content(
                {
                    "user_input": user_input,
                    "campaign_strategy": strategy,
                    "direction": direction,
                    "language": user_input.get("language") or "English",
                }
            )
        except Exception as e:
            log.warning("Colab engine failed (%s)", e)
            if not gemini_ready():
                raise

    return generate_content(
        schemas.UserInput(**user_input),
        schemas.CampaignStrategy(**strategy),
        schemas.CampaignDirection(**direction),
    )