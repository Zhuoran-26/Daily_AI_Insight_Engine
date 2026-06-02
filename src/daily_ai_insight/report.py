"""Markdown report generation from validated structured events."""

from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from jinja2 import Template

from daily_ai_insight.models import DailyInsightReport, StructuredAIEvent, TopicClusterSummary

FORBIDDEN_SYSTEM_RISK_TERMS = ("LLM", "幻觉", "人工复核", "可信度", "Harness", "Schema")

REPORT_TEMPLATE = """# AI 行业洞察日报

## 数据来源概览

- 报告日期：{{ report.date }}
- 样本数量：{{ report.total_events }}

### 渠道分布

{% for channel, count in report.source_channel_counts.items() -%}
- {{ channel_label(channel) }}{% if channel != "unknown" %} (`{{ channel }}`){% endif %}: {{ count }}
{% endfor %}

### 中英文来源分布

{% for language, count in report.source_language_counts.items() -%}
- {{ language_label(language) }}{% if language != "unknown" %} (`{{ language }}`){% endif %}: {{ count }}
{% endfor %}

### 来源追溯清单

{% for event in report.events -%}
{{ loop.index }}. **{{ event.title }}**
   - 来源：{{ event.source }}
   - URL：{{ event.url }}
   - 发布日期：{{ event.published_at }}
   - 来源渠道：{{ channel_label(event.source_channel) }}{% if event.source_channel %} (`{{ event.source_channel }}`){% endif %}
   - 来源语言：{{ language_label(event.source_language or event.language) }}{% if event.source_language or event.language %} (`{{ event.source_language or event.language }}`){% endif %}
   - 采集日期：{{ optional_text(event.collected_at) }}
   - 选择理由：{{ optional_text(event.selection_reason) }}
{% endfor %}

## 热点聚类与多源覆盖

同一热点可能被官方、科技媒体、聚合平台和社区重复提及。系统保留这些记录是为了观察信息扩散链路，而不是把它们简单视为重复数据。`published_at` 表示来源内容的发布时间，`collected_at` 表示样本采集或整理时间；社区源用于观察反馈和舆情，不作为事实主来源。

{% for cluster in report.topic_clusters -%}
- **{{ cluster.canonical_topic }}**：{{ cluster.source_count }} 个来源；覆盖渠道：{{ cluster.source_channels | join("、") }}；覆盖语言：{{ cluster.source_languages | join("、") }}；代表标题：{{ cluster.representative_title }}；代表来源：{{ cluster.representative_sources | join("、") }}；包含官方来源：{{ yes_no(cluster.has_official_source) }}；包含社区反馈：{{ yes_no(cluster.has_community_feedback) }}
{% endfor %}

## 今日主要热点 Top 3–5

{% for event in report.top_events -%}
{{ loop.index }}. **{{ event.title }}**
   - 来源：{{ event.source }}｜发布日期：{{ event.published_at }}
   - 分类：{{ event.category }}｜事件类型：{{ event.event_type }}
   - 重要性：{{ "%.1f"|format(event.importance_score) }}｜置信度：{{ "%.2f"|format(event.confidence) }}
   - 中文摘要：{{ event.summary }}
   - URL：{{ event.url }}
{% endfor %}

## 重点事件深度解读

{% for event in report.top_events -%}
### {{ loop.index }}. {{ event.title }}

- 背景：{{ optional_text(event.background) }}
- 行业影响：{{ optional_text(event.industry_impact) }}
- 趋势信号：{{ optional_text(event.trend_signal) }}
- 行业机会：{{ optional_text(event.industry_opportunity) }}
- 行业风险：{{ optional_text(event.industry_risk) }}
- 决策提示：{{ optional_text(event.decision_hint) }}
- 原文证据：{{ event.evidence }}
- 发布日期与来源：{{ event.published_at }}｜{{ event.source }}｜{{ event.url }}
{% if event.llm_generated %}
<small>本段分析由 LLM 生成，已通过 Schema、Source Grounding 和 Harness 校验，但仍建议人工复核。</small>
{% endif %}

{% endfor %}

## 趋势判断

{% for signal in report.trend_signals -%}
- {{ signal }}
{% endfor %}

## 舆情监测与风险预警

{% for item in report.risks_and_opportunities -%}
- {{ item }}
{% endfor %}

## 机会提示

{% for item in report.opportunity_signals -%}
- {{ item }}
{% endfor %}

## 可视化结果说明

{% for item in report.visualization_notes -%}
- {{ item }}
{% endfor %}

## Harness 校验摘要

- [{{ checked(report.harness_summary.get("source_integrity_passed")) }}] 来源完整性：{{ pass_label(report.harness_summary.get("source_integrity_passed")) }}
- [{{ checked(report.harness_summary.get("schema_compliance_passed")) }}] Schema 校验：{{ pass_label(report.harness_summary.get("schema_compliance_passed")) }}
- [{{ checked(report.harness_summary.get("grounding_passed")) }}] Source Grounding：{{ pass_label(report.harness_summary.get("grounding_passed")) }}
- [{{ checked(report.harness_summary.get("evidence_grounding_passed")) }}] Evidence Grounding：{{ pass_label(report.harness_summary.get("evidence_grounding_passed")) }}
- [{{ checked(report.harness_summary.get("loop_guard_passed")) }}] Step Budget：{{ pass_label(report.harness_summary.get("loop_guard_passed")) }}
- [x] 置信度阈值：最低要求 {{ report.harness_summary.get("min_confidence") }}
- [x] 抽取模式：{{ report.harness_summary.get("extractor_name") }}
- [x] 输入/输出数量：{{ report.harness_summary.get("input_count") }} / {{ report.harness_summary.get("output_count") }}

## 方法说明

`rule` 是 deterministic baseline，不调用真实 LLM API，也不依赖爬虫。它用固定规则完成分类、重要性评分和业务化中文分析，便于本地复现与对照评估。

`openai-compatible` 路径可用于真实 LLM 抽取，但 LLM 输出必须经过 JSON 解析、Pydantic Schema validation、Source Grounding、Evidence Grounding、confidence gate 和 item-level retry budget。系统会强制从 raw input 覆盖 title/source/url/published_at/language/provenance 字段。

报告中的行业风险和行业机会面向 AI 行业趋势分析、舆情监测与风险预警、信息快速理解与决策辅助。涉及 LLM 生成内容时，即使通过 Schema、Source Grounding 和 Harness 校验，仍建议人工复核。
"""


