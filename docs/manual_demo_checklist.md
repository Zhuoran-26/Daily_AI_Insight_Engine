# 手动演示验收清单

用于验证轻量 Streamlit 产品 Demo 和 CLI 端到端流程，不需要生产部署。

## 不需要 API Key 的最终验收路径

```bash
python3 -m pip install -e .
python3 -m pytest
python3 -m daily_ai_insight.cli run --input data/raw/real_ai_news_sample.json --extractor rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/real_ai_news_sample.json --expected data/eval/expected_real_sample_categories.json --extractor rule --output-prefix rule
python3 -m daily_ai_insight.cli evaluate --input data/raw/mixed_channel_ai_news_sample.json --expected data/eval/expected_mixed_sample_categories.json --extractor rule --output-prefix mixed_rule
python3 -m daily_ai_insight.cli review --evaluation outputs/llm_evaluation_summary.json --baseline outputs/rule_evaluation_summary.json
streamlit run app.py
```

这条路径验证 deterministic baseline、harnessed pipeline、real sample evaluation、mixed-channel sample evaluation、reviewer 和产品 Demo UI，不需要真实 API key。

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

在 **输入数据** 中选择：

```text
real_ai_news_sample.json
```

确认 UI 显示有效的原始新闻数量。

Phase 8.1 的中英混合多渠道样例也可以通过 CLI 验证：

```bash
python3 -m daily_ai_insight.cli evaluate \
  --input data/raw/mixed_channel_ai_news_sample.json \
  --expected data/eval/expected_mixed_sample_categories.json \
  --extractor rule \
  --output-prefix mixed_rule
```

该样例用于展示官方渠道、科技媒体、聚合平台、社交媒体/社区平台的中英混合覆盖。每条记录都保留来源、URL、发布日期、来源渠道、来源语言、选择理由和采集时间；它是产品演示静态样例，不代表完整实时舆情采集系统。

## 4. 选择抽取模式

在 **抽取模式** 中选择：

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
- 分类分布
- 重点事件表格
- 结构化事件表格
- Harness 校验摘要
- 分析日报 Markdown

## 6. 检查分析日报

确认 UI 中出现分析日报区块，并且生成产物存在：

```text
outputs/daily_report.md
```

## 7. 运行评估

点击：

```text
Run Evaluation
```

检查 UI 是否展示：

- 分类准确率
- 来源追溯通过率
- 平均置信度
- 失败项
- 分类不一致项表格

当前 evaluation 使用：

```text
data/eval/expected_real_sample_categories.json
```

除非新增匹配的 expected fixture，否则不要对自定义上传数据强行评估。

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

## 9. 中文体验检查

确认以下内容：

- Streamlit 页面标题为 `Daily AI Insight Engine｜AI 行业洞察日报系统`。
- 页面主要区块、按钮、提示和错误提示为中文。
- 运行后日报 section 使用中文，包括 `今日主要热点`、`分类分布`、`关键结论`、`趋势信号`、`风险与机会`、`方法说明`。
- 输入英文新闻时，原始 title/source/url 保持原样，系统生成的分析内容面向中文用户。
- 技术名和 source/url 保持原样，例如 OpenAI、DeepSeek、LLM、Agent、GPU。
- mixed sample 中的英文来源可以输入系统，但面向用户的分析输出应为中文。
- mixed sample 的 provenance 字段来自 raw input，不允许 LLM 编造或覆盖。
- 风险/机会描述应围绕 AI 行业趋势、舆情监测与决策辅助，不应把系统可信度风险误写成行业风险。

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
