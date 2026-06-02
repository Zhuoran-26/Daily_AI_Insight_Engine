"""Markdown report generation from validated structured events."""

from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from jinja2 import Template

from daily_ai_insight.models import DailyInsightReport, StructuredAIEvent

REPORT_TEMPLATE = """# Daily AI Insight Report

## Date

{{ report.date }}

## Total Events

{{ report.total_events }}

## Top Events

{% for event in report.top_events -%}
{{ loop.index }}. **{{ event.title }}**
   - Source: {{ event.source }}
   - URL: {{ event.url }}
   - Category: {{ event.category }}
   - Event Type: {{ event.event_type }}
   - Importance: {{ "%.1f"|format(event.importance_score) }}
   - Confidence: {{ "%.2f"|format(event.confidence) }}
   - Summary: {{ event.summary }}
   - Evidence: {{ event.evidence }}
{% endfor %}

## Category Distribution

{% for category, count in report.category_counts.items() -%}
- {{ category }}: {{ count }}
{% endfor %}

## Key Takeaways

{% for takeaway in report.key_takeaways -%}
- {{ takeaway }}
{% endfor %}

## Trend Signals

{% for signal in report.trend_signals -%}
- {{ signal }}
{% endfor %}

## Risks and Opportunities

{% for item in report.risks_and_opportunities -%}
- {{ item }}
{% endfor %}

## Harness Summary

{% for key, value in report.harness_summary.items() -%}
- {{ key }}: {{ value }}
{% endfor %}

## Methodology Note

This version is a deterministic baseline. It does not call a real LLM API, crawler, or UI layer.

Harness Engineering is used to prevent hallucinated sources, prevent events without source grounding, prevent infinite loops through a processing step budget, and prevent low-confidence results from directly entering the final report.

Future extensions can add an LLM extractor, stricter schema validation, an AI reviewer, and a human review queue. Those integrations must remain behind the same source grounding, confidence threshold, loop budget, deterministic fallback, and automated test controls.
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
        return ["No validated events were available for analysis."]

    leading_category = max(category_counts.items(), key=lambda item: item[1])[0]
    top_event = max(events, key=lambda event: event.importance_score)
    source_count = len({event.source for event in events})
    return [
        f"{leading_category} is the largest category in the validated sample with "
        f"{category_counts[leading_category]} events.",
        f"The top ranked event is '{top_event.title}' from {top_event.source}.",
        f"The report is grounded in {source_count} distinct source labels from raw inputs.",
    ]


def _build_trend_signals(
    events: list[StructuredAIEvent],
    category_counts: dict[str, int],
) -> list[str]:
    if not events:
        return ["No trend signals were available because no validated events were provided."]

    leading_category, leading_count = max(category_counts.items(), key=lambda item: item[1])
    high_importance_count = sum(1 for event in events if event.importance_score >= 6.0)
    agent_count = category_counts.get("agent", 0)
    application_count = category_counts.get("application", 0)
    infrastructure_count = category_counts.get("infrastructure", 0)

    signals = [
        f"{leading_category} leads the sample with {leading_count} validated events, indicating the dominant theme for this run.",
        f"{high_importance_count} events have importance score >= 6.0, suggesting several items are worth daily-report attention.",
    ]
    if agent_count or application_count:
        productization_count = agent_count + application_count
        productization_word = "event" if productization_count == 1 else "events"
        signals.append(
            f"Agent and application activity accounts for {productization_count} {productization_word}, showing productization momentum beyond model releases."
        )
    if infrastructure_count:
        infrastructure_word = "event" if infrastructure_count == 1 else "events"
        signals.append(
            f"Infrastructure appears in {infrastructure_count} {infrastructure_word}, indicating continued demand for deployment and compute foundations."
        )
    return signals


def _build_risks_and_opportunities(
    events: list[StructuredAIEvent],
    category_counts: dict[str, int],
) -> list[str]:
    if not events:
        return ["Risk: no validated events were available, so no opportunity or risk judgment should be made."]

    average_confidence = sum(event.confidence for event in events) / len(events)
    top_event = max(events, key=lambda event: event.importance_score)
    leading_category = max(category_counts.items(), key=lambda item: item[1])[0]

    return [
        f"Opportunity: the leading {leading_category} theme can guide deeper follow-up analysis and demo storytelling.",
        f"Opportunity: the top event '{top_event.title}' provides a concrete anchor for the daily report.",
        f"Risk: average extraction confidence is {average_confidence:.2f}; low-confidence or semantically ambiguous items should remain reviewable.",
        "Risk: deterministic category rules can misclassify complex product or agent news, so LLM extraction should stay behind harness checks.",
    ]
