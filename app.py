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

import altair as alt
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
MIXED_SAMPLE_PATH = Path("data/raw/mixed_channel_ai_news_sample.json")
SYNTHETIC_SAMPLE_PATH = Path("data/raw/sample_ai_news.json")
EXPECTED_REAL_SAMPLE_PATH = Path("data/eval/expected_real_sample_categories.json")
EXPECTED_MIXED_SAMPLE_PATH = Path("data/eval/expected_mixed_sample_categories.json")
UI_EVALUATION_SUMMARY_PATH = Path("outputs/ui_evaluation_summary.json")
UI_EVALUATION_REPORT_PATH = Path("outputs/ui_evaluation_report.md")
SAVED_LLM_EVALUATION_PATH = Path("outputs/llm_evaluation_summary.json")
SAVED_RULE_EVALUATION_PATH = Path("outputs/rule_evaluation_summary.json")
LLM_REVIEW_NOTE = "本段分析由 LLM 生成，已通过 Schema、Source Grounding 和 Harness 校验，但仍建议人工复核。"

SOURCE_CHANNEL_LABELS = {
    "official": "官方渠道",
    "tech_media": "科技媒体",
    "aggregator": "聚合平台",
    "social_media": "社交/社区",
}
SOURCE_LANGUAGE_LABELS = {
    "en": "英文",
    "zh": "中文",
}
CATEGORY_LABELS = {
    "model": "模型能力",
    "agent": "智能体与工作流",
    "infrastructure": "算力与基础设施",
    "application": "应用与产品",
}

EXTRACTOR_DESCRIPTIONS = {
    "rule": "规则 baseline，不需要 API key，稳定可复现，适合离线演示。",
    "mock-llm": "模拟 LLM 输出，用于测试 Harness 和异常拦截。",
    "openai-compatible": "真实 LLM 模式，调用 DeepSeek / OpenAI-compatible API，适合复杂语义抽取。",
}


def is_openai_key_configured() -> bool:
    load_dotenv()
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def is_bundled_real_sample(input_path: Path) -> bool:
    return input_path.resolve() == REAL_SAMPLE_PATH.resolve()


def is_bundled_mixed_sample(input_path: Path) -> bool:
    return input_path.resolve() == MIXED_SAMPLE_PATH.resolve()


def expected_fixture_for_input(input_path: Path) -> Path | None:
    if is_bundled_mixed_sample(input_path):
        return EXPECTED_MIXED_SAMPLE_PATH
    if is_bundled_real_sample(input_path):
        return EXPECTED_REAL_SAMPLE_PATH
    return None


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


def source_channel_label(value: str | None) -> str:
    return SOURCE_CHANNEL_LABELS.get(value or "", value or "未标注")


def source_language_label(value: str | None) -> str:
    return SOURCE_LANGUAGE_LABELS.get(value or "", value or "未标注")


def category_label(value: str | None) -> str:
    return CATEGORY_LABELS.get(value or "", value or "未分类")


def source_provenance_table(input_path: Path) -> list[dict[str, Any]]:
    return [
        {
            "标题": item.title,
            "来源": item.source,
            "URL": item.url,
            "发布日期": item.published_at,
            "来源渠道": source_channel_label(item.source_channel),
            "来源语言": source_language_label(item.source_language or item.language),
            "选择理由": item.selection_reason or "未提供",
            "采集日期": item.collected_at or "未提供",
        }
        for item in load_raw_news(input_path)
    ]


def top_events_table(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {
            "标题": event.title,
            "分类": category_label(event.category),
            "来源": event.source,
            "置信度": event.confidence,
            "重要性评分": event.importance_score,
            "URL": event.url,
        }
        for event in report.top_events
    ]


def structured_events_business_table(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "标题": event.get("title", ""),
            "来源": event.get("source", ""),
            "发布日期": event.get("published_at", ""),
            "来源渠道": source_channel_label(event.get("source_channel")),
            "分类": category_label(event.get("category")),
            "事件类型": event.get("event_type", ""),
            "重要性": event.get("importance_score"),
            "置信度": event.get("confidence"),
            "中文摘要": event.get("summary", ""),
            "行业影响": event.get("industry_impact", ""),
            "行业机会": event.get("industry_opportunity", ""),
            "行业风险": event.get("industry_risk", ""),
            "URL": event.get("url", ""),
        }
        for event in events
    ]


def topic_cluster_table(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {
            "canonical_topic": cluster.canonical_topic,
            "覆盖来源数量": cluster.source_count,
            "覆盖渠道": "、".join(cluster.source_channels),
            "覆盖语言": "、".join(cluster.source_languages),
            "代表标题": cluster.representative_title,
            "包含官方来源": "是" if cluster.has_official_source else "否",
            "包含社区反馈": "是" if cluster.has_community_feedback else "否",
        }
        for cluster in report.topic_clusters
    ]


