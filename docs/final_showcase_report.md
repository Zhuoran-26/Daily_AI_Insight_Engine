# Daily AI Insight Engine - 最终展示报告

## 项目做了什么

Daily AI Insight Engine 是一个面向 AI 行业信息分析的工程化 Demo。它把每日 AI 新闻、官方公告、科技媒体报道、聚合平台信息和社区讨论转化为可追溯、可校验、可评估的结构化洞察，并生成中文分析日报。

项目面向三类核心场景：

- AI 行业趋势分析
- 舆情监测与风险预警
- 信息快速理解与决策辅助

当前系统可以完成以下端到端流程：读取 curated raw news，将每条记录规范化为 `RawNewsItem`，通过所选 extractor 生成 `StructuredAIEvent`，经过 Schema validation、source grounding、evidence grounding 和 confidence gate，再生成日报、运行 Evaluation Harness，并交给 AI Reviewer 做复审。

最终展示推荐输入为：

```text
data/raw/mixed_channel_ai_news_sample.json
```

该样例包含 16 条中英混合、多渠道 AI 信息，覆盖官方渠道、科技媒体、聚合平台和社交/社区来源。

## 为什么这不是普通 Vibe Coding

普通 Vibe Coding 往往是把新闻交给 LLM，然后让模型直接写一篇看起来合理的总结。这个项目的重点不是“让 AI 写得像”，而是把 AI 输出放进一条可检查的工程链路里。

项目做了这些约束：

- 原始数据必须保留 `source`、`url`、`published_at` 等来源信息。
- 抽取结果必须符合 `StructuredAIEvent` Schema。
- 任何进入日报的事件都必须通过 Source Grounding 和 Evidence Grounding。
- 低置信度结果会被 Harness 拦截。
- LLM 输出不能修改原始 `title`、`source`、`url`、`published_at` 和 provenance 字段。
- Evaluation Harness 用 expected fixture 衡量 extractor 质量。
- AI Reviewer 复审的是抽取与评估质量，不替代人工行业判断。

因此，这个项目展示的是 Context Engineering、Harness Engineering、Structured Output、Evaluation Harness 和 AI Reviewer 如何共同约束一个 AI 辅助分析系统。

## 系统架构

整体流程如下：

```text
RawNewsItem
-> Extractor Strategy
-> Item-level LLM Extraction
-> Schema Validation
-> Harness Verification
-> Daily Report Generation
-> Evaluation Harness
-> AI Reviewer
```

其中：

- `rule` 是 deterministic Rule baseline，不需要 API key，适合离线演示和稳定回归。
- `mock-llm` 用来模拟 LLM 异常、低置信度和幻觉 source/url，验证 Harness 能否拦截。
- `openai-compatible` 支持 DeepSeek / OpenAI-compatible API，用于真实 LLM 抽取与对比评估。

生产 pipeline 保持 fail-fast。如果 Schema 校验、来源追溯、证据追溯或置信度检查失败，系统不会继续生成误导性的最终报告。

## 数据策略：中英混合、多渠道来源

最终展示数据是 `data/raw/mixed_channel_ai_news_sample.json`，共 16 条，采用中英混合、多渠道来源设计，直接对应笔试题中“数据获取”的参考方向。

四类 `source_channel`：

| source_channel | 中文说明 | 用途 |
|---|---|---|
| `official` | 官方渠道 | 确认技术发布事实、发布时间和产品范围。 |
| `tech_media` | 科技媒体 | 观察行业动态报道、竞争解读和外部叙事。 |
| `aggregator` | 聚合平台 | 发现跨来源热度和综合信息流，辅助快速理解。 |
| `social_media` | 社交/社区来源 | 捕捉用户反馈、开发者体验、成本敏感度和舆情风险。 |

mixed sample 每条记录都保留：

- `title`
- `summary`
- `source`
- `url`
- `published_at`
- `language`
- `source_channel`
- `source_language`
- `selection_reason`
- `collected_at`
- `canonical_topic`
- `topic_role`

