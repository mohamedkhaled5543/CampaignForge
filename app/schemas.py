
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class CampaignGoal(str, Enum):
    AWARENESS = "Awareness"
    ENGAGEMENT = "Engagement"
    SALES = "Sales"
    LAUNCH = "Launch"


class BrandTone(str, Enum):
    PROFESSIONAL = "Professional"
    PLAYFUL = "Playful"
    LUXURY = "Luxury"
    BOLD = "Bold"
    FRIENDLY = "Friendly"
    CUSTOM = "Custom"


class UserInput(BaseModel):
    product_name: str = Field(min_length=1)
    product_description: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)

    campaign_goal: CampaignGoal
    brand_tone: BrandTone
    language: str = "English"

    custom_tone: Optional[str] = None
    offer_or_price: Optional[str] = None
    key_differentiator: Optional[str] = None


class ProductUnderstanding(BaseModel):
    features: list[str]
    benefits: list[str]
    pain_points: list[str]
    customer_desires: list[str]
    product_positioning: str


class CampaignStrategy(BaseModel):
    core_message: str
    value_proposition: str
    emotional_angle: str
    cta: str
    content_pillars: list[str]


class CampaignDirection(BaseModel):
    name: str
    strategic_angle: str
    key_message: str
    recommended_cta: str
    content_approach: str


class CampaignDirections(BaseModel):
    product_focused: CampaignDirection
    lifestyle_focused: CampaignDirection
    conversion_focused: CampaignDirection


class PlatformContent(BaseModel):
    hook: str
    caption: str
    cta: str
    hashtags: list[str]
    visual_concept: str


class CampaignContent(BaseModel):
    instagram: PlatformContent
    tiktok: PlatformContent


class CampaignState(BaseModel):
    user_input: UserInput
    product_understanding: ProductUnderstanding
    campaign_strategy: CampaignStrategy
    campaign_directions: Optional[CampaignDirections] = None
    selected_direction: Optional[str] = None
    platform_content: Optional[CampaignContent] = None


class FinalCampaign(BaseModel):
    product_name: str
    campaign_goal: str
    brand_tone: str

    campaign_strategy: CampaignStrategy
    selected_direction: CampaignDirection

    instagram: PlatformContent
    tiktok: PlatformContent