def category_counts_table(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {"分类": category_label(category), "数量": count}
        for category, count in sorted(report.category_counts.items())
    ]


def category_distribution_chart_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    return category_counts_table(report)


def source_coverage_matrix_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    for event in report.events or report.top_events:
        channel = source_channel_label(event.source_channel)
        language = source_language_label(event.source_language or event.language)
        counts[(channel, language)] = counts.get((channel, language), 0) + 1

    channels = _with_observed_labels(
        [source_channel_label(channel) for channel in SOURCE_CHANNEL_LABELS],
        [channel for channel, _ in counts],
    )
    languages = _with_observed_labels(
        [source_language_label(language) for language in SOURCE_LANGUAGE_LABELS],
        [language for _, language in counts],
    )
    return [
        {
            "来源渠道": channel,
            "来源语言": language,
            "数量": counts.get((channel, language), 0),
        }
        for channel in channels
        for language in languages
    ]


def event_timeline_chart_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for event in report.events or report.top_events:
        counts[event.published_at] = counts.get(event.published_at, 0) + 1
    return [
        {"发布日期": published_at, "事件数": count}
        for published_at, count in sorted(counts.items())
    ]


def _with_observed_labels(defaults: list[str], observed: list[str]) -> list[str]:
    labels = [*defaults]
    for value in sorted(set(observed)):
        if value not in labels:
            labels.append(value)
    return labels


def top_events_importance_chart_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {
            "标题": event.title,
            "重要性评分": event.importance_score,
        }
        for event in report.top_events
    ]


def importance_confidence_scatter_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    return [
        {
            "标题": event.title,
            "来源": event.source,
            "发布日期": event.published_at,
            "分类": category_label(event.category),
            "置信度": event.confidence,
            "重要性": event.importance_score,
        }
        for event in report.events or report.top_events
    ]


def impact_area_distribution_chart_data(report: DailyInsightReport) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for event in report.events or report.top_events:
        for area in event.impact_areas:
            counts[area] = counts.get(area, 0) + 1
    return [
        {"影响领域": area, "事件数": count}
        for area, count in sorted(counts.items())
    ]


def source_coverage_matrix_chart(report: DailyInsightReport) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=source_coverage_matrix_data(report)))
        .mark_rect()
        .encode(
            x=alt.X("来源语言:N", title="来源语言"),
            y=alt.Y("来源渠道:N", title="来源渠道"),
            color=alt.Color("数量:Q", title="数量"),
            tooltip=[
                alt.Tooltip("来源渠道:N"),
                alt.Tooltip("来源语言:N"),
                alt.Tooltip("数量:Q"),
            ],
        )
        .properties(height=220)
    )


def event_timeline_chart(report: DailyInsightReport) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=event_timeline_chart_data(report)))
        .mark_area(opacity=0.55, line=True)
        .encode(
            x=alt.X("发布日期:T", title="发布日期"),
            y=alt.Y("事件数:Q", title="事件数", scale=alt.Scale(domainMin=0)),
            tooltip=[
                alt.Tooltip("发布日期:T"),
                alt.Tooltip("事件数:Q"),
            ],
        )
        .properties(height=220)
    )


def category_distribution_chart(report: DailyInsightReport) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=category_distribution_chart_data(report)))
        .mark_arc(innerRadius=45)
        .encode(
            theta=alt.Theta("数量:Q"),
            color=alt.Color("分类:N", title="分类"),
            tooltip=[
                alt.Tooltip("分类:N"),
                alt.Tooltip("数量:Q"),
            ],
        )
        .properties(height=240)
    )


def importance_confidence_scatter_chart(report: DailyInsightReport) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=importance_confidence_scatter_data(report)))
        .mark_circle(size=90, opacity=0.8)
        .encode(
            x=alt.X("置信度:Q", title="置信度", scale=alt.Scale(domain=[0, 1])),
            y=alt.Y("重要性:Q", title="重要性", scale=alt.Scale(domain=[0, 10])),
            color=alt.Color("分类:N", title="分类"),
            tooltip=[
                alt.Tooltip("标题:N"),
                alt.Tooltip("来源:N"),
                alt.Tooltip("发布日期:T"),
                alt.Tooltip("分类:N"),
                alt.Tooltip("重要性:Q"),
                alt.Tooltip("置信度:Q"),
            ],
        )
        .properties(height=240)
    )


