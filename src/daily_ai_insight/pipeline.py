"""Deterministic MVP pipeline with harness checks."""

from __future__ import annotations

import json
from pathlib import Path

from daily_ai_insight.harness import HarnessConfig, PipelineHarness
from daily_ai_insight.models import DailyInsightReport, RawNewsItem, StructuredAIEvent
from daily_ai_insight.normalize import load_raw_news
from daily_ai_insight.report import build_daily_report, write_report
from daily_ai_insight.validate import validate_raw_items, validate_structured_events

MAJOR_ENTITIES = (
    "OpenAI",
    "Google",
    "Anthropic",
    "NVIDIA",
    "Meta",
    "Microsoft",
    "Amazon",
    "Apple",
    "Mistral",
    "Hugging Face",
)

IMPORTANCE_KEYWORDS = ("release", "launch", "benchmark", "funding", "regulation")


def run_pipeline(
    input_path: str | Path,
    events_output_path: str | Path = "data/processed/structured_events.json",
    report_output_path: str | Path = "outputs/daily_report.md",
    harness_config: HarnessConfig | None = None,
) -> DailyInsightReport:
    harness = PipelineHarness(harness_config)
    step_count = 0

    def advance_step() -> None:
        nonlocal step_count
        step_count += 1
        harness.check_step_budget(step_count)

    advance_step()
    raw_items = load_raw_news(input_path)

    advance_step()
    raw_items = validate_raw_items(raw_items)

    advance_step()
    harness.check_input_size(raw_items)
    harness.check_source_integrity(raw_items)

    advance_step()
    events = extract_structured_events(raw_items)

    advance_step()
    events = validate_structured_events(events)

    advance_step()
    harness.check_event_grounding(events, raw_items)
    harness.check_confidence(events)

    advance_step()
    report = build_daily_report(events, harness.build_summary())

    _write_events(events, events_output_path)
    write_report(report, report_output_path)
    return report


def extract_structured_events(raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
    events: list[StructuredAIEvent] = []
    for index, item in enumerate(raw_items, start=1):
        category = classify_category(item)
        events.append(
            StructuredAIEvent(
                id=f"evt-{index:03d}",
                title=item.title,
                source=item.source,
                url=item.url,
                published_at=item.published_at,
                language=item.language,
                category=category,
                event_type=classify_event_type(item),
                entities=extract_entities(item),
                impact_areas=impact_areas_for_category(category),
                importance_score=score_importance(item),
                # Future LLM extractors may produce confidence, but harness checks
                # must still block low-confidence output before report generation.
                confidence=0.7,
                summary=item.summary,
                evidence=f"{item.source}: {item.summary}",
            )
        )
    return events


def classify_category(item: RawNewsItem) -> str:
    text = _combined_text(item)
    if any(keyword in text for keyword in ("model", "llm", "gpt", "claude", "gemini")):
        return "model"
    if "agent" in text:
        return "agent"
    if any(keyword in text for keyword in ("chip", "gpu", "nvidia")):
        return "infrastructure"
    return "application"


def classify_event_type(item: RawNewsItem) -> str:
    text = _combined_text(item)
    if any(keyword in text for keyword in ("release", "launch")):
        return "release"
    if "benchmark" in text:
        return "benchmark"
    if "funding" in text:
        return "funding"
    if "regulation" in text or "policy" in text:
        return "regulation"
    if "agent" in text:
        return "agent_update"
    return "application_update"


def extract_entities(item: RawNewsItem) -> list[str]:
    text = f"{item.title} {item.summary} {item.source}".lower()
    entities = [entity for entity in MAJOR_ENTITIES if entity.lower() in text]
    return entities or [item.source]


def impact_areas_for_category(category: str) -> list[str]:
    return {
        "model": ["model_capabilities"],
        "agent": ["automation"],
        "infrastructure": ["compute"],
        "application": ["productivity"],
    }[category]


def score_importance(item: RawNewsItem) -> float:
    text = _combined_text(item)
    score = 4.0
    if any(entity.lower() in text for entity in MAJOR_ENTITIES):
        score += 2.0
    score += sum(1.0 for keyword in IMPORTANCE_KEYWORDS if keyword in text)
    return min(10.0, round(score, 1))


def _combined_text(item: RawNewsItem) -> str:
    return f"{item.title} {item.summary}".lower()


def _write_events(events: list[StructuredAIEvent], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [event.model_dump(mode="json") for event in events]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
