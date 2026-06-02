import pytest

from daily_ai_insight.errors import HarnessError, LoopGuardError, SourceIntegrityError
from daily_ai_insight.harness import HarnessConfig, PipelineHarness
from daily_ai_insight.models import RawNewsItem, StructuredAIEvent


def raw_item(index: int = 1, **overrides):
    data = {
        "title": f"OpenAI launches model update {index}",
        "summary": "OpenAI describes a model launch.",
        "source": "OpenAI News",
        "url": f"https://openai.com/news/{index}",
        "published_at": "2026-05-20",
        "language": "en",
    }
    data.update(overrides)
    return RawNewsItem(**data)


def event_from_raw(item: RawNewsItem, **overrides):
    data = {
        "id": "evt-001",
        "title": item.title,
        "source": item.source,
        "url": item.url,
        "published_at": item.published_at,
        "language": item.language,
        "category": "model",
        "event_type": "release",
        "entities": ["OpenAI"],
        "impact_areas": ["model_capabilities"],
        "importance_score": 7.0,
        "confidence": 0.7,
        "summary": item.summary,
        "evidence": f"{item.source}: {item.summary}",
    }
    data.update(overrides)
    return StructuredAIEvent(**data)


def test_check_input_size_rejects_too_few_items():
    harness = PipelineHarness()
    with pytest.raises(HarnessError, match="below minimum"):
        harness.check_input_size([raw_item(i) for i in range(9)])


def test_check_input_size_rejects_too_many_items():
    harness = PipelineHarness()
    with pytest.raises(HarnessError, match="exceeds maximum"):
        harness.check_input_size([raw_item(i) for i in range(21)])


@pytest.mark.parametrize("url", ["fake://source", "hallucinated://source"])
def test_check_source_integrity_rejects_fake_urls(url):
    harness = PipelineHarness(HarnessConfig(min_items=1))
    with pytest.raises(SourceIntegrityError):
        harness.check_source_integrity([raw_item(url=url)])


def test_check_step_budget_rejects_exceeded_budget():
    harness = PipelineHarness(HarnessConfig(max_processing_steps=2))
    harness.check_step_budget(2)
    with pytest.raises(LoopGuardError):
        harness.check_step_budget(3)


def test_event_grounding_rejects_unknown_source_url():
    item = raw_item()
    event = event_from_raw(item, source="Unknown Source", url="https://unknown.example/")
    harness = PipelineHarness(HarnessConfig(min_items=1))

    with pytest.raises(HarnessError, match="not grounded"):
        harness.check_event_grounding([event], [item])


def test_confidence_rejects_below_threshold():
    item = raw_item()
    event = event_from_raw(item, confidence=0.4)
    harness = PipelineHarness(HarnessConfig(min_confidence=0.5))

    with pytest.raises(HarnessError, match="below threshold"):
        harness.check_confidence([event])
