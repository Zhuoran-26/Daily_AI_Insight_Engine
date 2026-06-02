# Daily AI Insight Engine

Daily AI Insight Engine turns daily AI-related news into structured events, validates those events with harness checks, and generates a traceable daily report.

This repository is being built for an AI application interview task. The goal is not only to produce a report, but to show a disciplined AI engineering workflow: context engineering, structured output, harness engineering, self verification, and test-backed development.

## Why This Is Not Vibe Coding

Ordinary vibe coding would paste raw news into an AI model and submit a report if it looked plausible. This project keeps the pipeline inspectable:

- raw news keeps source and URL metadata
- structured events must preserve source grounding
- generated reports are built from validated events
- low-confidence or ungrounded records fail fast
- every implementation phase has automated tests

## Harness Engineering

The `PipelineHarness` is a control layer around the pipeline. It prevents:

- hallucinated sources by rejecting fake or generated URLs
- ungrounded events by requiring every event to match a raw source/title/URL
- infinite loops by enforcing a processing step budget
- unverifiable output by requiring schema validation and confidence checks
- low-confidence results from directly entering the final report

The current MVP is deterministic. Future LLM or Agent stages must pass through the same harness before their outputs can be used downstream.

## Current Baseline

The default mode is a deterministic rule baseline:

1. Load synthetic sample AI news from `data/raw/sample_ai_news.json`.
2. Normalize raw records into `RawNewsItem`.
3. Validate raw source fields.
4. Convert records into `StructuredAIEvent` with the selected extractor.
5. Run schema validation plus harness grounding, evidence, confidence, and loop-budget checks.
6. Generate `data/processed/structured_events.json`.
7. Generate `outputs/daily_report.md`.

The sample data is synthetic for reproducible testing. URLs point to trusted public homepages or official source hubs, not invented article URLs.

## Data Strategy

The project uses two local raw-data fixtures:

- `data/raw/sample_ai_news.json`: synthetic fixture for stable, repeatable tests.
- `data/raw/real_ai_news_sample.json`: real-world sample for interview demonstration and qualitative review.

The synthetic fixture is intentionally controlled so schema, harness, and report behavior can be tested without depending on live websites. The real-world sample shows that the same pipeline can process traceable public AI news and announcements.

All real sample records must retain `source` and `url`. The harness blocks missing, suspicious, or hallucinated source URLs and requires each structured event to stay grounded in the raw input record that produced it.

## Install

```bash
python -m pip install -e .
```

If your shell does not provide `python`, use `python3` for the commands below.

## Run Tests

```bash
python -m pytest
```

## Run Pipeline

```bash
python -m daily_ai_insight.cli run --input data/raw/sample_ai_news.json --extractor rule
```

Equivalent `python3` command:

```bash
python3 -m daily_ai_insight.cli run --input data/raw/sample_ai_news.json --extractor rule
```

Generated files:

- `data/processed/structured_events.json`
- `outputs/daily_report.md`

## Running with Real-world Sample

```bash
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor rule
```

This uses the same deterministic baseline and writes the same output paths:

- `data/processed/structured_events.json`
- `outputs/daily_report.md`

## Extractor Modes

The pipeline supports three extractor modes:

- `rule`: default deterministic baseline. It is fully local, reproducible, and does not call an LLM.
- `mock-llm`: local test double for LLM workflow. It simulates semantic extraction and unsafe LLM behavior in tests without calling an API.
- `openai-compatible`: real OpenAI-compatible LLM extractor. It reads `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, and optional `OPENAI_MODEL`.

Run the real-world sample with mock LLM workflow:

```bash
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor mock-llm
```

Run the optional OpenAI-compatible interface:

```bash
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor openai-compatible
```

If `OPENAI_API_KEY` is missing, `openai-compatible` fails clearly and does not generate a misleading report. The OpenAI SDK is installed for this mode, but `rule` and `mock-llm` do not require API access.

## Using DeepSeek / OpenAI-compatible LLM

The default reproducible mode is still `rule`. The `openai-compatible` mode is an optional real LLM enhancement path and requires a local API key.

Create a local environment file:

```bash
cp .env.example .env
# then edit .env and replace OPENAI_API_KEY with your local key
```

Default suggested values:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
# For stronger reasoning, you can use:
# OPENAI_MODEL=deepseek-v4-pro
```