def impact_area_distribution_chart(report: DailyInsightReport) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=impact_area_distribution_chart_data(report)))
        .mark_bar()
        .encode(
            x=alt.X("事件数:Q", title="事件数"),
            y=alt.Y("影响领域:N", title="影响领域", sort="-x"),
            color=alt.Color("影响领域:N", legend=None),
            tooltip=[
                alt.Tooltip("影响领域:N"),
                alt.Tooltip("事件数:Q"),
            ],
        )
        .properties(height=220)
    )


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


def harness_checklist_table(report: DailyInsightReport) -> list[dict[str, Any]]:
    summary = report.harness_summary
    return [
        {"检查项": "输入数量检查", "结果": pass_label(bool(summary.get("input_count")))},
        {"检查项": "输出数量检查", "结果": pass_label(bool(summary.get("output_count")))},
        {"检查项": "来源完整性", "结果": pass_label(summary.get("source_integrity_passed"))},
        {"检查项": "Schema 校验", "结果": pass_label(summary.get("schema_compliance_passed"))},
        {"检查项": "来源追溯", "结果": pass_label(summary.get("grounding_passed"))},
        {"检查项": "证据追溯", "结果": pass_label(summary.get("evidence_grounding_passed"))},
        {"检查项": "Loop Guard", "结果": pass_label(summary.get("loop_guard_passed"))},
        {"检查项": "最低置信度阈值", "结果": str(summary.get("min_confidence", "未提供"))},
        {"检查项": "当前抽取模式", "结果": str(summary.get("extractor_name", "unknown"))},
    ]


def pass_label(value: object) -> str:
    return "通过" if value is True else "未通过"


def report_has_llm_generated_content(report: DailyInsightReport) -> bool:
    extractor_name = str(report.harness_summary.get("extractor_name", ""))
    return extractor_name == "openai-compatible" or any(
        event.llm_generated for event in report.events or report.top_events
    )


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
    st.info(
        "本系统用于从每日 AI 新闻、官方公告、科技媒体与社区讨论中提取结构化洞察，"
        "生成可读的中文分析报告与可视化结果，支持 AI 行业趋势分析、舆情监测与风险预警、"
        "信息快速理解与决策辅助。"
    )
    st.markdown(
        "**工作流**：新闻输入 → 结构化抽取 → 来源追溯 → Harness 校验 → "
        "趋势/风险/机会分析 → 可视化日报 → Evaluation → AI Reviewer"
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
        [
            "mixed_channel_ai_news_sample.json",
            "real_ai_news_sample.json",
            "sample_ai_news.json",
            "上传自定义 JSON",
        ],
        index=0,
        horizontal=True,
    )

    if data_source == "mixed_channel_ai_news_sample.json":
        input_path = MIXED_SAMPLE_PATH
    elif data_source == "real_ai_news_sample.json":
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
    _render_source_provenance_section(st, input_path)
    return input_path


def _render_source_provenance_section(st: Any, input_path: Path) -> None:
    st.subheader("数据来源追溯")
    st.caption("这一区域用于证明数据来源可追溯、发布时间明确、事件选择有理由。")
    st.dataframe(source_provenance_table(input_path), use_container_width=True)


def _render_extractor_section(st: Any) -> str:
    st.header("2. 结构化洞察生成方式")
    extractor_name = st.selectbox(
        "选择生成方式",
        ["rule", "mock-llm", "openai-compatible"],
        index=0,
    )
    st.caption(
        "该选项决定系统如何从已输入的新闻/公告/社区信息中生成结构化事件、摘要、分类、趋势、风险与机会；"
        "它不负责联网抓取新闻。"
    )
    st.info(EXTRACTOR_DESCRIPTIONS[extractor_name])

    if is_openai_key_configured():
        st.success("✅ 已检测到 OpenAI-compatible API 配置，可使用真实 LLM 抽取。")
    else:
        st.warning("⚠️ 未检测到 API key，openai-compatible 无法运行；可切换到 rule 模式。")

    return extractor_name


