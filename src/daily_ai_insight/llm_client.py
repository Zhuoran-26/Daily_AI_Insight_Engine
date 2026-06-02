"""OpenAI-compatible client placeholder for optional LLM extraction."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from daily_ai_insight.errors import PipelineError
from daily_ai_insight.models import RawNewsItem


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    api_key: str
    base_url: str
    model: str

    @classmethod
    def from_environment(cls) -> "OpenAICompatibleConfig":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise PipelineError(
                "openai-compatible extractor requires OPENAI_API_KEY. "
                "Use --extractor rule or --extractor mock-llm to run without an API key."
            )

        return cls(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip(),
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        )


class OpenAICompatibleClient:
    """Minimal adapter boundary without an SDK dependency.

    Phase 4 only establishes where a real OpenAI-compatible call would happen.
    The actual network call is intentionally not implemented, so the project
    remains runnable and testable without API credentials or paid services.
    """

    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config

    @classmethod
    def from_environment(cls) -> "OpenAICompatibleClient":
        return cls(OpenAICompatibleConfig.from_environment())

    def extract_events(self, prompt: str, raw_items: list[RawNewsItem]) -> list[dict[str, Any]]:
        if not prompt.strip():
            raise PipelineError("OpenAI-compatible extractor prompt is empty")
        if not raw_items:
            raise PipelineError("OpenAI-compatible extractor received no raw items")

        raise PipelineError(
            "openai-compatible extractor is configured but no real network adapter is "
            "implemented in Phase 4. Add an OpenAI-compatible adapter only behind "
            "schema validation, source grounding, confidence checks, and tests."
        )
