import json
from collections import defaultdict
from pathlib import Path

from typer.testing import CliRunner

from daily_ai_insight.cli import app
from daily_ai_insight.normalize import load_raw_news
from daily_ai_insight.pipeline import run_pipeline

ALLOWED_CATEGORIES = {"model", "agent", "infrastructure", "application"}
ALLOWED_SOURCE_CHANNELS = {"official", "tech_media", "aggregator", "social_media"}
REQUIRED_RAW_FIELDS = {
    "title",
    "summary",
    "source",
    "url",
    "published_at",
    "source_channel",
    "source_language",
    "selection_reason",
    "collected_at",
}
MIXED_SAMPLE_PATH = Path("data/raw/mixed_channel_ai_news_sample.json").resolve()
EXPECTED_MIXED_PATH = Path("data/eval/expected_mixed_sample_categories.json").resolve()


def _mixed_items() -> list[dict[str, str]]:
    payload = json.loads(MIXED_SAMPLE_PATH.read_text(encoding="utf-8"))
    return payload["items"]


def test_mixed_channel_sample_exists():
    assert MIXED_SAMPLE_PATH.exists()


def test_mixed_sample_has_required_provenance_and_channel_coverage():
    items = _mixed_items()
    channels_by_language: dict[str, set[str]] = defaultdict(set)

    assert 10 <= len(items) <= 20
    assert len({item["title"] for item in items}) == len(items)

    for item in items:
        for field in REQUIRED_RAW_FIELDS:
            assert item.get(field), f"{item.get('title', '<missing title>')} missing {field}"

        assert item["url"].startswith("https://")
        assert item["source_channel"] in ALLOWED_SOURCE_CHANNELS
        assert item["source_language"] in {"en", "zh"}
        channels_by_language[item["source_channel"]].add(item["source_language"])

    assert set(channels_by_language) == ALLOWED_SOURCE_CHANNELS
    assert {item["source_language"] for item in items} == {"en", "zh"}
    for source_channel in ALLOWED_SOURCE_CHANNELS:
        assert channels_by_language[source_channel] == {"en", "zh"}


def test_expected_mixed_categories_fixture_aligns_with_raw_titles():
    assert EXPECTED_MIXED_PATH.exists()

    raw_titles = {item["title"] for item in _mixed_items()}
    expected_payload = json.loads(EXPECTED_MIXED_PATH.read_text(encoding="utf-8"))
    expected_titles = {item["title"] for item in expected_payload}

    assert len(expected_payload) == len(raw_titles)
    assert expected_titles == raw_titles
    for item in expected_payload:
        assert item["expected_category"] in ALLOWED_CATEGORIES
        assert item["reason"]


def test_mixed_sample_can_be_normalized_and_preserves_provenance():
    items = load_raw_news(MIXED_SAMPLE_PATH)

    assert 10 <= len(items) <= 20
    assert all(item.source_channel in ALLOWED_SOURCE_CHANNELS for item in items)
    assert all(item.source_language in {"en", "zh"} for item in items)
    assert all(item.selection_reason for item in items)
    assert all(item.collected_at for item in items)


def test_mixed_sample_pipeline_runs_with_rule_extractor(tmp_path):
    events_path = tmp_path / "mixed_structured_events.json"
    report_path = tmp_path / "mixed_daily_report.md"
    raw_items = load_raw_news(MIXED_SAMPLE_PATH)

    report = run_pipeline(
        MIXED_SAMPLE_PATH,
        extractor_name="rule",
        events_output_path=events_path,
        report_output_path=report_path,
    )

    assert report.total_events == len(raw_items)
    assert report.harness_summary["source_integrity_passed"] is True
    assert report.harness_summary["grounding_passed"] is True
    assert report.harness_summary["extractor_name"] == "rule"
    assert events_path.exists()
    assert report_path.exists()

    report_text = report_path.read_text(encoding="utf-8")
    for phrase in (
        "数据来源概览",
        "重点事件深度解读",
        "行业影响",
        "行业机会",
        "行业风险",
        "决策提示",
        "舆情监测与风险预警",
    ):
        assert phrase in report_text

    first_item = raw_items[0]
    assert first_item.source in report_text
    assert first_item.url in report_text
    assert first_item.published_at in report_text
    assert first_item.selection_reason in report_text


def test_cli_evaluate_runs_for_mixed_sample_with_rule(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "evaluate",
            "--input",
            str(MIXED_SAMPLE_PATH),
            "--expected",
            str(EXPECTED_MIXED_PATH),
            "--extractor",
            "rule",
            "--output-prefix",
            "mixed_rule",
        ],
    )

    assert result.exit_code == 0
    assert "评估完成。" in result.output
    assert Path("outputs/mixed_rule_evaluation_summary.json").exists()
    assert Path("outputs/mixed_rule_evaluation_report.md").exists()
