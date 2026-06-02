import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from daily_ai_insight.cli import app
from daily_ai_insight.errors import PipelineError
from daily_ai_insight.evaluate import run_evaluation
from daily_ai_insight.extractors import RuleBasedExtractor
from daily_ai_insight.models import RawNewsItem, StructuredAIEvent

REAL_SAMPLE_PATH = Path("data/raw/real_ai_news_sample.json").resolve()
EXPECTED_PATH = Path("data/eval/expected_real_sample_categories.json").resolve()


class OneItemFailingExtractor(RuleBasedExtractor):
    name = "rule"

    def extract(self, raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
        events = super().extract(raw_items)
        if raw_items[0].title == "Work with Codex from anywhere":
            events[0].confidence = 0.2
        return events


def test_rule_extractor_generates_evaluation_summary():
    summary = run_evaluation(
        input_path=REAL_SAMPLE_PATH,
        expected_path=EXPECTED_PATH,
        extractor_name="rule",
    )

    assert summary.extractor == "rule"
    assert summary.total_items == 13
    assert summary.successful_items == 13
    assert summary.failed_items == 0
    assert 0 <= summary.category_accuracy <= 1
    assert 0 <= summary.grounding_pass_rate <= 1
    assert 0 <= summary.average_confidence <= 1
    assert len(summary.item_results) == 13


def test_failed_item_is_recorded_without_crashing_evaluation():
    summary = run_evaluation(
        input_path=REAL_SAMPLE_PATH,
        expected_path=EXPECTED_PATH,
        extractor=OneItemFailingExtractor(),
    )

    assert summary.failed_items == 1
    assert summary.successful_items == summary.total_items - 1
    failed = [item for item in summary.item_results if item.error]
    assert len(failed) == 1
    assert "below threshold" in failed[0].error


def test_cli_evaluate_generates_outputs(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "evaluate",
            "--input",
            str(REAL_SAMPLE_PATH),
            "--expected",
            str(EXPECTED_PATH),
            "--extractor",
            "rule",
        ],
    )

    assert result.exit_code == 0
    assert "Evaluation completed." in result.output
    assert Path("outputs/evaluation_summary.json").exists()
    assert Path("outputs/evaluation_report.md").exists()

    payload = json.loads(Path("outputs/evaluation_summary.json").read_text(encoding="utf-8"))
    assert payload["extractor"] == "rule"


def test_expected_fixture_title_mismatch_has_clear_error(tmp_path):
    fixture = tmp_path / "expected.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "title": "Not a real title",
                    "expected_category": "model",
                    "reason": "Intentional mismatch",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(PipelineError, match="titles do not match"):
        run_evaluation(
            input_path=REAL_SAMPLE_PATH,
            expected_path=fixture,
            extractor_name="rule",
        )
