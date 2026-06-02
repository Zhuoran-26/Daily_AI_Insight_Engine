"""Deterministic AI reviewer workflow for evaluation artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Template
from pydantic import BaseModel, ConfigDict, Field, field_validator

from daily_ai_insight.models import EvaluationSummary

MIN_CONFIDENCE_FOR_SHOWCASE = 0.7
LOW_ACCURACY_THRESHOLD = 0.5
MEANINGFUL_ACCURACY_DELTA = 0.05
DEFAULT_REVIEW_SUMMARY_PATH = Path("outputs/review_summary.json")
DEFAULT_REVIEW_REPORT_PATH = Path("outputs/review_report.md")
DEFAULT_DAILY_REPORT_PATH = Path("outputs/daily_report.md")

REVIEW_REPORT_TEMPLATE = """# AI Reviewer Report

## Summary

- Final verdict: {{ summary.final_verdict }}
- Total issues: {{ summary.total_issues }}
- Errors: {{ summary.error_count }}
- Warnings: {{ summary.warning_count }}
- Info: {{ summary.info_count }}

## Issues

| Severity | Area | Title | Suggested Action |
| --- | --- | --- | --- |
{% for issue in summary.issues -%}
| {{ issue.severity }} | {{ issue.area }} | {{ issue.title }} | {{ issue.suggested_action }} |
{% endfor %}

## Details

{% for issue in summary.issues -%}
### {{ issue.title }}

- Severity: {{ issue.severity }}
- Area: {{ issue.area }}
- Detail: {{ issue.detail }}
- Suggested action: {{ issue.suggested_action }}

{% endfor -%}

## Methodology Note

