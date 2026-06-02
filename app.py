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
    "rule": "无需 API key 的稳定规则 baseline。",
    "mock-llm": "用于测试 LLM workflow 的模拟模式。",
    "openai-compatible": "需要 .env 中配置 DeepSeek / OpenAI-compatible API key。",
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
            "标题": event.title,
            "分类": event.category,
            "来源": event.source,
            "置信度": event.confidence,
            "重要性评分": event.importance_score,
            "URL": event.url,
        }
        for event in report.top_events
    ]


def category_counts_table(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {"分类": category, "数量": count}
        for category, count in sorted(report.category_counts.items())
    ]


def category_distribution_chart_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    return category_counts_table(report)


def top_events_importance_chart_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {
            "标题": event.title,
            "重要性评分": event.importance_score,
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
            "抽取模式": "rule baseline",
            "分类准确率": rule_summary.category_accuracy,
        },
        {
            "抽取模式": "DeepSeek V4 Flash",
            "分类准确率": llm_summary.category_accuracy,
        },
    ]


def mismatched_items_table(summary: EvaluationSummary) -> list[dict[str, Any]]:
    return [
        {
            "标题": item.title,
            "预期分类": item.expected_category,
            "预测分类": item.predicted_category,
            "置信度": item.confidence,
        }
        for item in summary.item_results
        if item.error is None and not item.category_match
    ]


def failed_items_table(summary: EvaluationSummary) -> list[dict[str, Any]]:
    return [
        {
            "标题": item.title,
            "预期分类": item.expected_category,
            "错误": item.error,
        }
        for item in summary.item_results
        if item.error
    ]


def review_issues_table(summary: ReviewSummary) -> list[dict[str, str]]:
    return [
        {
            "严重程度": issue.severity,
            "区域": issue.area,
            "标题": issue.title,
            "建议动作": issue.suggested_action,
        }
        for issue in summary.issues
    ]


def main() -> None:
    import streamlit as st

    load_dotenv()
    st.set_page_config(page_title="Daily AI Insight Engine｜AI 行业洞察日报系统", layout="wide")
    st.title("Daily AI Insight Engine｜AI 行业洞察日报系统")
    st.caption(
        "一个带 Harness Engineering、Evaluation Harness 和 AI Reviewer 的 AI 行业信息结构化分析 Demo。"
    )

    input_path = _render_input_data_section(st)
    extractor_name = _render_extractor_section(st)

    _render_pipeline_section(st, input_path, extractor_name)
    _render_evaluation_section(st, input_path, extractor_name)
    _render_reviewer_section(st)


def _render_input_data_section(st: Any) -> Path | None:
    st.header("1. 输入数据")
    data_source = st.radio(
        "选择新闻输入",
        ["real_ai_news_sample.json", "sample_ai_news.json", "上传自定义 JSON"],
        index=0,
        horizontal=True,
    )

    if data_source == "real_ai_news_sample.json":
        input_path = REAL_SAMPLE_PATH
    elif data_source == "sample_ai_news.json":
        input_path = SYNTHETIC_SAMPLE_PATH
    else:
        uploaded_file = st.file_uploader("上传原始新闻 JSON", type=["json"])
        if uploaded_file is None:
            st.info("请上传与 RawNewsItem 兼容的 JSON 文件后继续。")
            return None
        input_path = save_uploaded_json(uploaded_file)

    try:
        item_count = validate_input_file(input_path)
    except (OSError, ValueError, PipelineError) as exc:
        st.error(f"输入数据校验失败：{exc}")
        return None

    st.success(f"已从 {input_path} 读取 {item_count} 条原始新闻。")
    return input_path


def _render_extractor_section(st: Any) -> str:
    st.header("2. 抽取模式")
    extractor_name = st.selectbox(
        "选择 extractor",
        ["rule", "mock-llm", "openai-compatible"],
        index=0,
    )
    st.info(EXTRACTOR_DESCRIPTIONS[extractor_name])

    if extractor_name == "openai-compatible" and not is_openai_key_configured():
        st.warning(
            "当前未配置 OPENAI_API_KEY。请先在 .env 中配置有效的 DeepSeek / OpenAI-compatible API key，"
            "否则该模式不会运行。"
        )

    return extractor_name


