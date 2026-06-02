# Extractor Evaluation Report

## Summary

- Extractor: rule
- Total items: 13
- Successful items: 13
- Failed items: 0
- Category accuracy: 0.38
- Grounding pass rate: 1.00
- Average confidence: 0.70

## Mismatched Items

| Title | Expected | Predicted | Confidence |
| --- | --- | --- | --- |
| A new personal finance experience in ChatGPT | application | model | 0.70 |
| Anthropic acquires Stainless | agent | model | 0.70 |
| PwC is deploying Claude to build technology, execute deals, and reinvent enterprise functions for clients | application | model | 0.70 |
| The Gemini app becomes more agentic, delivering proactive, 24/7 help | agent | model | 0.70 |
| I/O 2026 developer highlights: Antigravity, Gemini API, AI Studio | agent | model | 0.70 |
| Gemini Intelligence brings proactive AI to Android | application | model | 0.70 |
| Introducing Muse Spark: Meta's Most Powerful Model Yet | application | model | 0.70 |
| Meta partners with AWS on Graviton chips to power agentic AI | infrastructure | agent | 0.70 |


## Failed Items

| Title | Expected | Error |
| --- | --- | --- |


## Methodology Note

Evaluation is not intended to force 100 percent accuracy. It exposes the strengths and limits of each extractor. The rule baseline is a stable fallback, LLM extractors are intended for complex semantics, and the harness blocks hallucinated or ungrounded outputs before they become report inputs.