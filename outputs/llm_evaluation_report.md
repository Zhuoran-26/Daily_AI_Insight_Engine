# Extractor Evaluation Report

## Summary

- Extractor: openai-compatible
- Total items: 13
- Successful items: 13
- Failed items: 0
- Category accuracy: 0.69
- Grounding pass rate: 1.00
- Average confidence: 0.92

## Mismatched Items

| Title | Expected | Predicted | Confidence |
| --- | --- | --- | --- |
| OpenAI frontier models and Codex are now available on AWS | model | infrastructure | 0.95 |
| Anthropic acquires Stainless | agent | infrastructure | 0.95 |
| I/O 2026 developer highlights: Antigravity, Gemini API, AI Studio | agent | infrastructure | 0.80 |
| Introducing Muse Spark: Meta's Most Powerful Model Yet | application | model | 0.90 |


## Failed Items

| Title | Expected | Error |
| --- | --- | --- |


## Methodology Note

Evaluation is not intended to force 100 percent accuracy. It exposes the strengths and limits of each extractor. The rule baseline is a stable fallback, LLM extractors are intended for complex semantics, and the harness blocks hallucinated or ungrounded outputs before they become report inputs.