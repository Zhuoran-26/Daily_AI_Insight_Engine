# Daily AI Insight Engine

AI 行业信息结构化分析与日报生成系统。

这个项目不是把新闻丢给模型后直接生成一篇看起来合理的报告，而是一个工程化 AI Coding / Agentic Engineering 项目：从真实来源数据、结构化抽取、Schema 校验、Harness 约束、质量评估、AI Reviewer 复审，到最终日报输出，形成一条可运行、可测试、可解释的端到端链路。

## 推荐查看顺序

1. [`docs/final_showcase_report.md`](docs/final_showcase_report.md)
   项目最终亮点、架构、Rule baseline 与 DeepSeek V4 Flash 的真实对比结果。
2. [`docs/ai_coding_showcase.md`](docs/ai_coding_showcase.md)
   展示 Context Engineering、Harness Engineering、Structured Output、Self Verification 等 AI Coding 方法论。
3. [`outputs/llm_evaluation_report.md`](outputs/llm_evaluation_report.md)
   展示 DeepSeek V4 Flash 与 rule baseline 的结构化抽取评估结果。
4. [`outputs/review_report.md`](outputs/review_report.md)
   展示 AI Reviewer 对评估结果的复审、问题识别和 critique-revise 建议。
5. [`outputs/daily_report.md`](outputs/daily_report.md)
   展示最终生成的 AI 行业日报。

## 核心方法论

本项目重点展示以下 AI Engineering 能力：

- **Context Engineering**：用 `AGENTS.md`、项目规格文档、技能说明、prompt 和 fixture 管理上下文，而不是靠一次性提示词。
- **Harness Engineering**：用代码层约束阻止无来源事件、幻觉 URL、低置信度结果和不可控 agent loop 进入最终报告。
- **Item-level LLM Extraction**：OpenAI-compatible extractor 按单条 `RawNewsItem` 调用 LLM，降低 batch JSON 失败风险，并让 retry 和错误定位更精确。
- **Structured Output**：所有原始新闻、结构化事件、日报、评估摘要和 reviewer 输出都有明确 schema 或结构化格式。
- **Self Verification**：每个阶段都有 schema validation、source grounding、confidence check 或测试验证。
- **Evaluation Harness**：用 expected fixture 量化 category accuracy、grounding pass rate、failed item count 和 confidence，而不是凭主观感觉判断质量。
- **AI Reviewer / Critique-Revise**：用 deterministic reviewer 检查 mismatch、低置信度、失败项、baseline 对比和输出文件完整性。
- **Test-backed Development**：默认测试不依赖真实 API key，真实 LLM 集成测试通过环境变量显式开启。

## 为什么这不是普通 Vibe Coding

普通 vibe coding 往往是：

- 让 AI 直接读新闻并生成报告
- 人工觉得报告合理就提交
- 没有中间结构化产物
- 没有 source grounding
- 没有自动化质量评估

本项目的做法是：

- 原始输入保留 `source` 和 `url`
- 抽取结果必须是 `StructuredAIEvent`
- LLM 输出必须通过 JSON parse、Pydantic validation、source grounding、evidence grounding 和 confidence gate
- pipeline 保持 fail-fast，不能生成误导性报告
- evaluation harness 量化 extractor 的质量
- AI Reviewer 复审评估结果并给出可执行改进建议

## 项目流程

当前架构：

```text
RawNewsItem
-> Extractor Strategy
-> Item-level LLM Extraction
-> Schema Validation
-> Harness Verification
-> Evaluation Harness
-> AI Reviewer
-> Report Generation
```

核心输出：

```text
data/processed/structured_events.json
outputs/daily_report.md
outputs/rule_evaluation_summary.json
outputs/rule_evaluation_report.md
outputs/llm_evaluation_summary.json
outputs/llm_evaluation_report.md
outputs/review_summary.json
outputs/review_report.md
```

## 快速运行

安装项目：

```bash
python3 -m pip install -e .
```

运行默认测试：

```bash
python3 -m pytest
```

使用真实样例数据运行稳定 rule baseline：

```bash
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor rule
```

生成：

```text
data/processed/structured_events.json
outputs/daily_report.md
```

## 端到端实际验收

下面流程模拟从 GitHub 重新 clone 后进行验收。该流程不需要 API key，可以验证项目是否能真实运行。`rule` 模式是稳定 baseline，`openai-compatible` 模式才需要本地 `.env`。

```bash
git clone https://github.com/Zhuoran-26/Daily_AI_Insight_Engine.git
cd Daily_AI_Insight_Engine
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor rule --output-prefix rule
python3 -m daily_ai_insight.cli review --evaluation outputs/llm_evaluation_summary.json --baseline outputs/rule_evaluation_summary.json
```

这组命令可以验证：

- 项目依赖可以安装
- pipeline 可以真实跑通
- rule baseline 可以重新生成日报
- evaluation harness 可以重新生成 rule 评估
- reviewer 可以基于已提交的 LLM evaluation 与新生成的 rule baseline 做复审

## 数据策略

项目保留两类输入数据：

- `data/raw/sample_ai_news.json`：synthetic fixture，用于稳定测试和回归验证。
- `data/raw/real_ai_news_sample.json`：real-world sample，用于展示真实来源、真实 URL 和实际 pipeline 效果。

所有真实样例都必须保留 `source` 和 `url`。Harness 会阻止缺失来源、虚构 URL、低置信度或无法追溯的结构化事件进入最终报告。

## Extractor 模式

项目支持三种 extractor：