def _render_pipeline_section(st: Any, input_path: Path | None, extractor_name: str) -> None:
    st.header("3. 生成洞察日报")
    if st.button("生成洞察日报", type="primary", disabled=input_path is None):
        if input_path is None:
            st.error("请先选择或上传有效的输入 JSON。")
            return
        if extractor_name == "openai-compatible" and not is_openai_key_configured():
            st.error("缺少 OPENAI_API_KEY。运行 openai-compatible 模式前请先配置 .env。")
            return

        try:
            with st.spinner("正在运行带 Harness 校验的洞察日报 pipeline..."):
                report = run_pipeline(input_path, extractor_name=extractor_name)
            st.session_state["pipeline_report"] = report
        except (OSError, ValueError, PipelineError) as exc:
            st.error(f"日报生成失败：{exc}")
            return

        st.success("日报生成完成。")

    report = st.session_state.get("pipeline_report")
    if not report:
        return

    col_total, col_categories, col_extractor = st.columns(3)
    col_total.metric("事件总数", report.total_events)
    col_categories.metric("分类数", len(report.category_counts))
    col_extractor.metric("抽取模式", report.harness_summary.get("extractor_name", "unknown"))

    st.subheader("分类分布")
    st.bar_chart(category_distribution_chart_data(report), x="分类", y="数量")
    st.dataframe(category_counts_table(report), use_container_width=True)

    st.subheader("重点事件重要性")
    st.bar_chart(top_events_importance_chart_data(report), x="标题", y="重要性评分")
    st.dataframe(top_events_table(report), use_container_width=True)

    st.subheader("结构化事件")
    st.dataframe(load_structured_events(), use_container_width=True)

    st.subheader("Harness 校验摘要")
    st.json(report.harness_summary)

    st.subheader("分析日报")
    st.markdown(render_report(report))


def _render_evaluation_section(st: Any, input_path: Path | None, extractor_name: str) -> None:
    st.header("4. 评估与对比")
    st.caption(f"Expected fixture：{EXPECTED_REAL_SAMPLE_PATH}")

    can_evaluate = input_path is not None and is_bundled_real_sample(input_path)
    if not can_evaluate:
        st.warning(
            "当前 evaluation 仅支持内置 real-world sample。自定义数据需要提供匹配的 expected fixture 后再评估。"
        )

    if st.button("运行评估", disabled=not can_evaluate):
        if input_path is None:
            st.error("请先选择有效的输入 JSON。")
            return
        if extractor_name == "openai-compatible" and not is_openai_key_configured():
            st.error("缺少 OPENAI_API_KEY。运行 LLM evaluation 前请先配置 .env。")
            return

        try:
            with st.spinner("正在运行 Evaluation Harness..."):
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
            st.error(f"评估失败：{exc}")
            return

        st.success(f"评估完成。已写入 {summary_path} 和 {report_path}。")

    summary = st.session_state.get("evaluation_summary")
    if not summary:
        return

    col_accuracy, col_grounding, col_confidence, col_failed = st.columns(4)
    col_accuracy.metric("分类准确率", f"{summary.category_accuracy:.2f}")
    col_grounding.metric("来源追溯通过率", f"{summary.grounding_pass_rate:.2f}")
    col_confidence.metric("平均置信度", f"{summary.average_confidence:.2f}")
    col_failed.metric("失败项", summary.failed_items)

    comparison_data = extractor_accuracy_comparison_chart_data()
    if comparison_data:
        st.subheader("Rule baseline 与 DeepSeek V4 准确率对比")
        st.bar_chart(comparison_data, x="抽取模式", y="分类准确率")

    st.subheader("分类不一致项")
    st.dataframe(mismatched_items_table(summary), use_container_width=True)

    st.subheader("失败项")
    st.dataframe(failed_items_table(summary), use_container_width=True)

    with st.expander("评估报告 Markdown"):
        st.markdown(render_evaluation_report(summary))


def _render_reviewer_section(st: Any) -> None:
    st.header("5. AI Reviewer 复审")
    review_source = st.radio(
        "复审来源",
        ["使用当前评估结果", "使用已保存的 showcase 输出"],
        index=0,
        horizontal=True,
    )

    if st.button("运行复审"):
        try:
            with st.spinner("正在运行 deterministic reviewer..."):
                if review_source == "使用当前评估结果" and st.session_state.get("evaluation_summary"):
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
            st.error(f"复审失败：{exc}")
            return

        st.success(f"复审完成。已写入 {summary_path} 和 {report_path}。")

    summary = st.session_state.get("review_summary")
    if not summary:
        return

    col_verdict, col_errors, col_warnings, col_info = st.columns(4)
    col_verdict.metric("最终结论", summary.final_verdict)
    col_errors.metric("错误数", summary.error_count)
    col_warnings.metric("警告数", summary.warning_count)
    col_info.metric("信息数", summary.info_count)

    st.subheader("复审问题列表")
    st.dataframe(review_issues_table(summary), use_container_width=True)

    report_path = st.session_state.get("review_report_path")
    if report_path and Path(report_path).exists():
        st.subheader("复审报告")
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
