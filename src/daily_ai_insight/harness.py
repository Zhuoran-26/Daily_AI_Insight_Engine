"""Harness checks for source grounding, confidence, schema, and loop control."""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from daily_ai_insight.errors import HarnessError, LoopGuardError, SourceIntegrityError
from daily_ai_insight.models import RawNewsItem, StructuredAIEvent

SUPPORTED_EXTRACTORS = ("rule", "mock-llm", "openai-compatible")


class HarnessConfig(BaseModel):
    max_items: int = Field(default=20, ge=1)
    min_items: int = Field(default=10, ge=0)
    max_processing_steps: int = Field(default=8, ge=1)
    min_confidence: float = Field(default=0.5, ge=0, le=1)
    require_source_url: bool = True
    allow_synthetic_data: bool = True


class PipelineHarness:
    """Fail-fast guardrail for future LLM/Agent stages.

    The harness does not perform business analysis. It constrains the pipeline so
    later LLM/Agent integrations cannot add hallucinated sources, ungrounded
    events, low-confidence records, or uncontrolled processing loops.
    """

    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.config = config or HarnessConfig()
        self.input_count = 0
        self.output_count = 0
        self.last_step_count = 0
        self.source_integrity_passed = False
        self.schema_compliance_passed = False
        self.grounding_passed = False
        self.evidence_grounding_passed = False
        self.loop_guard_passed = False
        self.extractor_name = ""

    def check_extractor_name(self, extractor_name: str) -> None:
        if extractor_name not in SUPPORTED_EXTRACTORS:
            raise HarnessError(
                f"Unsupported extractor '{extractor_name}'. Supported extractors: "
                f"{', '.join(SUPPORTED_EXTRACTORS)}"
            )
        self.extractor_name = extractor_name

    def check_input_size(self, raw_items: list[RawNewsItem]) -> None:
        self.input_count = len(raw_items)
        if self.input_count < self.config.min_items:
            raise HarnessError(
                f"Input size {self.input_count} is below minimum {self.config.min_items}"
            )
        if self.input_count > self.config.max_items:
            raise HarnessError(
                f"Input size {self.input_count} exceeds maximum {self.config.max_items}"
            )

    def check_source_integrity(self, raw_items: list[RawNewsItem]) -> None:
        for index, item in enumerate(raw_items):
            url = item.url.strip()
            if self.config.require_source_url and not url:
                raise SourceIntegrityError(f"Raw item {index} is missing required source url")
            if self._is_suspicious_url(url):
                raise SourceIntegrityError(f"Raw item {index} has suspicious source url: {url}")
        self.source_integrity_passed = True

    def check_step_budget(self, step_count: int) -> None:
        self.last_step_count = step_count
        if step_count > self.config.max_processing_steps:
            raise LoopGuardError(
                f"Processing step count {step_count} exceeds budget {self.config.max_processing_steps}"
            )
        self.loop_guard_passed = True

    def check_schema_compliance(self, events: list[object]) -> None:
        if not events:
            raise HarnessError("Extractor produced no structured events")
        for index, event in enumerate(events):
            if isinstance(event, StructuredAIEvent):
                continue
            try:
                StructuredAIEvent.model_validate(event)
            except PydanticValidationError as exc:
                raise HarnessError(
                    f"Extractor output at index {index} failed schema compliance: {exc}"
                ) from exc
        self.schema_compliance_passed = True

    def check_event_grounding(
        self,
        events: list[StructuredAIEvent],
        raw_items: list[RawNewsItem],
    ) -> None:
        for index, event in enumerate(events):
            if self._find_grounded_raw_item(event, raw_items) is None:
                raise HarnessError(
                    "Structured event at index "
                    f"{index} is not grounded in raw source/title/url: {event.title}"
                )
        self.output_count = len(events)
        self.grounding_passed = True

    def check_single_event_grounding(
        self,
        event: StructuredAIEvent,
        raw_item: RawNewsItem,
    ) -> None:
        if event.title != raw_item.title:
            raise HarnessError("Structured event title does not match raw item title")
        if event.source != raw_item.source:
            raise HarnessError("Structured event source does not match raw item source")
        if event.url != raw_item.url:
            raise HarnessError("Structured event url does not match raw item url")

    def check_evidence_grounding(
        self,
        events: list[StructuredAIEvent],
        raw_items: list[RawNewsItem],
    ) -> None:
        raw_by_key = {
            self._grounding_key(item.title, item.source, item.url): item
            for item in raw_items
        }
        for index, event in enumerate(events):
            raw_item = raw_by_key.get(self._grounding_key(event.title, event.source, event.url))
            if raw_item is None:
                raise HarnessError(
                    f"Structured event at index {index} has evidence but no grounded raw item"
                )
            if not self._is_evidence_grounded(event.evidence, raw_item):
                raise HarnessError(
                    f"Structured event at index {index} evidence is not grounded in raw title or summary"
                )
        self.evidence_grounding_passed = True

    def check_single_evidence_grounding(
        self,
        event: StructuredAIEvent,
        raw_item: RawNewsItem,
    ) -> None:
        if not self._is_evidence_grounded(event.evidence, raw_item):
            raise HarnessError("Structured event evidence is not grounded in raw title or summary")

    def check_confidence(self, events: list[StructuredAIEvent]) -> None:
        for index, event in enumerate(events):
            if event.confidence < self.config.min_confidence:
                raise HarnessError(
                    "Structured event at index "
                    f"{index} has confidence {event.confidence} below threshold "
                    f"{self.config.min_confidence}"
                )

    def build_summary(self) -> dict[str, str | int | float | bool]:
        return {
            "input_count": self.input_count,
            "output_count": self.output_count,
            "extractor_name": self.extractor_name,
            "source_integrity_passed": self.source_integrity_passed,
            "schema_compliance_passed": self.schema_compliance_passed,
            "grounding_passed": self.grounding_passed,
            "evidence_grounding_passed": self.evidence_grounding_passed,
            "loop_guard_passed": self.loop_guard_passed,
            "min_confidence": self.config.min_confidence,
            "deterministic_baseline": True,
            "steps_used": self.last_step_count,
            "max_processing_steps": self.config.max_processing_steps,
        }

    @staticmethod
    def _grounding_key(title: str, source: str, url: str) -> tuple[str, str, str]:
        return (title.strip().lower(), source.strip().lower(), url.strip().lower())

    def _find_grounded_raw_item(
        self,
        event: StructuredAIEvent,
        raw_items: list[RawNewsItem],
    ) -> RawNewsItem | None:
        event_key = self._grounding_key(event.title, event.source, event.url)
        for item in raw_items:
            if self._grounding_key(item.title, item.source, item.url) == event_key:
                return item
        return None

    @staticmethod
    def _is_evidence_grounded(evidence: str, raw_item: RawNewsItem) -> bool:
        normalized_evidence = evidence.strip().lower()
        if not normalized_evidence:
            return False

        raw_title = raw_item.title.strip().lower()
        raw_summary = raw_item.summary.strip().lower()
        if (
            raw_title in normalized_evidence
            or raw_summary in normalized_evidence
            or normalized_evidence in raw_title
            or normalized_evidence in raw_summary
        ):
            return True

        # Conservative fallback for short LLM evidence phrases. Exact title or
        # summary grounding is preferred, but short copied fragments can be valid.
        raw_words = set(PipelineHarness._meaningful_words(f"{raw_title} {raw_summary}"))
        evidence_words = set(PipelineHarness._meaningful_words(normalized_evidence))
        return len(raw_words & evidence_words) >= 3

    @staticmethod
    def _meaningful_words(text: str) -> list[str]:
        cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
        return [word for word in cleaned.split() if len(word) >= 5]

    @staticmethod
    def _is_suspicious_url(url: str) -> bool:
        normalized = url.strip().lower()
        suspicious_prefixes = ("hallucinated://", "fake://", "unknown://")
        suspicious_fragments = ("example.com/unknown",)
        return (
            not normalized
            or normalized == "about:blank"
            or normalized.startswith(suspicious_prefixes)
            or any(fragment in normalized for fragment in suspicious_fragments)
        )
