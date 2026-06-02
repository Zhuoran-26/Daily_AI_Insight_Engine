"""OpenAI-compatible client for optional LLM extraction."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

from daily_ai_insight.errors import PipelineError
from daily_ai_insight.models import RawNewsItem

PLACEHOLDER_MODELS = {
    "your_model_here",
    "your-model-here",
    "your_model",
    "your-model",
    "model_name",
    "replace_me",
}


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    api_key: str
    base_url: str
    model: str

    @classmethod
    def from_environment(cls) -> "OpenAICompatibleConfig":
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise PipelineError(
                "openai-compatible extractor requires OPENAI_API_KEY. "
                "Use --extractor rule or --extractor mock-llm to run without an API key."
            )

        model = os.getenv("OPENAI_MODEL", "deepseek-v4-flash").strip() or "deepseek-v4-flash"
        if model.lower() in PLACEHOLDER_MODELS:
            raise PipelineError(
                "OPENAI_MODEL still looks like a placeholder. Use deepseek-v4-flash "
                "or another real OpenAI-compatible model name."
            )

        base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com").strip()
        base_url = base_url or "https://api.deepseek.com"

        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
        )


class OpenAICompatibleClient:
    """Small OpenAI-compatible chat client.

    The client only transports prompts and raw input. Parsing, schema validation,
    grounding, confidence checks, and retry decisions stay in the extractor and
    pipeline harness.
    """

    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config

    @classmethod
    def from_environment(cls) -> "OpenAICompatibleClient":
        return cls(OpenAICompatibleConfig.from_environment())

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        if not system_prompt.strip():
            raise PipelineError("OpenAI-compatible system prompt is empty")
        if not user_prompt.strip():
            raise PipelineError("OpenAI-compatible user prompt is empty")

        client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        try:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
        except Exception as exc:
            raise PipelineError(f"OpenAI-compatible API request failed: {exc}") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content or not content.strip():
            raise PipelineError("OpenAI-compatible API returned empty content")
        return content.strip()

    def complete_extraction(
        self,
        prompt: str,
        raw_items: list[RawNewsItem],
        feedback: str | None = None,
    ) -> str:
        if not prompt.strip():
            raise PipelineError("OpenAI-compatible extractor prompt is empty")
        if not raw_items:
            raise PipelineError("OpenAI-compatible extractor received no raw items")
        if len(raw_items) != 1:
            raise PipelineError("OpenAI-compatible item-level extraction expects exactly one raw item")

        user_content = self._build_user_content(raw_items, feedback)
        return self.complete_text(prompt, user_content)

    @staticmethod
    def _build_user_content(raw_items: list[RawNewsItem], feedback: str | None) -> str:
        item = raw_items[0]
        record = {
            "title": item.title,
            "summary": item.summary,
            "source": item.source,
            "url": item.url,
            "published_at": item.published_at,
            "language": item.language,
            "source_channel": item.source_channel,
            "source_language": item.source_language,
            "selection_reason": item.selection_reason,
            "collected_at": item.collected_at,
            "canonical_topic": item.canonical_topic,
            "topic_role": item.topic_role,
        }
        feedback_block = ""
        if feedback:
            feedback_block = (
                "\nPrevious output failed validation. Fix the output while using only "
                f"the same input records. Validation feedback: {feedback}\n"
            )

        return (
            "Extract one StructuredAIEvent suggestion for the single RawNewsItem below. "
            "Return only JSON: one object, no list, no Markdown, no commentary. "
            "Do not change immutable source fields."
            f"{feedback_block}\nRawNewsItem records:\n"
            f"{json.dumps(record, ensure_ascii=False, indent=2)}"
        )
