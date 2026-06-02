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
    def __init__(self, responses=None, default_response=None):
        self.responses = list(responses or [])
        self.default_response = default_response
        self.calls = []

    def complete_extraction(self, prompt, raw_items, feedback=None):
        self.calls.append(
            {
                "prompt": prompt,
                "feedback": feedback,
                "count": len(raw_items),
                "title": raw_items[0].title,
            }
        )
        if self.responses:
            response = self.responses.pop(0)
        else:
            response = self.default_response
        if callable(response):
            return response(raw_items[0])
        return response


def llm_json_for_item(raw_item, *, title=None, source=None, url=None, confidence=0.82):
    import json

    return json.dumps(
        {
            "id": "llm-suggested-id",
            "title": title or raw_item.title,
            "source": source or raw_item.source,
            "url": url or raw_item.url,
            "published_at": raw_item.published_at,
            "language": raw_item.language,
            "category": "application",
            "event_type": "application_update",
            "entities": [raw_item.source],
            "impact_areas": ["productivity"],
            "importance_score": 5.0,
            "confidence": confidence,
            "summary": raw_item.summary,
            "evidence": f"{raw_item.source}: {raw_item.summary}",
        }
    )


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
    monkeypatch.setenv("OPENAI_API_KEY", "")
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


def test_openai_compatible_calls_llm_once_per_raw_item(tmp_path):
    raw_items = load_raw_news(SAMPLE_PATH)
    client = FakeOpenAIClient(default_response=llm_json_for_item)

    report = run_pipeline(
        SAMPLE_PATH,
        extractor=OpenAICompatibleExtractor(client=client, max_retries=0),
        events_output_path=tmp_path / "events.json",
        report_output_path=tmp_path / "report.md",
    )

    assert report.total_events == len(raw_items)
    assert len(client.calls) == len(raw_items)
    assert all(call["count"] == 1 for call in client.calls)
    assert [call["title"] for call in client.calls] == [item.title for item in raw_items]


def test_openai_compatible_retries_after_json_parse_failure(tmp_path):
    raw_items = load_raw_news(SAMPLE_PATH)
    client = FakeOpenAIClient(["not json"], default_response=llm_json_for_item)

    report = run_pipeline(
        SAMPLE_PATH,
        extractor=OpenAICompatibleExtractor(client=client, max_retries=1),
        events_output_path=tmp_path / "events.json",
        report_output_path=tmp_path / "report.md",
    )

    assert report.total_events == len(raw_items)
    assert len(client.calls) == len(raw_items) + 1
    assert "not valid JSON" in client.calls[1]["feedback"]
    assert client.calls[0]["title"] == raw_items[0].title
    assert client.calls[1]["title"] == raw_items[0].title
    assert client.calls[2]["title"] == raw_items[1].title


def test_openai_compatible_overrides_hallucinated_immutable_fields(tmp_path):
    raw_items = load_raw_news(SAMPLE_PATH)
    client = FakeOpenAIClient(
        default_response=lambda item: llm_json_for_item(
            item,
            title="Invented title",
            source="Invented AI Wire",
            url="hallucinated://invented",
        )
    )

    report = run_pipeline(
        SAMPLE_PATH,
        extractor=OpenAICompatibleExtractor(client=client, max_retries=0),
        events_output_path=tmp_path / "events.json",
        report_output_path=tmp_path / "report.md",
    )

    assert report.top_events
    assert all(event.source in {item.source for item in raw_items} for event in report.top_events)
    assert all(event.url in {item.url for item in raw_items} for event in report.top_events)
    assert all(event.title in {item.title for item in raw_items} for event in report.top_events)


def test_openai_compatible_low_confidence_is_blocked(tmp_path):
    raw_items = load_raw_news(SAMPLE_PATH)
    client = FakeOpenAIClient(default_response=lambda item: llm_json_for_item(item, confidence=0.2))

    with pytest.raises(PipelineError, match="below threshold"):
        run_pipeline(
            SAMPLE_PATH,
            extractor=OpenAICompatibleExtractor(client=client, max_retries=0),
            events_output_path=tmp_path / "events.json",
            report_output_path=tmp_path / "report.md",
        )


def test_openai_compatible_failed_item_error_includes_index_and_title(tmp_path):
    raw_items = load_raw_news(SAMPLE_PATH)
    client = FakeOpenAIClient(
        [
            llm_json_for_item(raw_items[0]),
            "not json",
            "still not json",
        ],
        default_response=llm_json_for_item,
    )

    with pytest.raises(PipelineError) as exc_info:
        run_pipeline(
            SAMPLE_PATH,
            extractor=OpenAICompatibleExtractor(client=client, max_retries=1),
            events_output_path=tmp_path / "events.json",
            report_output_path=tmp_path / "report.md",
        )

    message = str(exc_info.value)
    assert "item 2" in message
    assert raw_items[1].title in message


def test_cli_default_extractor_is_rule(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["run", "--input", str(SAMPLE_PATH)])

    assert result.exit_code == 0
    assert "抽取模式：rule" in result.output


def test_cli_supports_mock_llm(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["run", "--input", str(REAL_SAMPLE_PATH), "--extractor", "mock-llm"],
    )

    assert result.exit_code == 0
    assert "抽取模式：mock-llm" in result.output
