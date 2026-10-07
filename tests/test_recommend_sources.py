from types import SimpleNamespace as D

from app.rag.sources import format_knowledge_sources
from app.services.recommend import recommend_direction


def test_recommend_by_goal():
    assert recommend_direction("Sales")["key"] == "conversion_focused"
    assert recommend_direction("Launch")["key"] == "product_focused"
    assert recommend_direction("Awareness")["key"] == "lifestyle_focused"


def test_sources_label_and_excerpt():
    docs = [D(page_content="Emotional Marketing Angles\n" + "text " * 100, metadata={"page": 2}),
            D(page_content="a sentence that just keeps going without being a heading at all, ok.", metadata={"page": 0})]
    out = format_knowledge_sources(docs)
    assert out[0]["section"] == "Emotional Marketing Angles" and out[0]["page"] == 3
    assert out[0]["excerpt"].endswith("...")
    assert out[1]["section"] == "Knowledge base, page 1"
