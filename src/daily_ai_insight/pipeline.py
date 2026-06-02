"""Harnessed MVP pipeline with pluggable extractor strategies."""

from __future__ import annotations

import json
from pathlib import Path

from daily_ai_insight.extractors import BaseExtractor, create_extractor
from daily_ai_insight.harness import HarnessConfig, PipelineHarness
from daily_ai_insight.models import DailyInsightReport, StructuredAIEvent
from daily_ai_insight.normalize import load_raw_news
from daily_ai_insight.report import build_daily_report, write_report
from daily_ai_insight.validate import validate_raw_items, validate_structured_events


def run_pipeline(
    input_path: str | Path,
    extractor_name: str = "rule",
    events_output_path: str | Path = "data/processed/structured_events.json",
    report_output_path: str | Path = "outputs/daily_report.md",
    harness_config: HarnessConfig | None = None,
    extractor: BaseExtractor | None = None,
) -> DailyInsightReport:
    harness = PipelineHarness(harness_config)
    selected_extractor = extractor or create_extractor(extractor_name)
    harness.check_extractor_name(selected_extractor.name)
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
    events = selected_extractor.extract(raw_items)

    advance_step()
    harness.check_schema_compliance(events)
    events = validate_structured_events(events)

    advance_step()
    harness.check_event_grounding(events, raw_items)
    harness.check_evidence_grounding(events, raw_items)
    harness.check_confidence(events)

    advance_step()
    report = build_daily_report(events, harness.build_summary())

    _write_events(events, events_output_path)
    write_report(report, report_output_path)
    return report


def _write_events(events: list[StructuredAIEvent], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [event.model_dump(mode="json") for event in events]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
