import json
from pathlib import Path

from typer.testing import CliRunner

from daily_ai_insight.cli import app
from daily_ai_insight.models import EvaluationItemResult, EvaluationSummary
from daily_ai_insight.reviewer import (
    RuleBasedReviewer,
    load_evaluation_summary,
    write_review_outputs,
)

REAL_SAMPLE_PATH = Path("data/raw/real_ai_news_sample.json").resolve()
EXPECTED_PATH = Path("data/eval/expected_real_sample_categories.json").resolve()


def make_summary(
    *,
    extractor: str = "rule",
    accuracy: float = 0.4,
    failed_items: int = 0,
    confidence: float = 0.7,
) -> EvaluationSummary:
    results = [
        EvaluationItemResult(
            title="Matching item",
            expected_category="model",
            predicted_category="model",
            category_match=True,
            confidence=confidence,
            grounded=True,
            error=None,
        ),
        EvaluationItemResult(
            title="Mismatched item",
            expected_category="agent",
            predicted_category="model",
            category_match=False,
            confidence=confidence,
            grounded=True,
            error=None,
        ),
    ]
    if failed_items:
        results.append(
            EvaluationItemResult(
                title="Failed item",
                expected_category="application",
                predicted_category=None,
                category_match=False,
                confidence=None,
                grounded=False,
                error="schema failure",
            )
        )

    total_items = len(results)
    successful_items = total_items - failed_items
    return EvaluationSummary(
        extractor=extractor,
        total_items=total_items,
        successful_items=successful_items,
        failed_items=failed_items,
        category_accuracy=accuracy,
        grounding_pass_rate=1.0 if not failed_items else 2 / total_items,
        average_confidence=confidence,
        item_results=results,
    )


def test_reviewer_can_read_evaluation_summary(tmp_path):
    summary_path = tmp_path / "evaluation_summary.json"
    expected = make_summary()
    summary_path.write_text(json.dumps(expected.model_dump(mode="json")), encoding="utf-8")

    loaded = load_evaluation_summary(summary_path)

    assert loaded.extractor == "rule"
    assert loaded.total_items == expected.total_items


def test_reviewer_detects_low_category_accuracy(tmp_path):
    report_path = tmp_path / "evaluation_report.md"
    daily_report_path = tmp_path / "daily_report.md"
    report_path.write_text("# Evaluation", encoding="utf-8")
    daily_report_path.write_text("# Daily", encoding="utf-8")

    summary = RuleBasedReviewer().review(
        evaluation=make_summary(accuracy=0.38),
        evaluation_report_path=report_path,
        daily_report_path=daily_report_path,
    )

    titles = {issue.title for issue in summary.issues}
    assert "分类准确率低于展示阈值" in titles
    assert summary.warning_count >= 1


def test_reviewer_compares_rule_vs_llm_accuracy(tmp_path):
    report_path = tmp_path / "llm_evaluation_report.md"
    daily_report_path = tmp_path / "daily_report.md"
    report_path.write_text("# Evaluation", encoding="utf-8")
    daily_report_path.write_text("# Daily", encoding="utf-8")

    summary = RuleBasedReviewer().review(
        evaluation=make_summary(extractor="openai-compatible", accuracy=0.69, confidence=0.92),
        baseline=make_summary(extractor="rule", accuracy=0.38),
        evaluation_report_path=report_path,
        daily_report_path=daily_report_path,
    )

    assert any(issue.title == "Extractor 相比 baseline 有提升" for issue in summary.issues)


def test_reviewer_writes_review_outputs(tmp_path):
    summary = RuleBasedReviewer().review(
        evaluation=make_summary(),
        evaluation_report_path=tmp_path / "missing_evaluation_report.md",
        daily_report_path=tmp_path / "missing_daily_report.md",
    )

    json_path, report_path = write_review_outputs(
        summary,
        summary_path=tmp_path / "outputs/review_summary.json",
        report_path=tmp_path / "outputs/review_report.md",
    )

    assert json_path.exists()
    assert report_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["final_verdict"] == summary.final_verdict


def test_cli_review_generates_outputs(tmp_path, monkeypatch):
    evaluation = make_summary(extractor="openai-compatible", accuracy=0.69, confidence=0.92)
    baseline = make_summary(extractor="rule", accuracy=0.38)
    evaluation_path = tmp_path / "llm_evaluation_summary.json"
    baseline_path = tmp_path / "rule_evaluation_summary.json"
    report_path = tmp_path / "llm_evaluation_report.md"
    daily_report_path = tmp_path / "outputs/daily_report.md"
    evaluation_path.write_text(json.dumps(evaluation.model_dump(mode="json")), encoding="utf-8")
    baseline_path.write_text(json.dumps(baseline.model_dump(mode="json")), encoding="utf-8")
    report_path.write_text("# Evaluation", encoding="utf-8")
    daily_report_path.parent.mkdir(parents=True, exist_ok=True)
    daily_report_path.write_text("# Daily", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "review",
            "--evaluation",
            str(evaluation_path),
            "--baseline",
            str(baseline_path),
        ],
    )

    assert result.exit_code == 0
    assert "复审完成。" in result.output
    assert Path("outputs/review_summary.json").exists()
    assert Path("outputs/review_report.md").exists()


def test_cli_evaluate_supports_output_prefix(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "evaluate",
            "--input",
            str(REAL_SAMPLE_PATH),
            "--expected",
            str(EXPECTED_PATH),
            "--extractor",
            "rule",
            "--output-prefix",
            "rule",
        ],
    )

    assert result.exit_code == 0
    assert Path("outputs/rule_evaluation_summary.json").exists()
    assert Path("outputs/rule_evaluation_report.md").exists()


def test_cli_evaluate_without_output_prefix_preserves_default_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
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
    assert Path("outputs/evaluation_summary.json").exists()
    assert Path("outputs/evaluation_report.md").exists()

    payload = json.loads(Path("outputs/evaluation_summary.json").read_text(encoding="utf-8"))
    assert payload["extractor"] == "rule"
