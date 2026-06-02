"""Schema and field validation helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from daily_ai_insight.errors import ValidationError
from daily_ai_insight.models import RawNewsItem, StructuredAIEvent


def _ensure_list(values: Iterable[Any] | None, label: str) -> list[Any]:
    if values is None:
        raise ValidationError(f"{label} validation failed: input is empty")
    items = list(values)
    if not items:
        raise ValidationError(f"{label} validation failed: input is empty")
    return items


def validate_raw_items(items: Iterable[RawNewsItem | dict[str, Any]] | None) -> list[RawNewsItem]:
    validated: list[RawNewsItem] = []
    for index, item in enumerate(_ensure_list(items, "RawNewsItem")):
        try:
            raw_item = item if isinstance(item, RawNewsItem) else RawNewsItem.model_validate(item)
        except PydanticValidationError as exc:
            raise ValidationError(f"RawNewsItem at index {index} failed schema validation: {exc}") from exc

        if not raw_item.source.strip():
            raise ValidationError(f"RawNewsItem at index {index} has empty source")
        if not raw_item.url.strip():
            raise ValidationError(f"RawNewsItem at index {index} has empty url")
        validated.append(raw_item)
    return validated


def validate_structured_events(
    events: Iterable[StructuredAIEvent | dict[str, Any]] | None,
) -> list[StructuredAIEvent]:
    validated: list[StructuredAIEvent] = []
    for index, event in enumerate(_ensure_list(events, "StructuredAIEvent")):
        try:
            structured_event = (
                event if isinstance(event, StructuredAIEvent) else StructuredAIEvent.model_validate(event)
            )
        except PydanticValidationError as exc:
            raise ValidationError(
                f"StructuredAIEvent at index {index} failed schema validation: {exc}"
            ) from exc

        if not structured_event.source.strip():
            raise ValidationError(f"StructuredAIEvent at index {index} has empty source")
        if not structured_event.url.strip():
            raise ValidationError(f"StructuredAIEvent at index {index} has empty url")
        if not 0 <= structured_event.importance_score <= 10:
            raise ValidationError(f"StructuredAIEvent at index {index} has invalid importance_score")
        if not 0 <= structured_event.confidence <= 1:
            raise ValidationError(f"StructuredAIEvent at index {index} has invalid confidence")
        validated.append(structured_event)
    return validated
