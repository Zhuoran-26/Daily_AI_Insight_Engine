from pathlib import Path

import pytest
from typer.testing import CliRunner

from daily_ai_insight.cli import app
from daily_ai_insight.errors import HarnessError, PipelineError
from daily_ai_insight.extractors import MockLLMExtractor, OpenAICompatibleExtractor, RuleBasedExtractor
from daily_ai_insight.normalize import load_raw_news
from daily_ai_insight.pipeline import run_pipeline

SAMPLE_PATH = Path("data/raw/sample_ai_news.json").resolve()
REAL_SAMPLE_PATH = Path("data/raw/real_ai_news_sample.json").resolve()


class FakeOpenAIClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete_extraction(self, prompt, raw_items, feedback=None):
        self.calls.append({"prompt": prompt, "feedback": feedback, "count": len(raw_items)})
        if len(self.calls) <= len(self.responses):
            return self.responses[len(self.calls) - 1]
        return self.responses[-1]


def llm_json_for(raw_items, *, source=None, url=None, confidence=0.82):
    import json

    events = []
    for index, item in enumerate(raw_items, start=1):
        events.append(
            {
                "id": f"llm-evt-{index:03d}",
                "title": item.title,
                "source": source or item.source,
                "url": url or item.url,
                "published_at": item.published_at,
                "language": item.language,
                "category": "application",
                "event_type": "application_update",
                "entities": [item.source],
                "impact_areas": ["productivity"],
                "importance_score": 5.0,
                "confidence": confidence,
                "summary": item.summary,
                "evidence": f"{item.source}: {item.summary}",
            }
        )
    return json.dumps(events)


def test_rule_based_extractor_generates_one_event_per_input():
    raw_items = load_raw_news(SAMPLE_PATH)
    events = RuleBasedExtractor().extract(raw_items)

    assert len(events) == len(raw_items)
    assert all(event.confidence == 0.7 for event in events)
    assert all(event.source for event in events)
    assert all(event.url for event in events)


def test_mock_llm_valid_mode_runs_through_pipeline(tmp_path):
    report = run_pipeline(
        REAL_SAMPLE_PATH,
        extractor=MockLLMExtractor(mode="valid"),
        events_output_path=tmp_path / "events.json",
        report_output_path=tmp_path / "report.md",
    )

    assert report.total_events == 13
    assert report.harness_summary["extractor_name"] == "mock-llm"
    assert report.harness_summary["schema_compliance_passed"] is True
    assert report.harness_summary["grounding_passed"] is True
    assert report.harness_summary["evidence_grounding_passed"] is True


def test_mock_llm_hallucinated_source_url_is_blocked(tmp_path):
    events_output_path = tmp_path / "events.json"
    report_output_path = tmp_path / "report.md"

    with pytest.raises(HarnessError, match="not grounded"):
        run_pipeline(
            REAL_SAMPLE_PATH,
            extractor=MockLLMExtractor(mode="hallucinated"),
            events_output_path=events_output_path,
            report_output_path=report_output_path,
        )

    assert not events_output_path.exists()
    assert not report_output_path.exists()


def test_mock_llm_low_confidence_is_blocked(tmp_path):
    with pytest.raises(HarnessError, match="below threshold"):
        run_pipeline(
            REAL_SAMPLE_PATH,
            extractor=MockLLMExtractor(mode="low-confidence"),
            events_output_path=tmp_path / "events.json",
            report_output_path=tmp_path / "report.md",
        )


def test_mock_llm_invalid_output_is_blocked_by_schema_harness(tmp_path):
    with pytest.raises(HarnessError, match="schema compliance"):
        run_pipeline(
            REAL_SAMPLE_PATH,
            extractor=MockLLMExtractor(mode="invalid"),
            events_output_path=tmp_path / "events.json",
            report_output_path=tmp_path / "report.md",
        )


def test_openai_compatible_without_api_key_fails_clearly(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    events_output_path = tmp_path / "events.json"
    report_output_path = tmp_path / "report.md"

    with pytest.raises(PipelineError, match="OPENAI_API_KEY"):
        run_pipeline(
            REAL_SAMPLE_PATH,
            extractor_name="openai-compatible",
            events_output_path=events_output_path,
            report_output_path=report_output_path,
        )

    assert not events_output_path.exists()
    assert not report_output_path.exists()


def test_openai_compatible_retries_after_json_parse_failure(tmp_path):
    raw_items = load_raw_news(SAMPLE_PATH)
    client = FakeOpenAIClient(["not json", llm_json_for(raw_items)])

    report = run_pipeline(
        SAMPLE_PATH,
        extractor=OpenAICompatibleExtractor(client=client, max_retries=1),
        events_output_path=tmp_path / "events.json",
        report_output_path=tmp_path / "report.md",
    )

    assert report.total_events == len(raw_items)
    assert len(client.calls) == 2
    assert "not valid JSON" in client.calls[1]["feedback"]


def test_openai_compatible_hallucinated_source_url_is_blocked(tmp_path):
    raw_items = load_raw_news(SAMPLE_PATH)
    client = FakeOpenAIClient(
        [
            llm_json_for(
                raw_items,
                source="Invented AI Wire",
                url="hallucinated://invented",
            )
        ]
    )

    with pytest.raises(PipelineError, match="not grounded"):
        run_pipeline(
            SAMPLE_PATH,
            extractor=OpenAICompatibleExtractor(client=client, max_retries=0),
            events_output_path=tmp_path / "events.json",
            report_output_path=tmp_path / "report.md",
        )


def test_openai_compatible_low_confidence_is_blocked(tmp_path):
    raw_items = load_raw_news(SAMPLE_PATH)
    client = FakeOpenAIClient([llm_json_for(raw_items, confidence=0.2)])

    with pytest.raises(PipelineError, match="below threshold"):
        run_pipeline(
            SAMPLE_PATH,
            extractor=OpenAICompatibleExtractor(client=client, max_retries=0),
            events_output_path=tmp_path / "events.json",
            report_output_path=tmp_path / "report.md",
        )


def test_cli_default_extractor_is_rule(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["run", "--input", str(SAMPLE_PATH)])

    assert result.exit_code == 0
    assert "Extractor: rule" in result.output


def test_cli_supports_mock_llm(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["run", "--input", str(REAL_SAMPLE_PATH), "--extractor", "mock-llm"],
    )

    assert result.exit_code == 0
    assert "Extractor: mock-llm" in result.output