- `rule`：默认 deterministic baseline，本地可复现，不需要 LLM。
- `mock-llm`：本地测试替身，用于模拟 LLM 工作流、幻觉 source/url、低置信度和 malformed output。
- `openai-compatible`：真实 OpenAI-compatible LLM 接口，当前默认面向 DeepSeek API，需要本地 `.env`。

运行示例：

```bash
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor rule
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor mock-llm
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor openai-compatible
```

如果缺少 `OPENAI_API_KEY`，`openai-compatible` 会清晰失败，不会静默 fallback 到 `rule`，也不会假装 LLM 成功。

## DeepSeek / OpenAI-compatible 运行方式

创建本地环境文件：

```bash
cp .env.example .env
# 编辑 .env，填入自己的 DeepSeek API key
```

`.env.example` 示例：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
# 如需更强推理，可改用:
# OPENAI_MODEL=deepseek-v4-pro
```

注意：

- `.env` 不要提交。
- 不要把真实 API key 写进 README、测试或代码。
- DeepSeek 默认模型为 `deepseek-v4-flash`。
- 如果需要更强推理，可以把 `OPENAI_MODEL` 改为 `deepseek-v4-pro`。

建议验证顺序：

```bash
python3 scripts/smoke_test_llm.py
RUN_LLM_INTEGRATION=1 python3 -m pytest tests/test_llm_integration.py
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor openai-compatible --output-prefix llm
```

默认测试不会调用真实 API。只有设置 `RUN_LLM_INTEGRATION=1` 且本地存在 `OPENAI_API_KEY` 时，才会运行真实 LLM integration test。

## Evaluation Harness

运行 rule baseline 评估：

```bash
python3 -m daily_ai_insight.cli evaluate \
  --input data/raw/real_ai_news_sample.json \
  --expected data/eval/expected_real_sample_categories.json \
  --extractor rule \
  --output-prefix rule
```

运行 LLM 评估：

```bash
python3 -m daily_ai_insight.cli evaluate \
  --input data/raw/real_ai_news_sample.json \
  --expected data/eval/expected_real_sample_categories.json \
  --extractor openai-compatible \
  --output-prefix llm
```

评估输出：

```text
outputs/rule_evaluation_summary.json
outputs/rule_evaluation_report.md
outputs/llm_evaluation_summary.json
outputs/llm_evaluation_report.md
```

当前已验证结果：

| Extractor | Category Accuracy | Grounding Pass Rate | Avg Confidence | Failed Items |
|---|---:|---:|---:|---:|
| Rule baseline | 0.38 | 1.00 | 0.70 | 0 |
| DeepSeek V4 Flash | 0.69 | 1.00 | 0.92 | 0 |

结论：

- rule baseline 暴露了规则方法在复杂语义分类上的局限。
- DeepSeek V4 Flash 在复杂语义分类上更强。
- Harness 保证两种模式都保持 source grounding，不允许无来源事件进入报告。

## AI Reviewer / Critique-Revise

运行 reviewer：

```bash
python3 -m daily_ai_insight.cli review \
  --evaluation outputs/llm_evaluation_summary.json \
  --baseline outputs/rule_evaluation_summary.json
```

生成：

```text
outputs/review_summary.json
outputs/review_report.md
```

Reviewer 会检查：

- category mismatch
- failed item
- grounding pass rate 是否低于 1.0
- average confidence 是否低于阈值
- LLM accuracy 是否明显高于 rule baseline
- evaluation report 和 daily report 是否存在

当前 reviewer 结论是 `reviewed_with_warnings`，原因是 DeepSeek V4 Flash 虽然显著高于 rule baseline，但仍存在少量 category mismatch。这是项目刻意保留的 critique-revise 展示面，而不是把 LLM 输出包装成完美结果。

## Harness Engineering 约束

Harness 的目标不是增强功能，而是防止不可信 AI 输出进入下游：

- 阻止 hallucinated source/url
- 阻止 ungrounded event
- 阻止 confidence 过低的结果进入最终报告
- 限制 LLM retry 次数，避免不可控 agent loop
- 对每个 extractor 使用同一套 schema validation 和 grounding checks
- pipeline 出错时 fail fast，不生成误导性报告

## 面试演示建议

推荐演示顺序：

1. 展示 README 顶部项目定位，强调这是工程化 AI Coding / Agentic Engineering 项目。
2. 展示 [`docs/final_showcase_report.md`](docs/final_showcase_report.md)，快速说明整体架构和结果。
3. 运行 rule pipeline：

   ```bash
   python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor rule
   ```

4. 展示 rule vs LLM evaluation：

   ```text
   outputs/rule_evaluation_report.md
   outputs/llm_evaluation_report.md
   ```

5. 展示 reviewer report：

   ```text
   outputs/review_report.md
   ```

6. 解释 Harness 如何防止幻觉、无来源事件和不可控 agent loop。

## 已知限制

- 当前 real-world sample 规模为 13 条，适合展示与评估，但不是完整生产数据集。
- evidence grounding 使用保守启发式，主要依赖 title/summary 可追溯片段。
- 真实新闻目前是手动整理样例，尚未接入 RSS/API collector。
- AI Reviewer 当前是 deterministic reviewer，还没有实现多轮自动 prompt repair。

## 后续演进

- 接入 RSS/API collector。
- 增加 reviewer-driven prompt refinement。
- 支持多日趋势追踪。
- 增加 Streamlit 或静态可视化 dashboard。
- 增加 CI workflow，自动运行默认测试与 fixture 校验。
