from pathlib import Path

from daily_ai_insight.normalize import load_raw_news
from daily_ai_insight.pipeline import run_pipeline

ALLOWED_CATEGORIES = {"model", "agent", "infrastructure", "application"}
REAL_SAMPLE_PATH = Path("data/raw/real_ai_news_sample.json")


def test_real_sample_can_be_normalized():
    items = load_raw_news(REAL_SAMPLE_PATH)

    assert 10 <= len(items) <= 20
    assert all(item.title for item in items)
    assert all(item.summary for item in items)
    assert all(item.source for item in items)
    assert all(item.url for item in items)


def test_real_sample_pipeline_runs_with_harness(tmp_path):
    events_path = tmp_path / "structured_events.json"
    report_path = tmp_path / "daily_report.md"
    raw_items = load_raw_news(REAL_SAMPLE_PATH)

    report = run_pipeline(
        REAL_SAMPLE_PATH,
        events_output_path=events_path,
        report_output_path=report_path,
    )

    assert report.total_events == len(raw_items)
    assert report.harness_summary
    assert report.harness_summary["source_integrity_passed"] is True
    assert report.harness_summary["grounding_passed"] is True
    assert report.harness_summary["steps_used"] <= report.harness_summary["max_processing_steps"]
    assert events_path.exists()
    assert report_path.exists()
    assert all(event.source for event in report.top_events)
    assert all(event.url for event in report.top_events)
    assert set(report.category_counts).issubset(ALLOWED_CATEGORIES)
    assert set(report.category_counts) == ALLOWED_CATEGORIES
