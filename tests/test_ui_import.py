import importlib
from pathlib import Path

from daily_ai_insight import evaluate, pipeline, reviewer
from daily_ai_insight.models import DailyInsightReport, StructuredAIEvent


def test_app_imports_without_starting_streamlit_server():
    app = importlib.import_module("app")

    assert callable(app.main)


def test_ui_reuses_existing_pipeline_evaluate_and_reviewer_functions():
    app = importlib.import_module("app")

    assert app.run_pipeline is pipeline.run_pipeline
    assert app.run_evaluation is evaluate.run_evaluation
    assert app.run_review is reviewer.run_review


def test_ui_detects_bundled_real_sample():
    app = importlib.import_module("app")

    assert app.is_bundled_real_sample(Path("data/raw/real_ai_news_sample.json"))
    assert not app.is_bundled_real_sample(Path("data/raw/sample_ai_news.json"))


def test_ui_openai_key_helper_handles_missing_key(monkeypatch):
    app = importlib.import_module("app")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    assert app.is_openai_key_configured() is False


def test_ui_pipeline_chart_helpers_use_report_data():
    app = importlib.import_module("app")
    event = StructuredAIEvent(
        id="evt-001",
        title="OpenAI launches model update",
        source="OpenAI",
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
        evidence="OpenAI: OpenAI describes a model launch.",
    )
    report = DailyInsightReport(
        date="2026-06-02",
        total_events=1,
        top_events=[event],
        category_counts={"model": 1},
        key_takeaways=["model leads the sample."],
        trend_signals=["model momentum is visible."],
        risks_and_opportunities=["Opportunity: model launch."],
        harness_summary={"extractor_name": "rule"},
    )

    assert app.category_distribution_chart_data(report) == [{"category": "model", "count": 1}]
    assert app.top_events_importance_chart_data(report) == [
        {"title": "OpenAI launches model update", "importance_score": 7.0}
    ]


def test_ui_extractor_accuracy_comparison_handles_missing_files(tmp_path):
    app = importlib.import_module("app")

    assert app.extractor_accuracy_comparison_chart_data(
        rule_path=tmp_path / "missing_rule.json",
        llm_path=tmp_path / "missing_llm.json",
    ) == []
