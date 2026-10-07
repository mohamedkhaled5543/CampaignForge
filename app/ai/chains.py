from functools import lru_cache

from langchain_core.prompts import ChatPromptTemplate

from app import schemas
from app.ai import prompts
from app.ai.llm import get_llm


def _chain(pair, schema, max_tokens):
    prompt = ChatPromptTemplate.from_messages([("system", pair[0]), ("human", pair[1])])
    # schema-checked output + automatic retry on a bad response
    return (prompt | get_llm(max_tokens).with_structured_output(schema)).with_retry(stop_after_attempt=3)


@lru_cache(maxsize=None)
def product_chain():
    return _chain(prompts.PRODUCT, schemas.ProductUnderstanding, 1000)


@lru_cache(maxsize=None)
def strategy_chain():
    return _chain(prompts.STRATEGY, schemas.CampaignStrategy, 1000)


@lru_cache(maxsize=None)
def directions_chain():
    return _chain(prompts.DIRECTIONS, schemas.CampaignDirections, 2000)


@lru_cache(maxsize=None)
def platform_chain():
    return _chain(prompts.PLATFORM, schemas.CampaignContent, 2000)
