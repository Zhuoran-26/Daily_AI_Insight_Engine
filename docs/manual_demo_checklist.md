# 手动演示验收清单

用于验证轻量 Streamlit 产品 Demo 和 CLI 端到端流程，不需要生产部署。

## 不需要 API Key 的最终验收路径

```bash
python3 -m pip install -e .
python3 -m pytest
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor rule --output-prefix rule
python3 -m daily_ai_insight.cli review --evaluation outputs/llm_evaluation_summary.json --baseline outputs/rule_evaluation_summary.json
streamlit run app.py
```

这条路径验证 deterministic baseline、harnessed pipeline、evaluation、reviewer 和产品 Demo UI，不需要真实 API key。

## 使用 DeepSeek 的最终验收路径

```bash
cp .env.example .env
python3 scripts/smoke_test_llm.py
RUN_LLM_INTEGRATION=1 python3 -m pytest tests/test_llm_integration.py
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor openai-compatible --output-prefix llm
```

运行 DeepSeek 路径前，请先在本地编辑 `.env`。不要提交 `.env` 或任何真实 API key。

## 1. Install Dependencies

```bash
python3 -m pip install -e .
```

## 2. Run Streamlit

```bash
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

## 3. Select Input Data

In **Input Data**, choose:

```text
real_ai_news_sample.json
```

Confirm the UI reports a valid raw news item count.

## 4. Select Extractor

In **Extractor Mode**, choose:

```text
rule
```

This path does not require an API key.

## 5. Run Insight Pipeline

Click:

```text
Run Insight Pipeline
```

Check that the UI shows:

- total events
- category counts
- top events table
- structured events table
- harness summary
- daily report markdown

## 6. Verify Daily Report

Confirm the daily report section appears in the UI and that the generated artifact exists:

```text
outputs/daily_report.md
```

## 7. Run Evaluation

Click:

```text
Run Evaluation
```

Check that the UI shows:

- category accuracy
- grounding pass rate
- average confidence
- failed items
- mismatched items table

Evaluation currently uses:

```text
data/eval/expected_real_sample_categories.json
```

Custom uploaded data should not be evaluated unless a matching expected fixture is added.

## 8. Run Reviewer

Click:

```text
Run Reviewer
```

Check that the UI shows:

- final verdict
- error count
- warning count
- info count
- reviewer issue table
- review report markdown

The reviewer can use the current evaluation result or the saved showcase outputs.

## 9. Optional DeepSeek / OpenAI-compatible Demo

Create a local `.env` file:

```bash
cp .env.example .env
```

Edit `.env` locally:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
```

Do not commit `.env` or any real API key.

Then run smoke and integration checks:

```bash
python3 scripts/smoke_test_llm.py
RUN_LLM_INTEGRATION=1 python3 -m pytest tests/test_llm_integration.py
```

In Streamlit, choose:

```text
openai-compatible
```

Then rerun pipeline or evaluation. If the API key is missing, the UI should show a clear error and must not silently fall back to `rule`.
