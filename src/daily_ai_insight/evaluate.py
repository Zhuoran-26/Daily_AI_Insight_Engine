"""Evaluation harness for comparing extractor quality."""

from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Template

from daily_ai_insight.errors import HarnessError, PipelineError, ValidationError
from daily_ai_insight.extractors import BaseExtractor, create_extractor
from daily_ai_insight.harness import PipelineHarness
from daily_ai_insight.llm_client import OpenAICompatibleConfig
from daily_ai_insight.models import EvaluationItemResult, EvaluationSummary, RawNewsItem, StructuredAIEvent
from daily_ai_insight.normalize import load_raw_news
from daily_ai_insight.validate import validate_raw_items, validate_structured_events

DEFAULT_EVALUATION_SUMMARY_PATH = Path("outputs/evaluation_summary.json")
DEFAULT_EVALUATION_REPORT_PATH = Path("outputs/evaluation_report.md")

EVALUATION_REPORT_TEMPLATE = """# 抽取器评估报告

## 评估摘要

- 抽取模式: {{ summary.extractor }}
- 样本总数: {{ summary.total_items }}
- 成功项: {{ summary.successful_items }}
- 失败项: {{ summary.failed_items }}
- 分类准确率: {{ "%.2f"|format(summary.category_accuracy) }}
- 来源追溯通过率: {{ "%.2f"|format(summary.grounding_pass_rate) }}
- 平均置信度: {{ "%.2f"|format(summary.average_confidence) }}

## 分类不一致项

| 标题 | 预期分类 | 预测分类 | 置信度 |
| --- | --- | --- | --- |
{% for item in mismatched -%}
| {{ item.title }} | {{ item.expected_category }} | {{ item.predicted_category or "" }} | {{ "" if item.confidence is none else "%.2f"|format(item.confidence) }} |
{% endfor %}

## 失败项

| 标题 | 预期分类 | 错误 |
| --- | --- | --- |
{% for item in failed -%}
| {{ item.title }} | {{ item.expected_category }} | {{ item.error or "" }} |
{% endfor %}

## 方法说明

Evaluation Harness 的目标不是追求 100% 准确率，而是暴露不同 extractor 的优势与局限。rule baseline 提供稳定可复现的 fallback，LLM extractor 用于处理更复杂的语义分类；无论哪种模式，Harness 都会在输出进入日报前阻止幻觉来源、无追溯事件和低置信度结果。
"""


def run_evaluation(
    input_path: Path,
    expected_path: Path,
    extractor_name: str = "rule",
    extractor: BaseExtractor | None = None,
) -> EvaluationSummary:
    raw_items = validate_raw_items(load_raw_news(input_path))
    expected_categories = _load_expected_categories(expected_path)
    _validate_expected_titles(raw_items, expected_categories)

    if extractor is None and extractor_name == "openai-compatible":
        OpenAICompatibleConfig.from_environment()

    selected_extractor = extractor or create_extractor(extractor_name)
    harness = PipelineHarness()
    harness.check_extractor_name(selected_extractor.name)
    harness.check_input_size(raw_items)
    harness.check_source_integrity(raw_items)

    item_results: list[EvaluationItemResult] = []
    for index, raw_item in enumerate(raw_items, start=1):
        expected_category = expected_categories[raw_item.title]
        try:
            event = _extract_single_event(selected_extractor, raw_item, index)
            validate_structured_events([event])
            harness.check_single_event_grounding(event, raw_item)
            harness.check_single_evidence_grounding(event, raw_item)
            harness.check_confidence([event])
            item_results.append(
                EvaluationItemResult(
                    title=raw_item.title,
                    expected_category=expected_category,
                    predicted_category=event.category,
                    category_match=event.category == expected_category,
                    confidence=event.confidence,
                    grounded=True,
                    error=None,
                )
            )
        except (PipelineError, HarnessError, ValidationError) as exc:
            item_results.append(
                EvaluationItemResult(
                    title=raw_item.title,
                    expected_category=expected_category,
                    predicted_category=None,
                    category_match=False,
                    confidence=None,
                    grounded=False,
                    error=f"item {index} '{raw_item.title}': {exc}",
                )
            )

    return _build_summary(selected_extractor.name, item_results)


