"""Streamlit product demo for Daily AI Insight Engine.

The UI is intentionally thin: it delegates pipeline, evaluation, and reviewer
work to the existing project modules instead of duplicating business logic.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from daily_ai_insight.errors import PipelineError
from daily_ai_insight.evaluate import render_evaluation_report, run_evaluation, write_evaluation_outputs
from daily_ai_insight.models import DailyInsightReport, EvaluationSummary
from daily_ai_insight.normalize import load_raw_news
from daily_ai_insight.pipeline import run_pipeline
from daily_ai_insight.report import render_report
from daily_ai_insight.reviewer import (
    ReviewSummary,
    RuleBasedReviewer,
    load_evaluation_summary,
    run_review,
    write_review_outputs,
)

REAL_SAMPLE_PATH = Path("data/raw/real_ai_news_sample.json")
SYNTHETIC_SAMPLE_PATH = Path("data/raw/sample_ai_news.json")
EXPECTED_REAL_SAMPLE_PATH = Path("data/eval/expected_real_sample_categories.json")
UI_EVALUATION_SUMMARY_PATH = Path("outputs/ui_evaluation_summary.json")
UI_EVALUATION_REPORT_PATH = Path("outputs/ui_evaluation_report.md")
SAVED_LLM_EVALUATION_PATH = Path("outputs/llm_evaluation_summary.json")
SAVED_RULE_EVALUATION_PATH = Path("outputs/rule_evaluation_summary.json")

EXTRACTOR_DESCRIPTIONS = {
    "rule": "无需 API key，稳定 deterministic baseline。",
    "mock-llm": "用于测试 LLM workflow，不调用真实 API。",
    "openai-compatible": "需要 .env 中配置 DeepSeek/OpenAI-compatible API key。",
}


def is_openai_key_configured() -> bool:
    load_dotenv()
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def is_bundled_real_sample(input_path: Path) -> bool:
    return input_path.resolve() == REAL_SAMPLE_PATH.resolve()


def save_uploaded_json(uploaded_file: Any) -> Path:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        temp_file.write(uploaded_file.getvalue())
        return Path(temp_file.name)


def validate_input_file(input_path: Path) -> int:
    raw_items = load_raw_news(input_path)
    if not raw_items:
        raise PipelineError("Input JSON did not contain any usable news items")
    return len(raw_items)


def load_structured_events(events_path: Path = Path("data/processed/structured_events.json")) -> list[dict[str, Any]]:
    if not events_path.exists():
        return []
    return json.loads(events_path.read_text(encoding="utf-8"))


def top_events_table(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {
            "title": event.title,
            "category": event.category,
            "source": event.source,
            "confidence": event.confidence,
            "importance_score": event.importance_score,
            "url": event.url,
        }
        for event in report.top_events
    ]


def category_counts_table(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {"category": category, "count": count}
        for category, count in sorted(report.category_counts.items())
    ]


def category_distribution_chart_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    return category_counts_table(report)


def top_events_importance_chart_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {
            "title": event.title,
            "importance_score": event.importance_score,
        }
        for event in report.top_events
    ]


def extractor_accuracy_comparison_chart_data(
    rule_path: Path = SAVED_RULE_EVALUATION_PATH,
    llm_path: Path = SAVED_LLM_EVALUATION_PATH,
) -> list[dict[str, Any]]:
    if not rule_path.exists() or not llm_path.exists():
        return []

    rule_summary = load_evaluation_summary(rule_path)
    llm_summary = load_evaluation_summary(llm_path)
    return [
        {
            "extractor": "rule baseline",
            "category_accuracy": rule_summary.category_accuracy,
        },
        {
            "extractor": "DeepSeek V4 Flash",
            "category_accuracy": llm_summary.category_accuracy,
        },
    ]


def mismatched_items_table(summary: EvaluationSummary) -> list[dict[str, Any]]:
    return [
        {
            "title": item.title,
            "expected_category": item.expected_category,
            "predicted_category": item.predicted_category,
            "confidence": item.confidence,
        }
        for item in summary.item_results
        if item.error is None and not item.category_match
    ]


def failed_items_table(summary: EvaluationSummary) -> list[dict[str, Any]]:
    return [
        {
            "title": item.title,
            "expected_category": item.expected_category,
            "error": item.error,
        }
        for item in summary.item_results
        if item.error
    ]


def review_issues_table(summary: ReviewSummary) -> list[dict[str, str]]:
    return [
        {
            "severity": issue.severity,
            "area": issue.area,
            "title": issue.title,
            "suggested_action": issue.suggested_action,
        }
        for issue in summary.issues
    ]


def main() -> None:
    import streamlit as st

    load_dotenv()
    st.set_page_config(page_title="Daily AI Insight Engine", layout="wide")
    st.title("Daily AI Insight Engine")
    st.caption(
        "Harnessed AI news analysis pipeline with rule baseline, optional LLM extraction, "
        "evaluation, and reviewer workflow."
    )

    input_path = _render_input_data_section(st)
    extractor_name = _render_extractor_section(st)

    _render_pipeline_section(st, input_path, extractor_name)
    _render_evaluation_section(st, input_path, extractor_name)
    _render_reviewer_section(st)


def _render_input_data_section(st: Any) -> Path | None:
    st.header("1. Input Data")
    data_source = st.radio(
        "Choose news input",
        ["real_ai_news_sample.json", "sample_ai_news.json", "Upload custom JSON"],
        index=0,
        horizontal=True,
    )

    if data_source == "real_ai_news_sample.json":
        input_path = REAL_SAMPLE_PATH
    elif data_source == "sample_ai_news.json":
        input_path = SYNTHETIC_SAMPLE_PATH
    else:
        uploaded_file = st.file_uploader("Upload raw news JSON", type=["json"])
        if uploaded_file is None:
            st.info("Upload a JSON file with RawNewsItem-compatible records to continue.")
            return None
        input_path = save_uploaded_json(uploaded_file)

    try:
        item_count = validate_input_file(input_path)
    except (OSError, ValueError, PipelineError) as exc:
        st.error(f"Input validation failed: {exc}")
        return None

    st.success(f"Loaded {item_count} raw news items from {input_path}.")
    return input_path


def _render_extractor_section(st: Any) -> str:
    st.header("2. Extractor Mode")
    extractor_name = st.selectbox(
        "Choose extractor",
        ["rule", "mock-llm", "openai-compatible"],
        index=0,
    )
    st.info(EXTRACTOR_DESCRIPTIONS[extractor_name])

    if extractor_name == "openai-compatible" and not is_openai_key_configured():
        st.warning(
            "OPENAI_API_KEY is not configured. This mode will fail until .env contains a valid "
            "DeepSeek/OpenAI-compatible API key."
        )

    return extractor_name


def _render_pipeline_section(st: Any, input_path: Path | None, extractor_name: str) -> None:
    st.header("3. Run Pipeline")
    if st.button("Run Insight Pipeline", type="primary", disabled=input_path is None):
        if input_path is None:
            st.error("Please choose or upload a valid input JSON first.")
            return
        if extractor_name == "openai-compatible" and not is_openai_key_configured():
            st.error("OPENAI_API_KEY is missing. Configure .env before running openai-compatible mode.")
            return

        try:
            with st.spinner("Running harnessed insight pipeline..."):
                report = run_pipeline(input_path, extractor_name=extractor_name)
            st.session_state["pipeline_report"] = report
        except (OSError, ValueError, PipelineError) as exc:
            st.error(f"Pipeline failed: {exc}")
            return

        st.success("Pipeline completed.")

    report = st.session_state.get("pipeline_report")
    if not report:
        return

    col_total, col_categories, col_extractor = st.columns(3)
    col_total.metric("Total events", report.total_events)
    col_categories.metric("Categories", len(report.category_counts))
    col_extractor.metric("Extractor", report.harness_summary.get("extractor_name", "unknown"))

    st.subheader("Category Counts")
    st.bar_chart(category_distribution_chart_data(report), x="category", y="count")
    st.dataframe(category_counts_table(report), use_container_width=True)

    st.subheader("Top Events")
    st.bar_chart(top_events_importance_chart_data(report), x="title", y="importance_score")
    st.dataframe(top_events_table(report), use_container_width=True)

    st.subheader("Structured Events")
    st.dataframe(load_structured_events(), use_container_width=True)

    st.subheader("Harness Summary")
    st.json(report.harness_summary)

    st.subheader("Daily Report")
    st.markdown(render_report(report))


def _render_evaluation_section(st: Any, input_path: Path | None, extractor_name: str) -> None:
    st.header("4. Evaluation Harness")
    st.caption(f"Expected fixture: {EXPECTED_REAL_SAMPLE_PATH}")

    can_evaluate = input_path is not None and is_bundled_real_sample(input_path)
    if not can_evaluate:
        st.warning(
            "Evaluation only supports bundled real-world sample unless a matching expected fixture is provided."
        )

    if st.button("Run Evaluation", disabled=not can_evaluate):
        if input_path is None:
            st.error("Please choose a valid input JSON first.")
            return
        if extractor_name == "openai-compatible" and not is_openai_key_configured():
            st.error("OPENAI_API_KEY is missing. Configure .env before running LLM evaluation.")
            return

        try:
            with st.spinner("Running evaluation harness..."):
                summary = run_evaluation(
                    input_path=input_path,
                    expected_path=EXPECTED_REAL_SAMPLE_PATH,
                    extractor_name=extractor_name,
                )
                summary_path, report_path = write_evaluation_outputs(
                    summary,
                    summary_path=UI_EVALUATION_SUMMARY_PATH,
                    report_path=UI_EVALUATION_REPORT_PATH,
                )
            st.session_state["evaluation_summary"] = summary
            st.session_state["evaluation_summary_path"] = summary_path
            st.session_state["evaluation_report_path"] = report_path
        except (OSError, ValueError, PipelineError) as exc:
            st.error(f"Evaluation failed: {exc}")
            return

        st.success(f"Evaluation completed. Wrote {summary_path} and {report_path}.")

    summary = st.session_state.get("evaluation_summary")
    if not summary:
        return

    col_accuracy, col_grounding, col_confidence, col_failed = st.columns(4)
    col_accuracy.metric("Category accuracy", f"{summary.category_accuracy:.2f}")
    col_grounding.metric("Grounding pass rate", f"{summary.grounding_pass_rate:.2f}")
    col_confidence.metric("Avg confidence", f"{summary.average_confidence:.2f}")
    col_failed.metric("Failed items", summary.failed_items)

    comparison_data = extractor_accuracy_comparison_chart_data()
    if comparison_data:
        st.subheader("Rule vs LLM Accuracy")
        st.bar_chart(comparison_data, x="extractor", y="category_accuracy")

    st.subheader("Mismatched Items")
    st.dataframe(mismatched_items_table(summary), use_container_width=True)

    st.subheader("Failed Items")
    st.dataframe(failed_items_table(summary), use_container_width=True)

    with st.expander("Evaluation Report Markdown"):
        st.markdown(render_evaluation_report(summary))


def _render_reviewer_section(st: Any) -> None:
    st.header("5. Reviewer")
    review_source = st.radio(
        "Review source",
        ["Use current evaluation result", "Use saved showcase outputs"],
        index=0,
        horizontal=True,
    )

    if st.button("Run Reviewer"):
        try:
            with st.spinner("Running deterministic reviewer..."):
                if review_source == "Use current evaluation result" and st.session_state.get("evaluation_summary"):
                    summary = _review_current_evaluation(st)
                else:
                    summary = run_review(
                        evaluation_path=SAVED_LLM_EVALUATION_PATH,
                        baseline_path=SAVED_RULE_EVALUATION_PATH,
                    )
                summary_path, report_path = write_review_outputs(summary)
            st.session_state["review_summary"] = summary
            st.session_state["review_summary_path"] = summary_path
            st.session_state["review_report_path"] = report_path
        except (OSError, ValueError, PipelineError) as exc:
            st.error(f"Reviewer failed: {exc}")
            return

        st.success(f"Reviewer completed. Wrote {summary_path} and {report_path}.")

    summary = st.session_state.get("review_summary")
    if not summary:
        return

    col_verdict, col_errors, col_warnings, col_info = st.columns(4)
    col_verdict.metric("Final verdict", summary.final_verdict)
    col_errors.metric("Errors", summary.error_count)
    col_warnings.metric("Warnings", summary.warning_count)
    col_info.metric("Info", summary.info_count)

    st.subheader("Review Issues")
    st.dataframe(review_issues_table(summary), use_container_width=True)

    report_path = st.session_state.get("review_report_path")
    if report_path and Path(report_path).exists():
        st.subheader("Review Report")
        st.markdown(Path(report_path).read_text(encoding="utf-8"))


def _review_current_evaluation(st: Any) -> ReviewSummary:
    evaluation = st.session_state["evaluation_summary"]
    baseline = None
    if SAVED_RULE_EVALUATION_PATH.exists() and evaluation.extractor != "rule":
        baseline = load_evaluation_summary(SAVED_RULE_EVALUATION_PATH)

    return RuleBasedReviewer().review(
        evaluation=evaluation,
        baseline=baseline,
        evaluation_report_path=st.session_state.get("evaluation_report_path"),
        daily_report_path=Path("outputs/daily_report.md"),
    )


if __name__ == "__main__":
    main()
