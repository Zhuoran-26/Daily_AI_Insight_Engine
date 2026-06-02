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

REVIEW_REPORT_TEMPLATE = """# AI Reviewer 复审报告

## 复审摘要

- 最终结论: {{ summary.final_verdict }}
- 问题总数: {{ summary.total_issues }}
- 错误数: {{ summary.error_count }}
- 警告数: {{ summary.warning_count }}
- 信息数: {{ summary.info_count }}

## 问题列表

| 严重程度 | 区域 | 标题 | 建议动作 |
| --- | --- | --- | --- |
{% for issue in summary.issues -%}
| {{ issue.severity }} | {{ issue.area }} | {{ issue.title }} | {{ issue.suggested_action }} |
{% endfor %}

## 问题详情

{% for issue in summary.issues -%}
### {{ issue.title }}

- 严重程度: {{ issue.severity }}
- 区域: {{ issue.area }}
- 详情: {{ issue.detail }}
- 建议动作: {{ issue.suggested_action }}

{% endfor -%}

## 方法说明

这个 deterministic reviewer 是覆盖在 evaluation artifact 之上的复审层。它不替代 Harness 校验，也不调用 LLM。它的作用是暴露分类不一致、失败项、置信度风险、缺失产物和 baseline 对比信号，让后续 revise 有明确依据。
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
                    title="没有失败评估项",
                    detail=f"全部 {evaluation.total_items} 条样本都生成了有效评估结果。",
                    suggested_action="继续保留当前 evaluation 路径中的 schema 与 harness 校验。",
                )
            ]

        failed_titles = [item.title for item in evaluation.item_results if item.error]
        return [
            ReviewIssue(
                severity="error",
                area="schema",
                title="检测到失败评估项",
                detail=f"{evaluation.failed_items} 条样本评估失败：{failed_titles}",
                suggested_action="在用于 showcase 对比前，先检查失败项错误原因。",
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
                    title="检测到分类不一致项",
                    detail=f"{len(mismatches)} 条成功样本的预测分类与 expected fixture 不一致。",
                    suggested_action="复查不一致标题，并在合理时更新抽取规则、prompt 或 expected fixture 说明。",
                )
            )

        if evaluation.category_accuracy < LOW_ACCURACY_THRESHOLD:
            issues.append(
                ReviewIssue(
                    severity="warning",
                    area="category",
                    title="分类准确率低于展示阈值",
                    detail=(
                        f"{evaluation.extractor} 的分类准确率为 {evaluation.category_accuracy:.2f}，"
                        f"低于 reviewer 阈值 {LOW_ACCURACY_THRESHOLD:.2f}。"
                    ),
                    suggested_action="将该结果用于解释 baseline 局限，或在声称质量提升前修订抽取逻辑。",
                )
            )

        return issues

    def _review_grounding(self, evaluation: EvaluationSummary) -> list[ReviewIssue]:
        if evaluation.grounding_pass_rate >= 1.0:
            return [
                ReviewIssue(
                    severity="info",
                    area="grounding",
                    title="来源追溯全部通过",
                    detail="所有评估样本都通过了 source grounding 检查。",
                    suggested_action="继续要求所有 extractor 模式保留 source 和 URL。",
                )
            ]

        return [
            ReviewIssue(
                severity="error",
                area="grounding",
                title="来源追溯通过率低于 1.0",
                detail=f"来源追溯通过率为 {evaluation.grounding_pass_rate:.2f}；至少一条样本未通过 grounding。",
                suggested_action="修复 source grounding 失败前，不要将该 extractor 结果用于最终报告。",
            )
        ]

    def _review_confidence(self, evaluation: EvaluationSummary) -> list[ReviewIssue]:
        if evaluation.average_confidence >= MIN_CONFIDENCE_FOR_SHOWCASE:
            return [
                ReviewIssue(
                    severity="info",
                    area="confidence",
                    title="平均置信度达到阈值",
                    detail=(
                        f"平均置信度为 {evaluation.average_confidence:.2f}，"
                        f"达到 {MIN_CONFIDENCE_FOR_SHOWCASE:.2f} 阈值。"
                    ),
                    suggested_action="继续在准确率之外展示置信度分布。",
                )
            ]

        return [
            ReviewIssue(
                severity="warning",
                area="confidence",
                title="平均置信度低于阈值",
                detail=(
                    f"平均置信度为 {evaluation.average_confidence:.2f}，"
                    f"低于 reviewer 阈值 {MIN_CONFIDENCE_FOR_SHOWCASE:.2f}。"
                ),
                suggested_action="低置信度结果应进入复审或 fail fast，不应直接进入最终报告。",
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
                    title="未提供 baseline 对比",
                    detail="Reviewer 只收到一个 evaluation summary。",
                    suggested_action="在声称 extractor 质量提升时，应提供 rule baseline summary 作为对比。",
                )
            ]

        delta = evaluation.category_accuracy - baseline.category_accuracy
        if delta <= MEANINGFUL_ACCURACY_DELTA:
            return [
                ReviewIssue(
                    severity="warning",
                    area="category",
                    title="Extractor 准确率未明显高于 baseline",
                    detail=(
                        f"{evaluation.extractor} 准确率为 {evaluation.category_accuracy:.2f}；"
                        f"{baseline.extractor} baseline 准确率为 {baseline.category_accuracy:.2f}；"
                        f"提升幅度为 {delta:.2f}。"
                    ),
                    suggested_action="在 evaluation 显示显著提升前，避免声称 LLM 质量提升。",
                )
            ]

        return [
            ReviewIssue(
                severity="info",
                area="category",
                title="Extractor 相比 baseline 有提升",
                detail=(
                    f"{evaluation.extractor} 准确率为 {evaluation.category_accuracy:.2f}；"
                    f"{baseline.extractor} baseline 准确率为 {baseline.category_accuracy:.2f}；"
                    f"提升幅度为 {delta:.2f}。"
                ),
                suggested_action="可以在 showcase 中使用该对比，同时说明仍然存在的分类不一致项。",
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
                    title="未提供评估报告路径",
                    detail="Reviewer 无法确认 Markdown evaluation report 是否存在。",
                    suggested_action="传入 evaluation report 路径，或使用 CLI 默认推断路径。",
                )
            )
        elif evaluation_report_path.exists():
            issues.append(
                ReviewIssue(
                    severity="info",
                    area="report",
                    title="评估报告存在",
                    detail=f"已找到 evaluation report：{evaluation_report_path}。",
                    suggested_action="将该报告作为人工可读的质量评估产物。",
                )
            )
        else:
            issues.append(
                ReviewIssue(
                    severity="warning",
                    area="report",
                    title="评估报告缺失",
                    detail=f"预期 evaluation report 位于 {evaluation_report_path}。",
                    suggested_action="重新运行 evaluation CLI，确保 reviewer 可查看 Markdown 报告。",
                )
            )

        if daily_report_path.exists():
            issues.append(
                ReviewIssue(
                    severity="info",
                    area="report",
                    title="分析日报存在",
                    detail=f"已找到 daily report：{daily_report_path}。",
                    suggested_action="在确认 evaluation 结果后，将该日报作为最终生成产物展示。",
                )
            )
        else:
            issues.append(
                ReviewIssue(
                    severity="warning",
                    area="report",
                    title="分析日报缺失",
                    detail=f"预期 daily report 位于 {daily_report_path}。",
                    suggested_action="最终演示前请先运行 pipeline，确保日报产物存在。",
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
