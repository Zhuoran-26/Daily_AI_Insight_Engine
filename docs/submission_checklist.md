# 笔试题要求验收清单

| 题目要求 | 项目实现 | 对应文件/命令 | 是否满足 |
|---|---|---|---|
| GitHub 提交 | 项目已整理为可提交仓库，包含代码、数据、文档、输出样例和演示入口。 | `git log --oneline` / GitHub 仓库 | 是 |
| 10-20 条 AI 信息输入 | 真实样例包含 13 条近期 AI 行业信息；mixed showcase 样例包含 16 条近期中英混合 AI 信息。 | `data/raw/real_ai_news_sample.json` / `data/raw/mixed_channel_ai_news_sample.json` | 是 |
| 原始数据字段 | 每条 raw item 保留 `title`、`summary`、`source`、`url`、`published_at`、`language`；mixed sample 额外保留 `source_channel`、`source_language`、`selection_reason`、`collected_at`、`canonical_topic`、`topic_role`。 | `data/raw/mixed_channel_ai_news_sample.json` | 是 |
| 多渠道数据设计 | mixed sample 直接对应笔试题“三、数据获取”的官方渠道、科技媒体、聚合平台、社交媒体/社区平台四类参考方向，每种渠道都包含英文和中文来源。 | `data/raw/mixed_channel_ai_news_sample.json` / `tests/test_mixed_sample_data.py` | 是 |
| 数据事件选择理由 | mixed sample 每条记录都有 `selection_reason`，说明其对趋势分析、舆情监测、风险预警或决策辅助的价值。 | `data/raw/mixed_channel_ai_news_sample.json` | 是 |
| 发布日期追溯 | mixed sample 每条记录都有 `published_at`，结构化事件也保留发布日期用于追溯。 | `data/raw/mixed_channel_ai_news_sample.json` / `src/daily_ai_insight/models.py` | 是 |
| 发布时间与采集时间区分 | `published_at` 表示来源内容发布时间，`collected_at` 表示样本采集或整理时间；社区源日期不把采集时间冒充为发布时间。 | `data/raw/mixed_channel_ai_news_sample.json` / `docs/data_source_notes.md` | 是 |
| 热点聚类与多源覆盖 | mixed sample 使用 `canonical_topic` 和 `topic_role` 标注同一热点的官方发布、媒体解读、聚合扩散和社区反馈，报告与 UI 展示多源覆盖。 | `src/daily_ai_insight/report.py` / `app.py` | 是 |
| 数据来源说明 | 说明 synthetic fixture 与 real-world sample 的用途、来源类型和防幻觉策略。 | `docs/data_source_notes.md` | 是 |
| Schema 设计 | 定义 `RawNewsItem`、`StructuredAIEvent`、`DailyInsightReport`、evaluation/reviewer schema；`StructuredAIEvent` 已增加业务化分析字段。 | `src/daily_ai_insight/models.py` / `docs/project_spec_v1.md` | 是 |
| 结构化抽取 | 支持 rule、mock-llm、openai-compatible 三种 extractor；rule 会 deterministic 生成中文业务分析字段。 | `src/daily_ai_insight/extractors.py` | 是 |
| 分析日报 | 从 validated structured events 生成中文 Markdown 日报，推荐最终展示输入为 mixed sample。 | `python3 -m daily_ai_insight.cli run --input data/raw/mixed_channel_ai_news_sample.json --extractor rule` | 是 |
| 热点聚类日报 section | 日报包含 `热点聚类与多源覆盖`，说明多源覆盖不是简单重复，并提示社区源仅用于反馈和舆情观察。 | `outputs/daily_report.md` / `src/daily_ai_insight/report.py` | 是 |
| Top 事件 | 日报展示按 importance score 排序的 `今日主要热点 Top 3–5`。 | `outputs/daily_report.md` | 是 |
| 深度解读 | 日报包含 `重点事件深度解读`，逐条展示背景、行业影响、趋势信号、行业机会、行业风险、决策提示、证据和来源。 | `outputs/daily_report.md` / `src/daily_ai_insight/report.py` | 是 |
| 趋势判断 | 日报包含业务化 `趋势判断` section，覆盖模型能力升级、Agent/workflow、云与基础设施、应用落地和社区反馈。 | `outputs/daily_report.md` / `src/daily_ai_insight/report.py` | 是 |
| 风险/机会提示 | 日报包含 `舆情监测与风险预警` 和 `机会提示`，只描述行业风险/行业机会。 | `outputs/daily_report.md` / `src/daily_ai_insight/report.py` | 是 |
| 可视化展示 | Streamlit UI 展示来源渠道 × 来源语言覆盖矩阵、事件发布时间线、分类分布、重要性 × 置信度散点图、影响领域分布、Rule vs LLM 评估对比，并说明每个图回答的问题。 | `streamlit run app.py` | 是 |
| 中文产品体验 | UI、CLI 可见输出、日报、Evaluation report 和 Reviewer report 面向中文用户；技术名可保留英文。 | `app.py` / `src/daily_ai_insight/report.py` / `src/daily_ai_insight/evaluate.py` / `src/daily_ai_insight/reviewer.py` | 是 |
| 跨语言输入输出 | 支持英文/中文新闻输入；保留原始标题、来源和 URL，同时将结构化摘要、趋势判断、风险机会和最终报告面向中文输出。 | `prompts/extraction_prompt.md` / `outputs/daily_report.md` | 是 |
| AI 使用说明 | 说明 LLM 不是直接生成最终报告，而是受 schema、harness、evaluation 和 reviewer 约束。 | `README.md` / `docs/ai_coding_showcase.md` | 是 |
| Prompt 设计 | extraction prompt 明确禁止编造 source/url，要求 JSON schema 输出。 | `prompts/extraction_prompt.md` | 是 |
| 错误处理与校验 | pipeline 对 schema、source、evidence、confidence、API key 缺失等情况 fail fast。 | `src/daily_ai_insight/harness.py` / `src/daily_ai_insight/llm_client.py` | 是 |
| Harness 防幻觉 | Harness 阻止 hallucinated source/url、ungrounded event、低置信度输出和不可控 loop。 | `src/daily_ai_insight/harness.py` | 是 |
| Evaluation Harness | 支持 category accuracy、grounding pass rate、average confidence、failed items 评估；mixed showcase 已保留 rule 与 LLM 两套评估产物。 | `src/daily_ai_insight/evaluate.py` / `outputs/mixed_llm_evaluation_report.md` | 是 |
| Reviewer | deterministic reviewer 检查 mismatch、failed items、confidence、grounding、baseline comparison。 | `src/daily_ai_insight/reviewer.py` / `outputs/review_report.md` | 是 |
| 测试 | 默认测试覆盖 pipeline、extractor、harness、LLM config、evaluation、reviewer、UI import。 | `python3 -m pytest` | 是 |
| Streamlit 产品 Demo | 提供本地可交互 UI，默认使用 mixed sample，支持数据来源追溯、业务化结构化事件表、中文 Harness checklist、多样化可视化、pipeline/evaluation/reviewer。 | `app.py` / `streamlit run app.py` | 是 |
| DeepSeek 可选真实 LLM 模式 | 支持 OpenAI-compatible DeepSeek API，默认不要求 API key；真实集成测试需显式开启。 | `.env.example` / `tests/test_llm_integration.py` | 是 |