`deepseek-v4-flash` is the default recommended model for this project. If you need stronger reasoning, change `OPENAI_MODEL` to `deepseek-v4-pro`. Keep the API key only in `.env`; `.env` is ignored by git.

Run with the real LLM extractor:

```bash
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor openai-compatible
```

The `.env` file is ignored by git. Do not commit real API keys.

LLM output is not trusted directly. The extractor retries invalid output up to two times, then fails without falling back to `rule`. Every LLM result must pass JSON parsing, Pydantic schema validation, `validate_structured_events`, source grounding, evidence grounding, and confidence checks before a report is written.

To manually run the real integration test:

```bash
RUN_LLM_INTEGRATION=1 python3 -m pytest tests/test_llm_integration.py
```

Without `RUN_LLM_INTEGRATION=1` and `OPENAI_API_KEY`, the integration test is skipped and the rest of the project remains fully testable.

Recommended LLM verification order:

```bash
python3 scripts/smoke_test_llm.py
RUN_LLM_INTEGRATION=1 python3 -m pytest tests/test_llm_integration.py
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor openai-compatible
```

## Item-Level LLM Extraction

The OpenAI-compatible extractor processes one `RawNewsItem` at a time. For each item it calls the LLM, parses one JSON object, validates one `StructuredAIEvent`, applies single-item source/evidence grounding, checks confidence, and retries only that item up to two times.

The LLM can suggest category, event type, entities, impact areas, importance, confidence, summary, and evidence. The system forces `title`, `source`, `url`, `published_at`, `language`, and `id` from the raw input, so the model cannot rewrite source metadata.

This design reduces batch-level JSON failures, makes retry scope smaller, and makes errors easier to locate because failures include item index and title.

## Evaluation Harness

Run extractor evaluation against the real-world sample and expected category fixture:

```bash
python3 -m daily_ai_insight.cli evaluate \
  --input data/raw/real_ai_news_sample.json \
  --expected data/eval/expected_real_sample_categories.json \
  --extractor rule
```

You can compare extractors:

```bash
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor mock-llm
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor openai-compatible
```

The `rule` and `mock-llm` evaluations do not need an API key. The `openai-compatible` evaluation needs `.env` configuration.

Evaluation outputs:

- `outputs/evaluation_summary.json`
- `outputs/evaluation_report.md`

The evaluation harness measures category accuracy, valid output count, failed items, grounding pass rate, and confidence distribution. It is separate from the production pipeline: evaluation records item-level failures for analysis, while the pipeline remains fail-fast to avoid misleading reports.

## Why Rule Baseline Is Not the Final Intelligence Layer

The rule extractor is valuable because it is deterministic, cheap, testable, and useful as a fallback. It is not expected to solve complex semantic classification. For example, application or agent news that mentions `GPT`, `Claude`, or `Gemini` may be over-classified as `model`.

Complex semantic extraction should move to an LLM extractor, but only behind mandatory verification:

- Pydantic schema validation
- source grounding against `RawNewsItem`
- evidence grounding against title or summary
- confidence threshold checks
- item-level retry budgets
- deterministic fallback behavior
- automated tests for hallucinated sources and low confidence

## Future LLM/Agent Extension Points

The deterministic extractor can be supplemented by the real OpenAI-compatible extractor, but only behind these controls:

- Pydantic schema validation
- source grounding against `RawNewsItem`
- confidence threshold checks
- loop and retry budgets
- deterministic fallback behavior
- AI reviewer and human review queue

No future model output should enter the final report unless it passes these checks.
