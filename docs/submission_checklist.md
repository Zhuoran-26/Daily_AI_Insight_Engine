# 笔试题要求验收清单

| 题目要求 | 项目实现 | 对应文件/命令 | 是否满足 |
|---|---|---|---|
| GitHub 提交 | 项目已整理为可提交仓库，包含代码、数据、文档、输出样例和演示入口。 | `git log --oneline` / GitHub 仓库 | 是 |
| 10-20 条 AI 信息输入 | 真实样例包含 13 条近期 AI 行业信息；mixed showcase 样例包含 16 条近期中英混合 AI 信息。 | `data/raw/real_ai_news_sample.json` / `data/raw/mixed_channel_ai_news_sample.json` | 是 |
| 原始数据字段 | 每条 raw item 保留 `title`、`summary`、`source`、`url`、`published_at`、`language`；mixed sample 额外保留 `source_channel`、`source_language`、`selection_reason`、`collected_at`。 | `data/raw/mixed_channel_ai_news_sample.json` | 是 |
| 多渠道数据设计 | mixed sample 覆盖官方渠道、科技媒体、聚合平台、社交媒体/社区平台，每种渠道都包含英文和中文来源。 | `data/raw/mixed_channel_ai_news_sample.json` / `tests/test_mixed_sample_data.py` | 是 |
| 数据事件选择理由 | mixed sample 每条记录都有 `selection_reason`，说明其对趋势分析、舆情监测、风险预警或决策辅助的价值。 | `data/raw/mixed_channel_ai_news_sample.json` | 是 |
| 发布日期追溯 | mixed sample 每条记录都有 `published_at`，结构化事件也保留发布日期用于追溯。 | `data/raw/mixed_channel_ai_news_sample.json` / `src/daily_ai_insight/models.py` | 是 |
| 数据来源说明 | 说明 synthetic fixture 与 real-world sample 的用途、来源类型和防幻觉策略。 | `docs/data_source_notes.md` | 是 |
| Schema 设计 | 定义 `RawNewsItem`、`StructuredAIEvent`、`DailyInsightReport`、evaluation/reviewer schema。 | `src/daily_ai_insight/models.py` / `docs/project_spec_v1.md` | 是 |
| 结构化抽取 | 支持 rule、mock-llm、openai-compatible 三种 extractor。 | `src/daily_ai_insight/extractors.py` | 是 |
| 分析日报 | 从 validated structured events 生成 Markdown 日报。 | `python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor rule` | 是 |
| Top 事件 | 日报展示按 importance score 排序的 Top Events。 | `outputs/daily_report.md` | 是 |
| 趋势判断 | 日报包含 deterministic `Trend Signals` section。 | `outputs/daily_report.md` / `src/daily_ai_insight/report.py` | 是 |
| 风险/机会提示 | 日报包含 `Risks and Opportunities` section。 | `outputs/daily_report.md` / `src/daily_ai_insight/report.py` | 是 |
| 可视化展示 | Streamlit UI 展示 category distribution、top event importance、rule vs LLM accuracy 图表。 | `streamlit run app.py` | 是 |
| 中文产品体验 | UI、CLI 可见输出、日报、Evaluation report 和 Reviewer report 面向中文用户；技术名可保留英文。 | `app.py` / `src/daily_ai_insight/report.py` / `src/daily_ai_insight/evaluate.py` / `src/daily_ai_insight/reviewer.py` | 是 |
| 跨语言输入输出 | 支持英文/中文新闻输入；保留原始标题、来源和 URL，同时将结构化摘要、趋势判断、风险机会和最终报告面向中文输出。 | `prompts/extraction_prompt.md` / `outputs/daily_report.md` | 是 |
| AI 使用说明 | 说明 LLM 不是直接生成最终报告，而是受 schema、harness、evaluation 和 reviewer 约束。 | `README.md` / `docs/ai_coding_showcase.md` | 是 |
| Prompt 设计 | extraction prompt 明确禁止编造 source/url，要求 JSON schema 输出。 | `prompts/extraction_prompt.md` | 是 |
| 错误处理与校验 | pipeline 对 schema、source、evidence、confidence、API key 缺失等情况 fail fast。 | `src/daily_ai_insight/harness.py` / `src/daily_ai_insight/llm_client.py` | 是 |
| Harness 防幻觉 | Harness 阻止 hallucinated source/url、ungrounded event、低置信度输出和不可控 loop。 | `src/daily_ai_insight/harness.py` | 是 |
| Evaluation Harness | 支持 category accuracy、grounding pass rate、average confidence、failed items 评估。 | `src/daily_ai_insight/evaluate.py` / `outputs/llm_evaluation_report.md` | 是 |
| Reviewer | deterministic reviewer 检查 mismatch、failed items、confidence、grounding、baseline comparison。 | `src/daily_ai_insight/reviewer.py` / `outputs/review_report.md` | 是 |
| 测试 | 默认测试覆盖 pipeline、extractor、harness、LLM config、evaluation、reviewer、UI import。 | `python3 -m pytest` | 是 |
| Streamlit 产品 Demo | 提供本地可交互 UI，支持选择数据、extractor、运行 pipeline/evaluation/reviewer。 | `app.py` / `streamlit run app.py` | 是 |
| DeepSeek 可选真实 LLM 模式 | 支持 OpenAI-compatible DeepSeek API，默认不要求 API key；真实集成测试需显式开启。 | `.env.example` / `tests/test_llm_integration.py` | 是 |

## 跨语言与 Schema 稳定性说明

本项目面向中文产品体验设计，但支持英文/中文新闻输入。英文 source 不等于英文产品体验：产品输出层的 UI、日报、评估报告和复审报告面向中文用户；原始 `title`、`source`、`url` 保持来源原样，便于追溯。

Schema 层保持英文 key、英文 category enum 和固定 extractor name，是为了保证工程稳定、自动化测试和 Evaluation Harness 可复现。

mixed sample 中的 provenance 字段来自 raw input，不允许 LLM 编造或覆盖。行业风险/机会应服务 AI 行业趋势、舆情监测与业务决策，不应把系统置信度或测试风险误写成行业风险。

## 无 API Key 验收命令

```bash
python3 -m pip install -e .
python3 -m pytest
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor rule --output-prefix rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/mixed_channel_ai_news_sample.json --expected data/eval/expected_mixed_sample_categories.json --extractor rule --output-prefix mixed_rule
python3 -m daily_ai_insight.cli review --evaluation outputs/llm_evaluation_summary.json --baseline outputs/rule_evaluation_summary.json
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
