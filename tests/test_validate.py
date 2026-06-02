import pytest

from daily_ai_insight.errors import ValidationError
from daily_ai_insight.validate import validate_raw_items, validate_structured_events


def valid_event_dict(**overrides):
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


def test_validate_raw_items_rejects_empty_list():
    with pytest.raises(ValidationError, match="input is empty"):
        validate_raw_items([])


def test_validate_structured_events_rejects_empty_url():
    with pytest.raises(ValidationError, match="failed schema validation"):
        validate_structured_events([valid_event_dict(url="")])