def build_daily_report(
    events: list[StructuredAIEvent],
    harness_summary: dict[str, str | int | float | bool],
    report_date: str | None = None,
) -> DailyInsightReport:
    category_counts = dict(Counter(event.category for event in events))
    source_channel_counts = _build_source_channel_counts(events)
    source_language_counts = _build_source_language_counts(events)
    topic_clusters = build_topic_clusters(events)
    top_events = sorted(events, key=lambda event: event.importance_score, reverse=True)[:5]
    key_takeaways = _build_key_takeaways(events, category_counts)
    trend_signals = _build_trend_signals(events, category_counts, source_channel_counts, topic_clusters)
    risks_and_opportunities = _build_risks_and_opportunities(events)
    opportunity_signals = _build_opportunity_signals(events)
    return DailyInsightReport(
        date=report_date or date.today().isoformat(),
        total_events=len(events),
        events=events,
        top_events=top_events,
        category_counts=category_counts,
        source_channel_counts=source_channel_counts,
        source_language_counts=source_language_counts,
        topic_clusters=topic_clusters,
        key_takeaways=key_takeaways,
        trend_signals=trend_signals,
        risks_and_opportunities=risks_and_opportunities,
        opportunity_signals=opportunity_signals,
        visualization_notes=_build_visualization_notes(),
        harness_summary=harness_summary,
    )


def render_report(report: DailyInsightReport) -> str:
    return Template(REPORT_TEMPLATE).render(
        report=report,
        channel_label=channel_label,
        language_label=language_label,
        optional_text=optional_text,
        checked=checked,
        pass_label=pass_label,
        yes_no=yes_no,
    )


def write_report(report: DailyInsightReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(report), encoding="utf-8")
    return path


def _build_key_takeaways(
    events: list[StructuredAIEvent],
    category_counts: dict[str, int],
) -> list[str]:
    if not events:
        return ["没有可用的已校验事件，因此不生成进一步分析结论。"]

    leading_category = max(category_counts.items(), key=lambda item: item[1])[0]
    top_event = max(events, key=lambda event: event.importance_score)
    source_count = len({event.source for event in events})
    return [
        f"{leading_category} 是本次已校验样本中的最大类别，共 {category_counts[leading_category]} 条事件。",
        f"最高优先级事件是来自 {top_event.source} 的“{top_event.title}”。",
        f"本报告基于 {source_count} 个不同来源标签生成，所有事件均保留 source/url/published_at 追溯信息。",
    ]


def _build_trend_signals(
    events: list[StructuredAIEvent],
    category_counts: dict[str, int],
    source_channel_counts: dict[str, int],
    topic_clusters: list[TopicClusterSummary],
) -> list[str]:
    if not events:
        return ["没有可用的已校验事件，因此不生成趋势判断。"]

    signals: list[str] = []
    if category_counts.get("model"):
        signals.append("模型能力升级仍是本次样本的核心线索，需要关注能力、成本、可靠性和 API 生态变化。")
    if category_counts.get("agent"):
        signals.append("Agent 化和 workflow 化正在把 AI 从单次问答推向多步骤任务执行，企业流程场景值得跟进。")
    if category_counts.get("infrastructure"):
        signals.append("云与基础设施分发正在影响模型可获得性、部署成本和企业采购路径。")
    if category_counts.get("application"):
        signals.append("应用场景落地显示 AI 能力正在进入更具体的办公、研发、内容和行业流程。")
    if source_channel_counts.get("social_media"):
        signals.append("开发者社区反馈可以补充官方与媒体信息，用于观察体验波动、成本敏感度和舆论热点。")
    multi_source_clusters = [cluster for cluster in topic_clusters if cluster.source_count >= 2]
    if multi_source_clusters:
        labels = "、".join(cluster.canonical_topic for cluster in multi_source_clusters[:4])
        signals.append(
            f"{len(multi_source_clusters)} 个热点出现多源覆盖（{labels}），说明这些事件存在官方发布、媒体解读、聚合扩散或社区反馈链路。"
        )

    top_event_signals = [
        event.trend_signal
        for event in sorted(events, key=lambda event: event.importance_score, reverse=True)
        if event.trend_signal
    ]
    return _unique_preserve_order([*signals, *top_event_signals])[:8]