其中，`published_at` 表示来源内容本身的发布时间，`collected_at` 表示样本采集或整理时间。二者不能混用，尤其是 Reddit、V2EX 等社区来源。社区/社交来源适合观察反馈和舆情，不作为事实主来源；事实确认仍优先依赖官方渠道和可追溯媒体报道。

## 热点聚类与多源覆盖

项目新增 `canonical_topic` 和 `topic_role` 来展示热点的多源覆盖关系。

这不是简单去重逻辑。相同热点出现在多个渠道，往往代表信息扩散链路：

- 官方渠道确认发布事实。
- 科技媒体给出行业报道和竞争视角。
- 聚合平台体现跨来源可见度。
- 社区/社交来源暴露用户反馈和舆论风险。

例如同一模型发布事件，可以同时有官方公告、TechCrunch 报道、中文聚合摘要和 Reddit 讨论。系统通过 `canonical_topic` 把它们归为同一热点，并通过 `topic_role` 标注每条记录在热点中的角色。这样既避免把重复热点误判为数据噪声，也能展示事件从发布到讨论的传播路径。

LLM 不允许生成或改写 `canonical_topic` 和 `topic_role`。这些字段来自 raw input，并在 extractor 中被复制到结构化事件。

## Rule Baseline vs DeepSeek V4 Flash

最终 mixed showcase 的本地评估结果如下：

| Extractor | Accuracy | Source Grounding | Avg Confidence | Failed Items |
|---|---:|---:|---:|---:|
| Rule baseline | 0.50 | 1.00 | 0.70 | 0 |
| DeepSeek V4 Flash | 0.88 | 1.00 | 0.89 | 0 |

这组结果说明：

- Rule baseline 稳定、可复现、无需 API key，但对复杂语义分类会偏粗糙。
- DeepSeek V4 Flash 在 mixed sample 上显著提升分类准确率。
- 两种模式的 Source Grounding pass rate 都是 `1.00`，说明质量提升没有以牺牲来源追溯为代价。
- 仍然存在少量 category mismatch，因此 LLM 输出应进入人工复核，而不是被包装成完全正确。

历史 real-world sample 的对照结果保留如下，作为早期 13 条真实样例的参考：

| Extractor | Accuracy | Source Grounding | Avg Confidence | Failed Items |
|---|---:|---:|---:|---:|
| Rule baseline | 0.38 | 1.00 | 0.70 | 0 |
| DeepSeek V4 Flash | 0.69 | 1.00 | 0.92 | 0 |

## Harness Engineering

Harness Engineering 是本项目的核心控制层。它的目标不是增加花哨功能，而是阻止不可信 AI 输出进入下游。

当前 Harness 覆盖：

- Schema validation：结构化事件必须符合 Pydantic Schema。
- Source Grounding：结构化事件的 `title`、`source`、`url` 等必须来自 raw input。
- Evidence Grounding：`evidence` 必须能追溯到原始 title 或 summary。
- Confidence gate：低于阈值的结果不能进入最终报告。
- Retry budget：Item-level LLM Extraction 有明确重试预算，避免不可控循环。
- Immutable provenance：LLM 不能修改来源、发布时间和 provenance 字段。

LLM 生成的背景、行业影响、趋势信号、行业风险、行业机会和决策提示，必须经过这些校验后才能进入报告。即使通过校验，报告仍提示建议人工复核。

## Evaluation Harness

Evaluation Harness 用 expected fixture 衡量 extractor 的质量，而不是只看报告“读起来是否顺”。

它会输出：

- category accuracy
- successful items
- failed items
- grounding pass rate
- average confidence
- mismatched items

对于最终 mixed sample，Evaluation Harness 使用：

```text
data/eval/expected_mixed_sample_categories.json
```

已保留的最终展示产物包括：

```text
outputs/mixed_rule_evaluation_summary.json
outputs/mixed_rule_evaluation_report.md
outputs/mixed_llm_evaluation_summary.json
outputs/mixed_llm_evaluation_report.md
```

