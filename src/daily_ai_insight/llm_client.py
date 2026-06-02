"""OpenAI-compatible client for optional LLM extraction."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

from daily_ai_insight.errors import PipelineError
from daily_ai_insight.models import RawNewsItem


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

        return cls(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com").strip(),
            model=os.getenv("OPENAI_MODEL", "deepseek-v4-flash").strip(),
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

        client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        user_content = self._build_user_content(raw_items, feedback)
        try:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0,
            )
        except Exception as exc:
            raise PipelineError(f"OpenAI-compatible API request failed: {exc}") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content or not content.strip():
            raise PipelineError("OpenAI-compatible API returned empty content")
        return content.strip()

    @staticmethod
    def _build_user_content(raw_items: list[RawNewsItem], feedback: str | None) -> str:
        records = [
            {
                "title": item.title,
                "summary": item.summary,
                "source": item.source,
                "url": item.url,
                "published_at": item.published_at,
                "language": item.language,
            }
            for item in raw_items
        ]
        feedback_block = ""
        if feedback:
            feedback_block = (
                "\nPrevious output failed validation. Fix the output while using only "
                f"the same input records. Validation feedback: {feedback}\n"
            )

        return (
            "Extract one StructuredAIEvent for each RawNewsItem below. "
            "Return only JSON: an array of objects, no Markdown, no commentary."
            f"{feedback_block}\nRawNewsItem records:\n"
            f"{json.dumps(records, ensure_ascii=False, indent=2)}"
        )
