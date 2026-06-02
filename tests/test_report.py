from daily_ai_insight.models import StructuredAIEvent
from daily_ai_insight.report import build_daily_report, write_report


def test_report_markdown_is_generated(tmp_path):
    event = StructuredAIEvent(
        id="evt-001",
        title="OpenAI launches model update",
        source="OpenAI News",
        url="https://openai.com/news/",
        published_at="2026-05-20",
        language="en",
        category="model",
        event_type="release",
        entities=["OpenAI"],
        impact_areas=["model_capabilities"],
        importance_score=7.0,
        confidence=0.7,
        summary="OpenAI describes a model launch.",
        evidence="OpenAI News: OpenAI describes a model launch.",
    )
    report = build_daily_report(
        [event],
        {
            "input_count": 1,
            "output_count": 1,
            "source_integrity_passed": True,
            "grounding_passed": True,
            "loop_guard_passed": True,
            "min_confidence": 0.5,
            "deterministic_baseline": True,
            "steps_used": 7,
            "max_processing_steps": 8,
        },
        report_date="2026-05-27",
    )

    path = write_report(report, tmp_path / "daily_report.md")
    text = path.read_text(encoding="utf-8")

    assert "Harness Summary" in text
    assert "Trend Signals" in text
    assert "Risks and Opportunities" in text
    assert "Methodology Note" in text
    assert "deterministic baseline" in text
    assert report.trend_signals
    assert report.risks_and_opportunities
