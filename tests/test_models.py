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


def test_structured_event_accepts_business_analysis_fields():
    event = StructuredAIEvent(
        **valid_event(
            source_channel="official",
            source_language="en",
            selection_reason="用于 AI 行业趋势分析。",
            collected_at="2026-06-03",
            background="该事件来自官方发布。",
            industry_impact="模型能力更新影响企业应用。",
            trend_signal="模型能力升级仍是行业趋势。",
            industry_risk="平台锁定和成本上升需要关注。",
            industry_opportunity="AI coding 和知识管理存在机会。",
            decision_hint="建议关注 API 成本和生态合作。",
            llm_generated=True,
            requires_human_review=True,
        )
    )

    assert event.background == "该事件来自官方发布。"
    assert event.industry_impact == "模型能力更新影响企业应用。"
    assert event.llm_generated is True
    assert event.requires_human_review is True


def test_structured_event_accepts_legacy_data_without_business_fields():
    event = StructuredAIEvent(**valid_event())

    assert event.background is None
    assert event.industry_risk is None
    assert event.llm_generated is False
    assert event.requires_human_review is False
