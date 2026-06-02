# 抽取器评估报告

## 评估摘要

- 抽取模式: rule
- 样本总数: 16
- 成功项: 16
- 失败项: 0
- 分类准确率: 0.50
- 来源追溯通过率: 1.00
- 平均置信度: 0.70

## 分类不一致项

| 标题 | 预期分类 | 预测分类 | 置信度 |
| --- | --- | --- | --- |
| OpenAI frontier models and Codex are now available on AWS | infrastructure | model | 0.70 |
| 腾讯面向全球市场推出全新AI工具及企业解决方案 | application | agent | 0.70 |
| Anthropic races toward a Wall Street debut with a confidential SEC filing | application | model | 0.70 |
| Anthropic releases Opus 4.8 with new ‘dynamic workflow’ tool | agent | model | 0.70 |
| GPT-5.5 and Codex are now GA on Amazon Bedrock | infrastructure | model | 0.70 |
| 重磅联手！OpenAI 尖端模型与 Codex 正式登陆 AWS，企业级 AI 落地再提速 | infrastructure | application | 0.70 |
| antigravity 变成了 codex 的模样， 3.5 更新 | agent | model | 0.70 |
| 求 codex、claude code 订阅账单每月$200 的，或者国内 coding 订阅，有偿 | application | model | 0.70 |


## 失败项

| 标题 | 预期分类 | 错误 |
| --- | --- | --- |


## 方法说明

Evaluation Harness 的目标不是追求 100% 准确率，而是暴露不同 extractor 的优势与局限。rule baseline 提供稳定可复现的 fallback，LLM extractor 用于处理更复杂的语义分类；无论哪种模式，Harness 都会在输出进入日报前阻止幻觉来源、无追溯事件和低置信度结果。