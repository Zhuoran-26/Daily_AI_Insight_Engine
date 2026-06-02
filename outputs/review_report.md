# AI Reviewer 复审报告

## 复审摘要

- 最终结论: reviewed_with_warnings
- 问题总数: 7
- 错误数: 0
- 警告数: 1
- 信息数: 6

## 问题列表

| 严重程度 | 区域 | 标题 | 建议动作 |
| --- | --- | --- | --- |
| info | schema | 没有失败评估项 | 继续保留当前 evaluation 路径中的 schema 与 harness 校验。 |
| warning | category | 检测到分类不一致项 | 复查不一致标题，并在合理时更新抽取规则、prompt 或 expected fixture 说明。 |
| info | grounding | 来源追溯全部通过 | 继续要求所有 extractor 模式保留 source 和 URL。 |
| info | confidence | 平均置信度达到阈值 | 继续在准确率之外展示置信度分布。 |
| info | category | Extractor 相比 baseline 有提升 | 可以在 showcase 中使用该对比，同时说明仍然存在的分类不一致项。 |
| info | report | 评估报告存在 | 将该报告作为人工可读的质量评估产物。 |
| info | report | 分析日报存在 | 在确认 evaluation 结果后，将该日报作为最终生成产物展示。 |


## 问题详情

### 没有失败评估项

- 严重程度: info
- 区域: schema
- 详情: 全部 13 条样本都生成了有效评估结果。
- 建议动作: 继续保留当前 evaluation 路径中的 schema 与 harness 校验。

### 检测到分类不一致项

- 严重程度: warning
- 区域: category
- 详情: 4 条成功样本的预测分类与 expected fixture 不一致。
- 建议动作: 复查不一致标题，并在合理时更新抽取规则、prompt 或 expected fixture 说明。

### 来源追溯全部通过

- 严重程度: info
- 区域: grounding
- 详情: 所有评估样本都通过了 source grounding 检查。
- 建议动作: 继续要求所有 extractor 模式保留 source 和 URL。

### 平均置信度达到阈值

- 严重程度: info
- 区域: confidence
- 详情: 平均置信度为 0.92，达到 0.70 阈值。
- 建议动作: 继续在准确率之外展示置信度分布。

### Extractor 相比 baseline 有提升

- 严重程度: info
- 区域: category
- 详情: openai-compatible 准确率为 0.69；rule baseline 准确率为 0.38；提升幅度为 0.31。
- 建议动作: 可以在 showcase 中使用该对比，同时说明仍然存在的分类不一致项。

### 评估报告存在

- 严重程度: info
- 区域: report
- 详情: 已找到 evaluation report：outputs/llm_evaluation_report.md。
- 建议动作: 将该报告作为人工可读的质量评估产物。

### 分析日报存在

- 严重程度: info
- 区域: report
- 详情: 已找到 daily report：outputs/daily_report.md。
- 建议动作: 在确认 evaluation 结果后，将该日报作为最终生成产物展示。

## 方法说明

这个 deterministic reviewer 是覆盖在 evaluation artifact 之上的复审层。它不替代 Harness 校验，也不调用 LLM。它的作用是暴露分类不一致、失败项、置信度风险、缺失产物和 baseline 对比信号，让后续 revise 有明确依据。