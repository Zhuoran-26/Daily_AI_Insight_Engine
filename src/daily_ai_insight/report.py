"""Markdown report generation from validated structured events."""

from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from jinja2 import Template

from daily_ai_insight.models import DailyInsightReport, StructuredAIEvent

REPORT_TEMPLATE = """# AI 行业洞察日报

## 日期

{{ report.date }}

## 事件总数

{{ report.total_events }}

## 今日主要热点

{% for event in report.top_events -%}
{{ loop.index }}. **{{ event.title }}**
   - 来源: {{ event.source }}
   - URL: {{ event.url }}
   - 分类: {{ event.category }}
   - 事件类型: {{ event.event_type }}
   - 重要性: {{ "%.1f"|format(event.importance_score) }}
   - 置信度: {{ "%.2f"|format(event.confidence) }}
   - 摘要: {{ event.summary }}
   - 证据: {{ event.evidence }}
{% endfor %}

## 分类分布

{% for category, count in report.category_counts.items() -%}
- {{ category }}: {{ count }}
{% endfor %}

## 关键结论

{% for takeaway in report.key_takeaways -%}
- {{ takeaway }}
{% endfor %}

## 趋势信号

{% for signal in report.trend_signals -%}
- {{ signal }}
{% endfor %}

## 风险与机会

{% for item in report.risks_and_opportunities -%}
- {{ item }}
{% endfor %}

## Harness 校验摘要

{% for key, value in report.harness_summary.items() -%}
- {{ key }}: {{ value }}
{% endfor %}

## 方法说明

当前日报由 deterministic baseline 生成，不依赖真实 LLM API 或爬虫。

Harness Engineering 用于阻止幻觉来源、无来源追溯事件、不可控 agent loop，以及低置信度结果直接进入最终报告。

后续可以继续接入 LLM extractor、更严格的 Schema 校验、AI Reviewer 和人工复审队列，但这些能力必须继续受 source grounding、confidence threshold、loop budget、deterministic fallback 和自动化测试约束。
"""


def build_daily_report(
    events: list[StructuredAIEvent],
    harness_summary: dict[str, str | int | float | bool],
    report_date: str | None = None,
) -> DailyInsightReport:
    category_counts = dict(Counter(event.category for event in events))
    top_events = sorted(events, key=lambda event: event.importance_score, reverse=True)[:5]
    key_takeaways = _build_key_takeaways(events, category_counts)
    trend_signals = _build_trend_signals(events, category_counts)
    risks_and_opportunities = _build_risks_and_opportunities(events, category_counts)
    return DailyInsightReport(
        date=report_date or date.today().isoformat(),
        total_events=len(events),
        top_events=top_events,
        category_counts=category_counts,
        key_takeaways=key_takeaways,
        trend_signals=trend_signals,
        risks_and_opportunities=risks_and_opportunities,
        harness_summary=harness_summary,
    )


def render_report(report: DailyInsightReport) -> str:
    return Template(REPORT_TEMPLATE).render(report=report)


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
        f"最高优先级事件是来自 {top_event.source} 的 “{top_event.title}”。",
        f"本报告基于 {source_count} 个不同来源标签生成，所有事件均保留 source/url 追溯信息。",
    ]


def _build_trend_signals(
    events: list[StructuredAIEvent],
    category_counts: dict[str, int],
) -> list[str]:
    if not events:
        return ["没有可用的已校验事件，因此不生成趋势信号。"]

    leading_category, leading_count = max(category_counts.items(), key=lambda item: item[1])
    high_importance_count = sum(1 for event in events if event.importance_score >= 6.0)
    agent_count = category_counts.get("agent", 0)
    application_count = category_counts.get("application", 0)
    infrastructure_count = category_counts.get("infrastructure", 0)

    signals = [
        f"{leading_category} 以 {leading_count} 条已校验事件领先，说明这是本次样本中的主要关注方向。",
        f"{high_importance_count} 条事件的重要性评分不低于 6.0，说明本次日报中有多条值得重点跟进的信息。",
    ]
    if agent_count or application_count:
        productization_count = agent_count + application_count
        signals.append(
            f"Agent 与 application 相关事件共 {productization_count} 条，显示 AI 能力正在从模型发布继续走向产品化和工作流落地。"
        )
    if infrastructure_count:
        signals.append(
            f"infrastructure 相关事件共 {infrastructure_count} 条，说明部署、算力和平台基础设施仍是 AI 生态的重要支撑。"
        )
    return signals


def _build_risks_and_opportunities(
    events: list[StructuredAIEvent],
    category_counts: dict[str, int],
) -> list[str]:
    if not events:
        return ["风险：没有可用的已校验事件，因此不应生成机会或风险判断。"]

    average_confidence = sum(event.confidence for event in events) / len(events)
    top_event = max(events, key=lambda event: event.importance_score)
    leading_category = max(category_counts.items(), key=lambda item: item[1])[0]

    return [
        f"机会：{leading_category} 作为本次主导主题，可作为后续深度分析和业务演示的重点方向。",
        f"机会：Top 事件 “{top_event.title}” 可作为日报解读的具体锚点。",
        f"风险：当前平均抽取置信度为 {average_confidence:.2f}，低置信度或语义模糊的信息仍应进入复审。",
        "风险：deterministic rule 可能误判复杂产品或 Agent 类新闻，因此 LLM 抽取也必须继续受 Harness 校验约束。",
    ]
