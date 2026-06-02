# 手动演示验收清单

用于验证轻量 Streamlit 产品 Demo 和 CLI 端到端流程，不需要生产部署。

## 不需要 API Key 的最终验收路径

```bash
python3 -m pip install -e .
python3 -m pytest
python3 -m daily_ai_insight.cli run --input data/raw/mixed_channel_ai_news_sample.json --extractor rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor rule --output-prefix rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/mixed_channel_ai_news_sample.json --expected data/eval/expected_mixed_sample_categories.json --extractor rule --output-prefix mixed_rule
python3 -m daily_ai_insight.cli review --evaluation outputs/mixed_llm_evaluation_summary.json --baseline outputs/mixed_rule_evaluation_summary.json
streamlit run app.py
```

这条路径验证 deterministic baseline、harnessed pipeline、mixed-channel showcase sample、real sample evaluation、mixed-channel sample evaluation、reviewer 和产品 Demo UI，不需要真实 API key。

## 使用 DeepSeek 的最终验收路径

```bash
cp .env.example .env
python3 scripts/smoke_test_llm.py
RUN_LLM_INTEGRATION=1 python3 -m pytest tests/test_llm_integration.py
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor openai-compatible --output-prefix llm
```

运行 DeepSeek 路径前，请先在本地编辑 `.env`。不要提交 `.env` 或任何真实 API key。

## 1. 安装依赖

```bash
python3 -m pip install -e .
```

## 2. 运行 Streamlit

```bash
streamlit run app.py
```

打开终端中显示的本地 Streamlit URL。

## 3. 选择输入数据

Streamlit 默认输入应为：

```text
mixed_channel_ai_news_sample.json
```

最终展示推荐使用 `data/raw/mixed_channel_ai_news_sample.json`，因为它覆盖中英混合、官方渠道、科技媒体、聚合平台和社交媒体/社区平台，更贴合 AI 行业趋势分析、舆情监测与风险预警、信息快速理解与决策辅助。

确认 UI 显示有效的原始新闻数量，并展示 `数据来源追溯` 表格。该表应包含标题、来源、URL、发布日期、来源渠道、来源语言、选择理由和采集日期。`published_at` 是来源内容发布时间，`collected_at` 是样本采集或整理时间。

通过 CLI 验证 mixed sample：

```bash
python3 -m daily_ai_insight.cli run \
  --input data/raw/mixed_channel_ai_news_sample.json \
  --extractor rule

python3 -m daily_ai_insight.cli evaluate \
  --input data/raw/mixed_channel_ai_news_sample.json \
  --expected data/eval/expected_mixed_sample_categories.json \
  --extractor rule \
  --output-prefix mixed_rule
```

该样例用于展示官方渠道、科技媒体、聚合平台、社交媒体/社区平台的中英混合覆盖。每条记录都保留来源、URL、发布日期、来源渠道、来源语言、选择理由、采集时间、热点聚类和来源角色；它是产品演示静态样例，不代表完整实时舆情采集系统。

## 4. 选择结构化洞察生成方式

在 **结构化洞察生成方式** 中选择：

```text
rule
```

该路径不需要 API key。

## 5. 生成洞察日报

点击：

```text
生成洞察日报
```

检查 UI 是否展示：

- 事件总数
- 数据来源追溯表格
- 多样化可视化图表
- 热点聚类与多源覆盖表格
- 今日主要热点表格
- 业务化结构化事件表格
- 中文 Harness checklist
- 分析日报 Markdown

结构化事件表默认应使用中文友好列：标题、来源、发布日期、来源渠道、分类、事件类型、重要性、置信度、中文摘要、行业影响、行业机会、行业风险、URL。完整结构化 JSON 应放在 `查看完整结构化 JSON` expander 中。

Harness Summary 默认应是中文 checklist；原始 JSON 应放在 `查看原始 Harness JSON` expander 中。

热点聚类区应展示 `canonical_topic`、覆盖来源数量、覆盖渠道、覆盖语言、代表标题、是否包含官方来源、是否包含社区反馈。这里的多源覆盖用于说明同一热点的信息扩散链路，社区源用于观察反馈和舆情，不作为事实主来源。

