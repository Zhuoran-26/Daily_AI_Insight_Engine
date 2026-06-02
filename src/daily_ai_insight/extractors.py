"""Extractor strategies for deterministic and optional LLM-backed extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from daily_ai_insight.errors import PipelineError
from daily_ai_insight.llm_client import OpenAICompatibleClient
from daily_ai_insight.models import RawNewsItem, StructuredAIEvent

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
SUPPORTED_EXTRACTORS = ("rule", "mock-llm", "openai-compatible")


class BaseExtractor(ABC):
    name: str

    @abstractmethod
    def extract(self, raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
        """Extract structured events from normalized raw news items."""


class RuleBasedExtractor(BaseExtractor):
    name = "rule"

    def extract(self, raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
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
                    # Deterministic baseline confidence. Future LLM extractors
                    # may emit confidence, but harness checks still gate output.
                    confidence=0.7,
                    summary=item.summary,
                    evidence=f"{item.source}: {item.summary}",
                )
            )
        return events


class MockLLMExtractor(BaseExtractor):
    """Test double for LLM extraction workflows.

    Modes intentionally simulate both valid and unsafe model behavior so tests
    can prove that schema validation, grounding, and confidence gates still run.
    """

    name = "mock-llm"

    def __init__(self, mode: str = "valid") -> None:
        allowed_modes = {"valid", "invalid", "hallucinated", "low-confidence"}
        if mode not in allowed_modes:
            raise PipelineError(f"Unsupported mock LLM mode: {mode}")
        self.mode = mode

    def extract(self, raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
        if self.mode == "invalid":
            return [{"not": "a structured event"}]  # type: ignore[return-value]

        events: list[StructuredAIEvent] = []
        for index, item in enumerate(raw_items, start=1):
            category = semantic_category(item)
            source = item.source
            url = item.url
            confidence = 0.82

            if self.mode == "hallucinated" and index == 1:
                source = "Invented AI Wire"
                url = "hallucinated://invented-source"
            if self.mode == "low-confidence" and index == 1:
                confidence = 0.3

            events.append(
                StructuredAIEvent(
                    id=f"mock-evt-{index:03d}",
                    title=item.title,
                    source=source,
                    url=url,
                    published_at=item.published_at,
                    language=item.language,
                    category=category,
                    event_type=classify_event_type(item),
                    entities=extract_entities(item),
                    impact_areas=impact_areas_for_category(category),
                    importance_score=score_importance(item),
                    confidence=confidence,
                    summary=item.summary,
                    evidence=f"{item.source}: {item.summary}",
                )
            )
        return events


class OpenAICompatibleExtractor(BaseExtractor):
    """Optional OpenAI-compatible interface position.

    This class intentionally avoids adding an SDK dependency in Phase 4. It reads
    environment configuration and fails clearly if a real adapter is not ready.
    """

    name = "openai-compatible"

    def __init__(
        self,
        prompt_path: str | Path = "prompts/extraction_prompt.md",
        client: OpenAICompatibleClient | None = None,
    ) -> None:
        self.prompt_path = Path(prompt_path)
        self.client = client

    def extract(self, raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
        client = self.client or OpenAICompatibleClient.from_environment()
        prompt = self._load_prompt()
        response = client.extract_events(prompt=prompt, raw_items=raw_items)
        return self._validate_response(response)

    def _load_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise PipelineError(f"Extraction prompt not found: {self.prompt_path}")
        return self.prompt_path.read_text(encoding="utf-8")

    @staticmethod
    def _validate_response(response: Any) -> list[StructuredAIEvent]:
        if not isinstance(response, list):
            raise PipelineError("OpenAI-compatible extractor response must be a list")

        events: list[StructuredAIEvent] = []
        for index, item in enumerate(response):
            try:
                events.append(StructuredAIEvent.model_validate(item))
            except PydanticValidationError as exc:
                raise PipelineError(
                    f"OpenAI-compatible extractor response item {index} failed schema validation: {exc}"
                ) from exc
        return events


def create_extractor(extractor_name: str) -> BaseExtractor:
    if extractor_name == "rule":
        return RuleBasedExtractor()
    if extractor_name == "mock-llm":
        return MockLLMExtractor()
    if extractor_name == "openai-compatible":
        return OpenAICompatibleExtractor()
    raise PipelineError(f"Unsupported extractor: {extractor_name}")


def classify_category(item: RawNewsItem) -> str:
    text = _combined_text(item)
    if any(keyword in text for keyword in ("model", "llm", "gpt", "claude", "gemini")):
        return "model"
    if "agent" in text:
        return "agent"
    if any(keyword in text for keyword in ("chip", "gpu", "nvidia")):
        return "infrastructure"
    return "application"


def semantic_category(item: RawNewsItem) -> str:
    text = _combined_text(item)
    if any(keyword in text for keyword in ("chip", "gpu", "nvidia", "infrastructure", "blackwell", "graviton")):
        return "infrastructure"
    if any(keyword in text for keyword in ("agent", "agentic", "codex", "sdk", "mcp", "workflow")):
        return "agent"
    if any(keyword in text for keyword in ("app", "android", "accessibility", "finance", "advertising", "application")):
        return "application"
    if any(keyword in text for keyword in ("model", "llm", "gpt", "claude", "gemini")):
        return "model"
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
