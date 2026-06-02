# 抽取器评估报告

## 评估摘要

- 抽取模式: rule
- 样本总数: 13
- 成功项: 13
- 失败项: 0
- 分类准确率: 0.38
- 来源追溯通过率: 1.00
- 平均置信度: 0.70

## 分类不一致项

| 标题 | 预期分类 | 预测分类 | 置信度 |
| --- | --- | --- | --- |
| A new personal finance experience in ChatGPT | application | model | 0.70 |
| Anthropic acquires Stainless | agent | model | 0.70 |
| PwC is deploying Claude to build technology, execute deals, and reinvent enterprise functions for clients | application | model | 0.70 |
| The Gemini app becomes more agentic, delivering proactive, 24/7 help | agent | model | 0.70 |
| I/O 2026 developer highlights: Antigravity, Gemini API, AI Studio | agent | model | 0.70 |
| Gemini Intelligence brings proactive AI to Android | application | model | 0.70 |
| Introducing Muse Spark: Meta's Most Powerful Model Yet | application | model | 0.70 |
| Meta partners with AWS on Graviton chips to power agentic AI | infrastructure | agent | 0.70 |


## 失败项

| 标题 | 预期分类 | 错误 |
| --- | --- | --- |


## 方法说明

Evaluation Harness 的目标不是追求 100% 准确率，而是暴露不同 extractor 的优势与局限。rule baseline 提供稳定可复现的 fallback，LLM extractor 用于处理更复杂的语义分类；无论哪种模式，Harness 都会在输出进入日报前阻止幻觉来源、无追溯事件和低置信度结果。