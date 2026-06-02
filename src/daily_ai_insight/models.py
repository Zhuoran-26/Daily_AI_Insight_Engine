"""Pydantic schemas for the harnessed MVP pipeline."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RawNewsItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str
    summary: str
    source: str
    url: str
    published_at: str
    language: str

    @field_validator("title", "summary", "source", "url")
    @classmethod
    def require_non_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return value.strip()

    @field_validator("language")
    @classmethod
    def default_unknown_language(cls, value: str) -> str:
        if not value or not value.strip():
            return "unknown"
        return value.strip()


class StructuredAIEvent(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str
    title: str
    source: str
    url: str
    published_at: str
    language: str
    category: str
    event_type: str
    entities: list[str]
    impact_areas: list[str]
    importance_score: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    summary: str
    evidence: str

    @field_validator(
        "id",
        "title",
        "source",
        "url",
        "published_at",
        "language",
        "category",
        "event_type",
        "summary",
        "evidence",
    )
    @classmethod
    def require_non_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return value.strip()


class DailyInsightReport(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    date: str
    total_events: int = Field(ge=0)
    top_events: list[StructuredAIEvent]
    category_counts: dict[str, int]
    key_takeaways: list[str]
    harness_summary: dict[str, str | int | float | bool]

    @field_validator("date")
    @classmethod
    def require_date(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("date must not be empty")
        return value.strip()
