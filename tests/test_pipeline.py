from pathlib import Path

from daily_ai_insight.pipeline import run_pipeline


def test_sample_pipeline_runs_to_completion(tmp_path):
    events_path = tmp_path / "structured_events.json"
    report_path = tmp_path / "daily_report.md"

    report = run_pipeline(
        Path("data/raw/sample_ai_news.json"),
        events_output_path=events_path,
        report_output_path=report_path,
    )

    assert report.total_events == 12
    assert events_path.exists()
    assert report_path.exists()
    assert report.harness_summary["input_count"] == 12
    assert report.harness_summary["output_count"] == 12
    assert report.harness_summary["grounding_passed"] is True
    assert report.harness_summary["steps_used"] <= report.harness_summary["max_processing_steps"]
    assert all(event.source for event in report.top_events)
    assert all(event.url for event in report.top_events)