def write_evaluation_outputs(
    summary: EvaluationSummary,
    summary_path: str | Path = DEFAULT_EVALUATION_SUMMARY_PATH,
    report_path: str | Path = DEFAULT_EVALUATION_REPORT_PATH,
) -> tuple[Path, Path]:
    json_path = Path(summary_path)
    md_path = Path(report_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(
        json.dumps(summary.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    md_path.write_text(render_evaluation_report(summary), encoding="utf-8")
    return json_path, md_path


def evaluation_output_paths(output_prefix: str | None = None) -> tuple[Path, Path]:
    if not output_prefix:
        return DEFAULT_EVALUATION_SUMMARY_PATH, DEFAULT_EVALUATION_REPORT_PATH

    safe_prefix = output_prefix.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", safe_prefix):
        raise PipelineError("Evaluation output prefix may only contain letters, numbers, underscores, and hyphens")

    return (
        Path(f"outputs/{safe_prefix}_evaluation_summary.json"),
        Path(f"outputs/{safe_prefix}_evaluation_report.md"),
    )


def render_evaluation_report(summary: EvaluationSummary) -> str:
    failed = [item for item in summary.item_results if item.error]
    mismatched = [item for item in summary.item_results if not item.error and not item.category_match]
    return Template(EVALUATION_REPORT_TEMPLATE).render(
        summary=summary,
        failed=failed,
        mismatched=mismatched,
    )


def _extract_single_event(
    extractor: BaseExtractor,
    raw_item: RawNewsItem,
    index: int,
) -> StructuredAIEvent:
    events = extractor.extract([raw_item])
    if len(events) != 1:
        raise PipelineError(
            f"extractor returned {len(events)} events for single item {index}; expected 1"
        )
    return events[0]


def _load_expected_categories(expected_path: Path) -> dict[str, str]:
    payload = json.loads(Path(expected_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise PipelineError("Expected category fixture must be a list")

    expected: dict[str, str] = {}
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise PipelineError(f"Expected fixture item {index} must be an object")
        title = str(item.get("title", "")).strip()
        category = str(item.get("expected_category", "")).strip()
        if not title or not category:
            raise PipelineError(f"Expected fixture item {index} is missing title or expected_category")
        expected[title] = category
    return expected


def _validate_expected_titles(
    raw_items: list[RawNewsItem],
    expected_categories: dict[str, str],
) -> None:
    raw_titles = {item.title for item in raw_items}
    expected_titles = set(expected_categories)
    missing = sorted(raw_titles - expected_titles)
    extra = sorted(expected_titles - raw_titles)
    if missing or extra:
        raise PipelineError(
            "Expected category fixture titles do not match raw input. "
            f"Missing expected titles: {missing}. Extra expected titles: {extra}."
        )


def _build_summary(
    extractor_name: str,
    item_results: list[EvaluationItemResult],
) -> EvaluationSummary:
    total_items = len(item_results)
    successful_items = sum(1 for item in item_results if item.error is None)
    failed_items = total_items - successful_items
    matched_items = sum(1 for item in item_results if item.error is None and item.category_match)
    grounded_items = sum(1 for item in item_results if item.grounded)
    confidences = [item.confidence for item in item_results if item.confidence is not None]

    return EvaluationSummary(
        extractor=extractor_name,
        total_items=total_items,
        successful_items=successful_items,
        failed_items=failed_items,
        category_accuracy=matched_items / successful_items if successful_items else 0.0,
        grounding_pass_rate=grounded_items / total_items if total_items else 0.0,
        average_confidence=sum(confidences) / len(confidences) if confidences else 0.0,
        item_results=item_results,
    )
