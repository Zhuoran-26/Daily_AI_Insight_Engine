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
    source_channel: str | None = None
    source_language: str | None = None
    selection_reason: str | None = None
    collected_at: str | None = None

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

    @field_validator(
        "source_channel",
        "source_language",
        "selection_reason",
        "collected_at",
        mode="before",
    )
    @classmethod
    def empty_optional_provenance_to_none(cls, value: object) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


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
    source_channel: str | None = None
    source_language: str | None = None
    selection_reason: str | None = None
    collected_at: str | None = None
    background: str | None = None
    industry_impact: str | None = None
    trend_signal: str | None = None
    industry_risk: str | None = None
    industry_opportunity: str | None = None
    decision_hint: str | None = None
    llm_generated: bool = False
    requires_human_review: bool = False

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

    @field_validator(
        "source_channel",
        "source_language",
        "selection_reason",
        "collected_at",
        "background",
        "industry_impact",
        "trend_signal",
        "industry_risk",
        "industry_opportunity",
        "decision_hint",
        mode="before",
    )
    @classmethod
    def empty_optional_text_to_none(cls, value: object) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class DailyInsightReport(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    date: str
    total_events: int = Field(ge=0)
    events: list[StructuredAIEvent] = Field(default_factory=list)
    top_events: list[StructuredAIEvent]
    category_counts: dict[str, int]
    source_channel_counts: dict[str, int] = Field(default_factory=dict)
    source_language_counts: dict[str, int] = Field(default_factory=dict)
    key_takeaways: list[str]
    trend_signals: list[str]
    risks_and_opportunities: list[str]
    opportunity_signals: list[str] = Field(default_factory=list)
    visualization_notes: list[str] = Field(default_factory=list)
    harness_summary: dict[str, str | int | float | bool]

    @field_validator("date")
    @classmethod
    def require_date(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("date must not be empty")
        return value.strip()


class EvaluationItemResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str
    expected_category: str
    predicted_category: str | None
    category_match: bool
    confidence: float | None = Field(default=None, ge=0, le=1)
    grounded: bool
    error: str | None


class EvaluationSummary(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    extractor: str
    total_items: int = Field(ge=0)
    successful_items: int = Field(ge=0)
    failed_items: int = Field(ge=0)
    category_accuracy: float = Field(ge=0, le=1)
    grounding_pass_rate: float = Field(ge=0, le=1)
    average_confidence: float = Field(ge=0, le=1)
    item_results: list[EvaluationItemResult]
