# 抽取器评估报告

## 评估摘要

- 抽取模式: openai-compatible
- 样本总数: 16
- 成功项: 16
- 失败项: 0
- 分类准确率: 0.88
- 来源追溯通过率: 1.00
- 平均置信度: 0.89

## 分类不一致项

| 标题 | 预期分类 | 预测分类 | 置信度 |
| --- | --- | --- | --- |
| Anthropic races toward a Wall Street debut with a confidential SEC filing | application | model | 0.95 |
| GPT-5.5 and Codex are now GA on Amazon Bedrock | infrastructure | model | 0.90 |


## 失败项

| 标题 | 预期分类 | 错误 |
| --- | --- | --- |


## 方法说明

Evaluation Harness 的目标不是追求 100% 准确率，而是暴露不同 extractor 的优势与局限。rule baseline 提供稳定可复现的 fallback，LLM extractor 用于处理更复杂的语义分类；无论哪种模式，Harness 都会在输出进入日报前阻止幻觉来源、无追溯事件和低置信度结果。