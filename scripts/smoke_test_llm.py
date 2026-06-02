"""Smoke-test the configured OpenAI-compatible LLM endpoint."""

from __future__ import annotations

from dotenv import load_dotenv

from daily_ai_insight.errors import PipelineError
from daily_ai_insight.llm_client import OpenAICompatibleClient, OpenAICompatibleConfig


def main() -> int:
    load_dotenv()
    try:
        config = OpenAICompatibleConfig.from_environment()
    except PipelineError as exc:
        print(f"Configuration error: {exc}")
        print("To configure a local key:")
        print("  cp .env.example .env")
        print("  # then edit .env")
        return 1

    print(f"base_url: {config.base_url}")
    print(f"model: {config.model}")
    try:
        client = OpenAICompatibleClient(config)
        response = client.complete_text(
            system_prompt="You are a minimal connectivity smoke test.",
            user_prompt="Return the word ok.",
        )
    except PipelineError as exc:
        print("request_success: False")
        print(f"error: {exc}")
        return 1

    print("request_success: True")
    print(f"response_preview: {response[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