## 跨语言与 Schema 稳定性说明

本项目面向中文产品体验设计，但支持英文/中文新闻输入。英文 source 不等于英文产品体验：产品输出层的 UI、日报、评估报告和复审报告面向中文用户；原始 `title`、`source`、`url` 保持来源原样，便于追溯。

Schema 层保持英文 key、英文 category enum 和固定 extractor name，是为了保证工程稳定、自动化测试和 Evaluation Harness 可复现。

mixed sample 中的 provenance 字段来自 raw input，不允许 LLM 编造或覆盖。`canonical_topic` 和 `topic_role` 同样来自 raw input，用于展示同一热点的多源覆盖和来源角色。行业风险/机会应服务 AI 行业趋势、舆情监测与业务决策，不应把系统置信度或测试风险误写成行业风险。

mixed sample 的来源设计与题目数据获取参考方向保持一致：官方渠道用于确认技术发布信息，科技媒体用于行业动态报道，聚合平台用于综合信息流和跨来源热度观察，社交媒体/社区用于舆论讨论热点。样本采用中英混合来源，例如 OpenAI、Anthropic、Tencent、ERNIE Blog、TechCrunch、IT之家、Hacker News、AIbase、Reddit 和 V2EX。

Phase 8.2 增加了 `background`、`industry_impact`、`trend_signal`、`industry_risk`、`industry_opportunity`、`decision_hint`、`llm_generated`、`requires_human_review`。这些字段用于把结构化事件转化为可读的中文业务解读。LLM 生成内容会显示人工复核提示；行业风险/机会必须围绕 AI 行业和业务决策，不得把系统可信度、LLM 幻觉、Schema/Harness 校验或人工复核需求写成行业风险。

Phase 8.3 将 Streamlit 默认输入切换为 mixed sample，并把 provenance、业务分析字段、Harness checklist 和多样化可视化放到产品展示层。UI 不修改底层 schema key、category enum 或 extractor 参数名；Evaluation 对 mixed sample 默认使用 `expected_mixed_sample_categories.json`，Reviewer 复审抽取与评估质量，不替代人工行业判断。

Phase 8.4 修复 Streamlit Altair chart 对内联数据缺少显式 encoding type 时的渲染异常，并新增热点聚类与多源覆盖展示。`published_at` 与 `collected_at` 在报告和文档中明确区分，Reddit 等社区源只作为舆情与反馈信号。

## 无 API Key 验收命令

```bash
python3 -m pip install -e .
python3 -m pytest
python3 -m daily_ai_insight.cli run --input data/raw/mixed_channel_ai_news_sample.json --extractor rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor rule --output-prefix rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/mixed_channel_ai_news_sample.json --expected data/eval/expected_mixed_sample_categories.json --extractor rule --output-prefix mixed_rule
python3 -m daily_ai_insight.cli review --evaluation outputs/mixed_llm_evaluation_summary.json --baseline outputs/mixed_rule_evaluation_summary.json
streamlit run app.py
```

## DeepSeek 可选验收命令

```bash
cp .env.example .env
# 编辑 .env，填入自己的 API key，不要提交 .env
python3 scripts/smoke_test_llm.py
RUN_LLM_INTEGRATION=1 python3 -m pytest tests/test_llm_integration.py
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor openai-compatible --output-prefix llm
```