def build_topic_clusters(events: list[StructuredAIEvent]) -> list[TopicClusterSummary]:
    grouped: dict[str, list[StructuredAIEvent]] = {}
    for event in events:
        topic = event.canonical_topic or "uncategorized"
        grouped.setdefault(topic, []).append(event)

    clusters: list[TopicClusterSummary] = []
    for topic, topic_events in grouped.items():
        ordered = sorted(topic_events, key=lambda event: event.importance_score, reverse=True)
        clusters.append(
            TopicClusterSummary(
                canonical_topic=topic,
                source_count=len(topic_events),
                source_channels=_unique_preserve_order(
                    [channel_label(event.source_channel) for event in topic_events]
                ),
                source_languages=_unique_preserve_order(
                    [language_label(event.source_language or event.language) for event in topic_events]
                ),
                representative_title=ordered[0].title,
                representative_sources=_unique_preserve_order(
                    [event.source for event in topic_events]
                )[:4],
                has_official_source=any(event.source_channel == "official" for event in topic_events),
                has_community_feedback=any(
                    event.source_channel == "social_media" or event.topic_role == "community_feedback"
                    for event in topic_events
                ),
            )
        )
    return sorted(clusters, key=lambda cluster: (-cluster.source_count, cluster.canonical_topic))


def _build_risks_and_opportunities(events: list[StructuredAIEvent]) -> list[str]:
    if not events:
        return ["没有可用的已校验事件，因此不生成行业风险判断。"]

    risks = []
    for event in sorted(events, key=lambda item: item.importance_score, reverse=True):
        if event.industry_risk and not _contains_system_risk_term(event.industry_risk):
            risks.append(f"{event.title}：{event.industry_risk}")

    if risks:
        return _unique_preserve_order(risks)[:6]
    return ["当前样本未形成明确行业风险信号，建议继续结合更多来源观察竞争、合规、成本和用户体验变化。"]


def _build_opportunity_signals(events: list[StructuredAIEvent]) -> list[str]:
    if not events:
        return ["没有可用的已校验事件，因此不生成行业机会提示。"]

    opportunities = [
        f"{event.title}：{event.industry_opportunity}"
        for event in sorted(events, key=lambda item: item.importance_score, reverse=True)
        if event.industry_opportunity
    ]
    return _unique_preserve_order(opportunities)[:6] or [
        "当前样本未形成明确行业机会提示，建议继续观察模型 API、企业 Agent workflow、AI coding、云基础设施和垂直应用。"
    ]


def _build_visualization_notes() -> list[str]:
    return [
        "来源渠道 × 来源语言覆盖矩阵回答：样本是否覆盖中英混合与多渠道来源。",
        "事件发布时间线回答：事件在时间上如何分布，哪些日期出现信息密集。",
        "分类分布图回答：今日 AI 信息主要集中在模型能力、智能体与工作流、基础设施还是应用产品。",
        "重要性 × 置信度散点图回答：哪些高重要性事件值得优先关注，哪些事件需要进一步人工复核。",
        "影响领域分布回答：事件主要影响哪些业务或技术方向。",
        "Rule vs LLM 评估对比回答：不同 extractor 在分类准确率、来源追溯和失败项上的差异。",
    ]


def _build_source_channel_counts(events: list[StructuredAIEvent]) -> dict[str, int]:
    counts = Counter(event.source_channel or "unknown" for event in events)
    return dict(counts)


def _build_source_language_counts(events: list[StructuredAIEvent]) -> dict[str, int]:
    counts = Counter(event.source_language or event.language or "unknown" for event in events)
    return dict(counts)


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            unique_values.append(cleaned)
            seen.add(cleaned)
    return unique_values


def _contains_system_risk_term(text: str) -> bool:
    normalized = text.lower()
    return any(term.lower() in normalized for term in FORBIDDEN_SYSTEM_RISK_TERMS)


def channel_label(source_channel: str | None) -> str:
    return {
        "official": "官方渠道",
        "tech_media": "科技媒体",
        "aggregator": "聚合平台",
        "social_media": "社交/社区渠道",
        "unknown": "未标注渠道",
    }.get(source_channel or "unknown", source_channel or "未标注渠道")


def language_label(source_language: str | None) -> str:
    return {
        "en": "英文来源",
        "zh": "中文来源",
        "unknown": "未标注语言",
    }.get(source_language or "unknown", source_language or "未标注语言")


def optional_text(value: str | None) -> str:
    return value if value else "未提供"


def checked(value: object) -> str:
    return "x" if value is True else " "


def pass_label(value: object) -> str:
    return "通过" if value is True else "未通过"


def yes_no(value: bool) -> str:
    return "是" if value else "否"
