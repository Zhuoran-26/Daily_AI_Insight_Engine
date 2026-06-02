import subprocess

import pytest

from daily_ai_insight.errors import PipelineError
from daily_ai_insight.llm_client import OpenAICompatibleConfig


def test_env_example_uses_deepseek_v4_flash_default():
    text = open(".env.example", encoding="utf-8").read()

    assert "OPENAI_BASE_URL=https://api.deepseek.com" in text
    assert "OPENAI_MODEL=deepseek-v4-flash" in text
    assert "# OPENAI_MODEL=deepseek-v4-pro" in text
    assert "your_api_key_here" in text


def test_env_file_is_ignored_by_git():
    result = subprocess.run(
        ["git", "check-ignore", ".env"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0


def test_missing_api_key_fails_clearly(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")

    with pytest.raises(PipelineError, match="OPENAI_API_KEY"):
        OpenAICompatibleConfig.from_environment()


def test_missing_model_defaults_to_deepseek_v4_flash(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.setenv("OPENAI_MODEL", "")

    config = OpenAICompatibleConfig.from_environment()

    assert config.base_url == "https://api.deepseek.com"
    assert config.model == "deepseek-v4-flash"


def test_placeholder_model_fails(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "your_model_here")

    with pytest.raises(PipelineError, match="placeholder"):
        OpenAICompatibleConfig.from_environment()
