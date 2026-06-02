# Manual Demo Checklist

Use this checklist to verify the lightweight Streamlit product demo without requiring a production deployment.

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