## 6. 检查分析日报

确认 UI 或 CLI 生成的分析日报包含以下中文 section，并且生成产物存在：

```text
outputs/daily_report.md
```

需要检查的 section：

- `数据来源概览`
- `热点聚类与多源覆盖`
- `今日主要热点 Top 3–5`
- `重点事件深度解读`
- `趋势判断`
- `舆情监测与风险预警`
- `机会提示`
- `可视化结果说明`
- `Harness 校验摘要`
- `方法说明`

## 6.1 检查可视化

确认 UI 中每个图表旁边都有“这个图回答什么问题”的说明，并至少包含：

- 来源渠道 × 来源语言覆盖矩阵：验证中英混合与多渠道来源覆盖。
- 事件发布时间线：观察样本在时间上的分布和近期热点。
- 分类分布：观察当前 AI 热点集中方向。
- 重要性 × 置信度散点图：辅助判断优先关注事件和需要人工复核的事件。
- 影响领域分布：观察事件主要影响的业务或技术方向。
- Rule vs LLM 评估对比：说明 rule baseline 的局限、DeepSeek V4 Flash 的语义优势，以及 Harness 对来源追溯的约束。

## 7. 运行评估

点击：

```text
运行评估
```

检查 UI 是否展示：

- 分类准确率
- 来源追溯通过率
- 平均置信度
- 失败项
- 分类不一致项表格

当前 evaluation 默认对 mixed sample 使用：

```text
data/eval/expected_mixed_sample_categories.json
```

如果切换到 `real_ai_news_sample.json`，应自动使用 `data/eval/expected_real_sample_categories.json`。自定义上传数据可以生成日报，但需要匹配的 expected fixture 才能进行定量评估。

## 8. 运行 AI Reviewer 复审

点击：

```text
运行复审
```

检查 UI 是否展示：

- 最终结论
- 错误数
- 警告数
- 信息数
- 复审问题表格
- 复审报告 Markdown

Reviewer 可以使用当前 evaluation 结果，也可以使用已保存的 showcase outputs。

确认 Reviewer 区域提示：Reviewer 复审的是抽取与评估质量，不替代人工行业判断；涉及 LLM 生成内容时，需要人工审核。

## 9. 中文体验检查

确认以下内容：

- Streamlit 页面标题为 `Daily AI Insight Engine｜AI 行业洞察日报系统`。
- 页面主要区块、按钮、提示和错误提示为中文。
- 运行后日报 section 使用中文，包括 `数据来源概览`、`今日主要热点 Top 3–5`、`重点事件深度解读`、`趋势判断`、`舆情监测与风险预警`、`机会提示`、`可视化结果说明`、`Harness 校验摘要`、`方法说明`。
- 输入英文新闻时，原始 title/source/url 保持原样，系统生成的分析内容面向中文用户。
- 技术名和 source/url 保持原样，例如 OpenAI、DeepSeek、LLM、Agent、GPU。
- mixed sample 中的英文来源可以输入系统，但面向用户的分析输出应为中文。
- mixed sample 的 provenance 字段来自 raw input，不允许 LLM 编造或覆盖。
- 风险/机会描述应围绕 AI 行业趋势、舆情监测与决策辅助，不应把系统可信度风险误写成行业风险。
- LLM 生成内容旁边应显示人工复核提示：`本段分析由 LLM 生成，已通过 Schema、Source Grounding 和 Harness 校验，但仍建议人工复核。`

## 10. 可选 DeepSeek / OpenAI-compatible Demo

创建本地 `.env` 文件：

```bash
cp .env.example .env
```

本地编辑 `.env`：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
```

不要提交 `.env` 或任何真实 API key。

然后运行 smoke 和 integration 检查：

```bash
python3 scripts/smoke_test_llm.py
RUN_LLM_INTEGRATION=1 python3 -m pytest tests/test_llm_integration.py
```

在 Streamlit 中选择：

```text
openai-compatible
```

然后重新运行 pipeline 或 evaluation。如果缺少 API key，UI 应显示清晰错误，不得静默 fallback 到 `rule`。