def _render_visualization_section(st: Any, report: DailyInsightReport) -> None:
    st.subheader("可视化日报")

    col_matrix, col_timeline = st.columns(2)
    with col_matrix:
        st.markdown("**来源渠道 × 来源语言覆盖矩阵**")
        st.caption("这个图回答什么问题：这个图用于验证样本是否覆盖中英混合与多渠道来源。")
        _render_altair_chart_safely(st, source_coverage_matrix_chart(report), "来源渠道 × 来源语言覆盖矩阵")

    with col_timeline:
        st.markdown("**事件发布时间线**")
        st.caption("这个图回答什么问题：这个图用于观察样本在时间上的分布，体现每日信息流和近期热点。")
        _render_altair_chart_safely(st, event_timeline_chart(report), "事件发布时间线")

    col_category, col_scatter = st.columns(2)
    with col_category:
        st.markdown("**分类分布**")
        st.caption("这个图回答什么问题：这个图用于观察当前 AI 热点集中在哪些方向。")
        _render_altair_chart_safely(st, category_distribution_chart(report), "分类分布")

    with col_scatter:
        st.markdown("**重要性 × 置信度散点图**")
        st.caption("这个图回答什么问题：这个图用于辅助判断哪些事件值得优先关注，哪些高重要性但低置信度的事件需要人工复核。")
        _render_altair_chart_safely(st, importance_confidence_scatter_chart(report), "重要性 × 置信度散点图")

    st.markdown("**影响领域分布**")
    st.caption("这个图回答什么问题：这个图用于观察事件主要影响哪些业务或技术方向。")
    _render_altair_chart_safely(st, impact_area_distribution_chart(report), "影响领域分布")


def _render_topic_cluster_section(st: Any, report: DailyInsightReport) -> None:
    st.subheader("热点聚类与多源覆盖")
    st.caption(
        "同一热点可能被官方、科技媒体、聚合平台和社区重复提及。这里展示的是信息扩散与多源覆盖，"
        "不是把多条记录简单视为重复数据；社区源用于观察反馈和舆情，不作为事实主来源。"
    )
    rows = topic_cluster_table(report)
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("当前报告没有可展示的热点聚类。")


def _render_altair_chart_safely(st: Any, chart: alt.Chart, chart_name: str) -> None:
    try:
        chart.to_dict()
        st.altair_chart(chart, use_container_width=True)
    except Exception as exc:
        st.warning(f"{chart_name} 渲染失败：{exc}")


def _render_llm_review_note(st: Any, report: DailyInsightReport) -> None:
    if report_has_llm_generated_content(report):
        st.caption(LLM_REVIEW_NOTE)


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

    _render_visualization_section(st, report)
    _render_topic_cluster_section(st, report)

    st.subheader("今日主要热点")
    st.dataframe(top_events_table(report), use_container_width=True)

    st.subheader("结构化事件")
    raw_events = load_structured_events()
    st.dataframe(structured_events_business_table(raw_events), use_container_width=True)
    _render_llm_review_note(st, report)
    with st.expander("查看完整结构化 JSON"):
        st.json(raw_events)

    st.subheader("Harness 校验摘要")
    st.dataframe(harness_checklist_table(report), use_container_width=True)
    with st.expander("查看原始 Harness JSON"):
        st.json(report.harness_summary)

    st.subheader("分析日报")
    _render_llm_review_note(st, report)
    st.markdown(render_report(report))


def _render_evaluation_section(st: Any, input_path: Path | None, extractor_name: str) -> None:
    st.header("4. 评估与对比")
    expected_path = expected_fixture_for_input(input_path) if input_path else None
    st.caption(f"Expected fixture：{expected_path or '未匹配'}")

    can_evaluate = input_path is not None and expected_path is not None
    if not can_evaluate:
        st.warning(
            "自定义数据可以生成日报，但需要匹配的 expected fixture 才能进行定量评估。"
        )

    if st.button("运行评估", disabled=not can_evaluate):
        if input_path is None:
            st.error("请先选择有效的输入 JSON。")
            return
        if expected_path is None:
            st.error("当前输入缺少匹配的 expected fixture，无法进行定量评估。")
            return
        if extractor_name == "openai-compatible" and not is_openai_key_configured():
            st.error("缺少 OPENAI_API_KEY。运行 LLM evaluation 前请先配置 .env。")
            return

        try:
            with st.spinner("正在运行 Evaluation Harness..."):
                summary = run_evaluation(
                    input_path=input_path,
                    expected_path=expected_path,
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
        st.caption(
            "这个图回答什么问题：Rule baseline 暴露规则局限，DeepSeek V4 Flash 对复杂语义更强，"
            "Harness 保证两种模式都保持来源追溯。"
        )
        st.bar_chart(comparison_data, x="抽取模式", y="分类准确率")

    st.subheader("分类不一致项")
    st.dataframe(mismatched_items_table(summary), use_container_width=True)

    st.subheader("失败项")
    st.dataframe(failed_items_table(summary), use_container_width=True)

    with st.expander("评估报告 Markdown"):
        st.markdown(render_evaluation_report(summary))


def _render_reviewer_section(st: Any) -> None:
    st.header("5. AI Reviewer 复审")
    st.info("Reviewer 复审的是抽取与评估质量，不替代人工行业判断。涉及 LLM 生成内容时，需要人工审核。")
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
