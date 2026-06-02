"""Raw news loading and normalization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from daily_ai_insight.errors import ValidationError
from daily_ai_insight.models import RawNewsItem

RAW_FIELDS = ("title", "summary", "source", "url", "published_at", "language")
PROVENANCE_FIELDS = (
    "source_channel",
    "source_language",
    "selection_reason",
    "collected_at",
    "canonical_topic",
    "topic_role",
)


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    raise ValidationError("Raw news JSON must be a list or an object with an 'items' list")


def load_raw_news(path: str | Path) -> list[RawNewsItem]:
    """Load JSON records, trim basic fields, and skip records without title or summary."""

    input_path = Path(path)
    with input_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    raw_items: list[RawNewsItem] = []
    for record in _extract_records(payload):
        if not isinstance(record, dict):
            raise ValidationError("Each raw news record must be an object")

        cleaned = {field: _clean_string(record.get(field, "")) for field in RAW_FIELDS}
        cleaned.update(
            {
                field: _clean_string(record.get(field)) or None
                for field in PROVENANCE_FIELDS
            }
        )
        if not cleaned["title"] or not cleaned["summary"]:
            continue
        if not cleaned["language"]:
            cleaned["language"] = "unknown"
        raw_items.append(RawNewsItem(**cleaned))

    return raw_items
