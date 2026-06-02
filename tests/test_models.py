import pytest
from pydantic import ValidationError as PydanticValidationError

from daily_ai_insight.models import RawNewsItem, StructuredAIEvent


def valid_raw_item(**overrides):
    data = {
        "title": "OpenAI launches model update",
        "summary": "OpenAI describes a model launch.",
        "source": "OpenAI News",
        "url": "https://openai.com/news/",
        "published_at": "2026-05-20",
        "language": "en",
    }
    data.update(overrides)
    return data


def valid_event(**overrides):
    data = {
        "id": "evt-001",
        "title": "OpenAI launches model update",
        "source": "OpenAI News",
        "url": "https://openai.com/news/",
        "published_at": "2026-05-20",
        "language": "en",
        "category": "model",
        "event_type": "release",
        "entities": ["OpenAI"],
        "impact_areas": ["model_capabilities"],
        "importance_score": 7.0,
        "confidence": 0.7,
        "summary": "OpenAI describes a model launch.",
        "evidence": "OpenAI News: OpenAI describes a model launch.",
    }
    data.update(overrides)
    return data


def test_raw_news_item_normal_create():
    item = RawNewsItem(**valid_raw_item())
    assert item.title == "OpenAI launches model update"
    assert item.url == "https://openai.com/news/"


@pytest.mark.parametrize("field", ["title", "source", "url"])
def test_raw_news_item_rejects_empty_required_fields(field):
    with pytest.raises(PydanticValidationError):
        RawNewsItem(**valid_raw_item(**{field: "  "}))


def test_structured_event_rejects_importance_out_of_range():
    with pytest.raises(PydanticValidationError):
        StructuredAIEvent(**valid_event(importance_score=11))


def test_structured_event_rejects_confidence_out_of_range():
    with pytest.raises(PydanticValidationError):
        StructuredAIEvent(**valid_event(confidence=1.1))