This deterministic reviewer is a critique layer over evaluation artifacts. It does not replace harness validation, and it does not call an LLM. Its purpose is to surface mismatch patterns, failed items, confidence risks, missing artifacts, and baseline comparison signals so the next revise step can be deliberate.
"""


class ReviewIssue(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    severity: str
    area: str
    title: str
    detail: str
    suggested_action: str

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        allowed = {"info", "warning", "error"}
        if value not in allowed:
            raise ValueError(f"severity must be one of {sorted(allowed)}")
        return value

    @field_validator("area")
    @classmethod
    def validate_area(cls, value: str) -> str:
        allowed = {"grounding", "schema", "confidence", "category", "report"}
        if value not in allowed:
            raise ValueError(f"area must be one of {sorted(allowed)}")
        return value


class ReviewSummary(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    total_issues: int = Field(ge=0)
    error_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    info_count: int = Field(ge=0)
    issues: list[ReviewIssue]
    final_verdict: str


class RuleBasedReviewer:
    """Review evaluation summaries with bounded deterministic checks."""

    name = "rule-based-reviewer"

    def review(
        self,
        evaluation: EvaluationSummary,
        baseline: EvaluationSummary | None = None,
        evaluation_report_path: Path | None = None,
        daily_report_path: Path = DEFAULT_DAILY_REPORT_PATH,
    ) -> ReviewSummary:
        issues: list[ReviewIssue] = []

        issues.extend(self._review_failed_items(evaluation))
        issues.extend(self._review_category_quality(evaluation))
        issues.extend(self._review_grounding(evaluation))
        issues.extend(self._review_confidence(evaluation))
        issues.extend(self._review_baseline_comparison(evaluation, baseline))
        issues.extend(self._review_artifacts(evaluation_report_path, daily_report_path))

        return build_review_summary(issues)

    def _review_failed_items(self, evaluation: EvaluationSummary) -> list[ReviewIssue]:
        if evaluation.failed_items == 0:
            return [
                ReviewIssue(
                    severity="info",
                    area="schema",
                    title="No failed evaluation items",
                    detail=f"All {evaluation.total_items} items produced valid evaluation results.",
                    suggested_action="Keep the current schema and harness checks in the evaluation path.",
                )
            ]

        failed_titles = [item.title for item in evaluation.item_results if item.error]
        return [
            ReviewIssue(
                severity="error",
                area="schema",
                title="Failed evaluation items detected",
                detail=f"{evaluation.failed_items} items failed evaluation: {failed_titles}",
                suggested_action="Inspect failed item errors before using this extractor result in a showcase comparison.",
            )
        ]

    def _review_category_quality(self, evaluation: EvaluationSummary) -> list[ReviewIssue]:
        mismatches = [item for item in evaluation.item_results if item.error is None and not item.category_match]
        issues: list[ReviewIssue] = []

        if mismatches:
            issues.append(
                ReviewIssue(
                    severity="warning",
                    area="category",
                    title="Category mismatches detected",
                    detail=f"{len(mismatches)} successful items were classified differently from the expected fixture.",
                    suggested_action="Review mismatched titles and update extractor rules, prompts, or expected fixture notes if justified.",
                )
            )

        if evaluation.category_accuracy < LOW_ACCURACY_THRESHOLD:
            issues.append(
                ReviewIssue(
                    severity="warning",
                    area="category",
                    title="Category accuracy is below showcase threshold",
                    detail=(
                        f"{evaluation.extractor} accuracy is {evaluation.category_accuracy:.2f}, "
                        f"below the {LOW_ACCURACY_THRESHOLD:.2f} reviewer threshold."
                    ),
                    suggested_action="Use this result to explain baseline limitations or revise extraction logic before claiming quality gains.",
                )
            )

        return issues

    def _review_grounding(self, evaluation: EvaluationSummary) -> list[ReviewIssue]:
        if evaluation.grounding_pass_rate >= 1.0:
            return [
                ReviewIssue(
                    severity="info",
                    area="grounding",
                    title="Grounding pass rate is complete",
                    detail="Every evaluated item passed source grounding checks.",
                    suggested_action="Keep source and URL preservation mandatory for all extractor modes.",
                )
            ]

        return [
            ReviewIssue(
                severity="error",
                area="grounding",
                title="Grounding pass rate below 1.0",
                detail=f"Grounding pass rate is {evaluation.grounding_pass_rate:.2f}; at least one item is not grounded.",
                suggested_action="Block this extractor result from final reporting until source grounding failures are fixed.",
            )
        ]

    def _review_confidence(self, evaluation: EvaluationSummary) -> list[ReviewIssue]:
        if evaluation.average_confidence >= MIN_CONFIDENCE_FOR_SHOWCASE:
            return [
                ReviewIssue(
                    severity="info",
                    area="confidence",
                    title="Average confidence meets threshold",
                    detail=(
                        f"Average confidence is {evaluation.average_confidence:.2f}, "
                        f"meeting the {MIN_CONFIDENCE_FOR_SHOWCASE:.2f} threshold."
                    ),
                    suggested_action="Continue reporting confidence distribution alongside accuracy.",
                )
            ]

        return [
            ReviewIssue(
                severity="warning",
                area="confidence",
                title="Average confidence below threshold",
                detail=(
                    f"Average confidence is {evaluation.average_confidence:.2f}, "
                    f"below the {MIN_CONFIDENCE_FOR_SHOWCASE:.2f} reviewer threshold."
                ),
                suggested_action="Send low-confidence results to review or fail fast before using them in the final report.",
            )
        ]

    def _review_baseline_comparison(
        self,
        evaluation: EvaluationSummary,
        baseline: EvaluationSummary | None,
    ) -> list[ReviewIssue]:
        if baseline is None:
            return [
                ReviewIssue(
                    severity="info",
                    area="category",
                    title="No baseline comparison provided",
                    detail="Reviewer received only one evaluation summary.",
                    suggested_action="Provide a rule baseline summary when making extractor quality claims.",
                )
            ]

        delta = evaluation.category_accuracy - baseline.category_accuracy
        if delta <= MEANINGFUL_ACCURACY_DELTA:
            return [
                ReviewIssue(
                    severity="warning",
                    area="category",
                    title="Extractor accuracy is not clearly above baseline",
                    detail=(
                        f"{evaluation.extractor} accuracy is {evaluation.category_accuracy:.2f}; "
                        f"{baseline.extractor} baseline accuracy is {baseline.category_accuracy:.2f}; "
                        f"delta is {delta:.2f}."
                    ),
                    suggested_action="Avoid claiming LLM quality improvement until evaluation shows a meaningful gain.",
                )
            ]

        return [
            ReviewIssue(
                severity="info",
                area="category",
                title="Extractor improves over baseline",
                detail=(
                    f"{evaluation.extractor} accuracy is {evaluation.category_accuracy:.2f}; "
                    f"{baseline.extractor} baseline accuracy is {baseline.category_accuracy:.2f}; "
                    f"delta is {delta:.2f}."
                ),
                suggested_action="Use this comparison in the showcase, while still explaining remaining mismatches.",
            )
        ]

    def _review_artifacts(
        self,
        evaluation_report_path: Path | None,
        daily_report_path: Path,
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []

        if evaluation_report_path is None:
            issues.append(
                ReviewIssue(
                    severity="warning",
                    area="report",
                    title="Evaluation report path not provided",
                    detail="Reviewer could not verify whether a Markdown evaluation report exists.",
                    suggested_action="Pass the evaluation report path or use the CLI default inference.",
                )
            )
        elif evaluation_report_path.exists():
            issues.append(
                ReviewIssue(
                    severity="info",
                    area="report",
                    title="Evaluation report exists",
                    detail=f"Found evaluation report at {evaluation_report_path}.",
                    suggested_action="Use the report as the human-readable quality artifact.",
                )
            )
        else:
            issues.append(
                ReviewIssue(
                    severity="warning",
                    area="report",
                    title="Evaluation report is missing",
                    detail=f"Expected evaluation report at {evaluation_report_path}.",
                    suggested_action="Run the evaluation CLI again so reviewers can inspect the Markdown report.",
                )
            )

        if daily_report_path.exists():
            issues.append(
                ReviewIssue(
                    severity="info",
                    area="report",
                    title="Daily report exists",
                    detail=f"Found daily report at {daily_report_path}.",
                    suggested_action="Use the daily report as the final generated artifact after validating evaluation results.",
                )
            )
        else:
            issues.append(
                ReviewIssue(
                    severity="warning",
                    area="report",
                    title="Daily report is missing",
                    detail=f"Expected daily report at {daily_report_path}.",
                    suggested_action="Run the pipeline before final demo so the report artifact is available.",
                )
            )

        return issues


def build_review_summary(issues: list[ReviewIssue]) -> ReviewSummary:
    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    info_count = sum(1 for issue in issues if issue.severity == "info")

    if error_count:
        final_verdict = "needs_revision"
    elif warning_count:
        final_verdict = "reviewed_with_warnings"
    else:
        final_verdict = "approved_for_showcase"

    return ReviewSummary(
        total_issues=len(issues),
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        issues=issues,
        final_verdict=final_verdict,
    )


def load_evaluation_summary(summary_path: Path) -> EvaluationSummary:
    payload = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    return EvaluationSummary.model_validate(payload)


def infer_evaluation_report_path(summary_path: Path) -> Path:
    path = Path(summary_path)
    if path.name.endswith("_summary.json"):
        return path.with_name(path.name.removesuffix("_summary.json") + "_report.md")
    return path.with_name(path.stem + "_report.md")


def run_review(
    evaluation_path: Path,
    baseline_path: Path | None = None,
    evaluation_report_path: Path | None = None,
    daily_report_path: Path = DEFAULT_DAILY_REPORT_PATH,
    reviewer: RuleBasedReviewer | None = None,
) -> ReviewSummary:
    evaluation = load_evaluation_summary(evaluation_path)
    baseline = load_evaluation_summary(baseline_path) if baseline_path else None
    report_path = evaluation_report_path or infer_evaluation_report_path(evaluation_path)
    selected_reviewer = reviewer or RuleBasedReviewer()
    return selected_reviewer.review(
        evaluation=evaluation,
        baseline=baseline,
        evaluation_report_path=report_path,
        daily_report_path=daily_report_path,
    )


def write_review_outputs(
    summary: ReviewSummary,
    summary_path: str | Path = DEFAULT_REVIEW_SUMMARY_PATH,
    report_path: str | Path = DEFAULT_REVIEW_REPORT_PATH,
) -> tuple[Path, Path]:
    json_path = Path(summary_path)
    md_path = Path(report_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(
        json.dumps(summary.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    md_path.write_text(render_review_report(summary), encoding="utf-8")
    return json_path, md_path


def render_review_report(summary: ReviewSummary) -> str:
    return Template(REVIEW_REPORT_TEMPLATE).render(summary=summary)