Evaluation Harness 和 Harness Engineering 的职责不同：Harness 判断“这个输出是否安全到可以进入下游”，Evaluation 判断“这个 extractor 在样例上的质量如何”。

## AI Reviewer Workflow

AI Reviewer 当前采用 deterministic `RuleBasedReviewer`，用于复审 evaluation artifact。

它检查：

- category mismatch
- failed item
- grounding pass rate 是否低于 1.00
- average confidence 是否低于阈值
- LLM accuracy 是否明显高于 Rule baseline
- evaluation report 和 daily report 是否存在

最终 mixed showcase 的 reviewer 对比路径是：

```text
outputs/mixed_llm_evaluation_summary.json
outputs/mixed_rule_evaluation_summary.json
```

Reviewer 的作用是形成 critique-revise 工作流：先运行 evaluation，再复审结果，然后决定是否需要修订规则、prompt 或 expected fixture。Reviewer 不替代人工行业判断，尤其是涉及 LLM 生成的行业分析时，仍建议人工复核。

## Streamlit Product Demo

Streamlit Product Demo 是面试展示入口，启动方式：

```bash
streamlit run app.py
```

Demo 默认使用：

```text
mixed_channel_ai_news_sample.json
```

产品界面展示：

- 数据来源追溯：标题、来源、URL、发布日期、采集日期、来源渠道、来源语言、选择理由。
- 结构化洞察生成方式：`rule`、`mock-llm`、`openai-compatible`。
- 可视化日报：来源渠道 × 来源语言覆盖矩阵、事件发布时间线、分类分布、重要性 × 置信度散点图、影响领域分布。
- 热点聚类与多源覆盖：展示 `canonical_topic`、覆盖来源数量、渠道/语言覆盖、是否包含官方来源、是否包含社区反馈。
- 业务化结构化事件表：中文友好列，同时保留 raw JSON expander。
- Harness 校验摘要：默认展示中文 checklist，原始 JSON 放入 expander。
- Evaluation Harness：运行 mixed sample 的评估。
- AI Reviewer：复审抽取与评估质量。

这个 Demo 的价值在于，它不是单页摘要，而是把来源、结构化事件、校验、评估、复审和最终日报都放到同一条可解释链路中。

## 工程质量

项目体现了 test-backed AI engineering：

- 默认测试不调用真实 API。
- 真实 LLM integration test 必须显式设置环境变量。
- `.env` 和真实 API key 不提交。
- Rule baseline 保持 deterministic。
- mock LLM 覆盖幻觉 source/url、低置信度和 malformed output。
- OpenAI-compatible extractor 采用 Item-level LLM Extraction，降低 batch JSON 失败风险。
- Prompt、Schema、Harness、Evaluation 和 Reviewer 都有版本化文件。
- 最终报告来自可追溯的结构化中间产物。

当前默认测试结果：

```text
81 passed, 1 skipped
```

## 已知限制

- 当前 mixed sample 是手动整理的静态展示样例，不是实时舆情采集系统。
- Evidence Grounding 使用保守启发式，主要依赖 raw title 和 summary。
- `expected_mixed_sample_categories.json` 适合本次 16 条样例，不是完整 AI 事件分类本体。
- AI Reviewer 当前是 deterministic reviewer，还没有实现多轮自动 prompt repair。
- 社区/社交来源只能作为舆情和反馈信号，不能替代官方发布事实。

## 后续优化方向

- 接入 RSS、官方 API 或搜索 API，并保持 source allowlist。
- 增加 raw snapshot 存储，提升数据采集可复现性。
- 引入多日趋势追踪，展示热点随时间变化。
- 扩展可视化 dashboard，支持多日对比和风险趋势。
- 增加 reviewer-driven prompt refinement，形成更完整的 critique-revise 循环。
- 增加 CI workflow，自动运行默认测试、fixture 校验和文档产物检查。
