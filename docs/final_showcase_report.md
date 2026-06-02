# Daily AI Insight Engine - Final Showcase

## What This Project Does

Daily AI Insight Engine turns AI-related news into structured, validated, and reviewable daily insight artifacts.

The current system can load curated raw news, normalize each item into `RawNewsItem`, extract `StructuredAIEvent` records with a selected extractor, enforce schema and harness checks, generate a business-oriented daily report, evaluate extraction quality, and run a deterministic reviewer over the evaluation output.

For the final showcase, the recommended input is `data/raw/mixed_channel_ai_news_sample.json`. It is a Chinese/English multi-channel sample aligned with the assignment's data acquisition guidance: official channels, tech media, aggregators, and social/community sources.

The mixed sample also includes topic-level provenance with `canonical_topic` and `topic_role`. This lets the system show when one hotspot is covered by multiple source types instead of treating repeated appearances as accidental duplicates.

## Why This Is More Than Vibe Coding

This project does not ask an LLM to directly write a plausible report. It builds an inspectable workflow around model output:

- source records keep `source` and `url`
- extractor output must conform to schema
- source and evidence grounding are checked before reports
- confidence gates block low-confidence records
- business analysis fields are structured as data instead of free-form report prose
- item-level LLM extraction has retry budgets
- evaluation uses an expected fixture instead of subjective impressions
- reviewer output is structured and actionable

The point is not only that AI can generate text. The point is that AI-assisted work can be constrained, measured, reviewed, and explained.

## Chinese Product Experience

The product layer is designed for Chinese users while preserving source traceability. English input news keeps its original `title`, `source`, and `url`, but user-facing analysis, trend signals, risks, opportunities, evaluation reports, reviewer reports, and the Streamlit UI are localized for Chinese reading.

Schema keys, category enum values, and extractor names remain English on purpose. That keeps validation, tests, and Evaluation Harness behavior stable while avoiding a mixed-language product experience.

Phase 8.2 adds business-facing analysis fields to `StructuredAIEvent`: `background`, `industry_impact`, `trend_signal`, `industry_risk`, `industry_opportunity`, `decision_hint`, `llm_generated`, and `requires_human_review`. The rule extractor fills these fields with deterministic Chinese templates; the OpenAI-compatible extractor can receive them from the LLM but still forces immutable source and provenance fields from raw input.

## System Architecture

RawNewsItem -> Extractor Strategy -> Item-level LLM Extraction -> Schema Validation -> Harness Verification -> Evaluation Harness -> AI Reviewer -> Report Generation

The production pipeline stays fail-fast. If schema validation, source grounding, evidence grounding, or confidence checks fail, the pipeline does not produce a misleading final report.

The evaluation pipeline is intentionally more diagnostic. It records item-level failures so extractor quality can be measured without weakening production safety.

## Rule Baseline vs DeepSeek V4

Observed local evaluation result on the 16-item mixed-channel showcase sample:

| Extractor | Accuracy | Grounding | Avg Confidence | Failed Items |
|---|---:|---:|---:|---:|
| Rule baseline | 0.50 | 1.00 | 0.70 | 0 |
| DeepSeek V4 Flash | 0.88 | 1.00 | 0.89 | 0 |

Historical comparison on the 13-item real-world sample:

| Extractor | Accuracy | Grounding | Avg Confidence | Failed Items |
|---|---:|---:|---:|---:|
| Rule baseline | 0.38 | 1.00 | 0.70 | 0 |
| DeepSeek V4 Flash | 0.69 | 1.00 | 0.92 | 0 |

The rule baseline is stable and reproducible, but it over-classifies complex items that mention model names. The DeepSeek V4 Flash runs improve category accuracy while preserving grounding, which is the kind of measurable gain the project is designed to expose.

## Harness Engineering

Harness Engineering is the control layer around the AI pipeline:

- source grounding blocks hallucinated source names and URLs
- evidence grounding requires extracted evidence to be traceable to raw title or summary text
- confidence gates prevent low-confidence records from entering final reports
- item-level retry limits prevent uncontrolled LLM repair loops
- fail-fast behavior avoids silently producing unsupported reports
- no structured event can invent a raw source outside the input data
- raw `canonical_topic` and `topic_role` are copied through extraction and are not inferred by the LLM

These guardrails make LLM extraction optional but verification mandatory.

LLM-generated analysis is never treated as final industry judgment. The daily report displays a human-review note for LLM-generated sections, and the reviewer is documented as checking extraction and evaluation quality rather than replacing human business judgment.

## Business Daily Report

The generated daily report is oriented to:

- AI 行业趋势分析
- 舆情监测与风险预警
- 信息快速理解与决策辅助

It contains:

- 数据来源概览 with sample count, channel/language distribution, URL, publication date, source channel, source language, and selection reason
- 热点聚类与多源覆盖, showing official announcements, media framing, aggregator visibility, and community feedback around the same canonical topic
- 今日主要热点 Top 3–5
- 重点事件深度解读 with background, industry impact, trend signal, industry opportunity, industry risk, decision hint, evidence, and source traceability
- 趋势判断 based on model capability, Agent/workflow, cloud infrastructure, application landing, and community feedback
- 舆情监测与风险预警 using only industry risks, not system confidence or harness risks
- 机会提示 for AI coding, enterprise Agent workflow, model API, cloud infrastructure, and vertical applications
- 可视化结果说明 that explains what each current chart answers
- Harness 校验摘要 as a Chinese checklist
- 方法说明 that documents deterministic rule baseline and LLM validation constraints

`published_at` is treated as the source publication date, while `collected_at` is the local fixture collection or review date. This is especially important for community sources such as Reddit or V2EX: they are useful for public-opinion monitoring and feedback signals, but they do not replace official sources for factual release claims.

## Streamlit Product Demo

The Streamlit demo now defaults to `mixed_channel_ai_news_sample.json`, so the first screen starts from the final showcase dataset rather than the older real-world fixture. The UI keeps the same pipeline and harness calls; it does not bypass source grounding or confidence checks.

The product view includes:

- 数据来源追溯: title, source, URL, publication date, source channel, source language, and selection reason
- 业务化结构化事件表: Chinese-friendly columns for category, source channel, summary, industry impact, opportunity, risk, and URL, with raw JSON kept in an expander
- 中文 Harness checklist: source integrity, schema validation, source grounding, evidence grounding, loop guard, confidence threshold, and extractor name, with raw JSON kept in an expander
- 多样化可视化: source channel × language heatmap, event timeline, category distribution, importance × confidence scatter, impact-area distribution, and Rule vs LLM comparison
- 热点聚类与多源覆盖: canonical topic, source count, covered channels/languages, representative title, official-source flag, and community-feedback flag
- LLM 人工复核提示: LLM-generated analysis is marked for human review without being treated as an industry risk

These charts answer practical questions for trend analysis, public-opinion monitoring, risk warning, and decision support: whether the sample is balanced across sources, when events cluster, which AI themes dominate, which events deserve priority, which business/technical areas are affected, and how rule and LLM extractors compare under the same harness.

## Evaluation Harness

The evaluation harness measures extractor quality instead of relying on a reviewer saying the output "looks right."

It compares predictions against an expected category fixture. The Streamlit demo defaults to the mixed sample and `data/eval/expected_mixed_sample_categories.json`; the older real sample still uses `data/eval/expected_real_sample_categories.json`.
It reports:

- category accuracy
- successful and failed item counts
- grounding pass rate
- confidence distribution
- mismatched items
- failed items

This separates hallucination prevention from quality measurement. Harness checks answer "is this safe enough to use?" Evaluation answers "how good was this extractor on the fixture?"

## AI Reviewer Workflow

The AI Reviewer layer is implemented as a deterministic `RuleBasedReviewer` for this phase.

It reviews evaluation output and detects:

- category mismatches
- failed items
- grounding pass rate below 1.0
- average confidence below threshold
- LLM accuracy that is not clearly above rule baseline
- missing evaluation or daily report artifacts

It generates:

- `outputs/review_summary.json`
- `outputs/review_report.md`

For the final mixed showcase, the intended reviewer comparison is `outputs/mixed_llm_evaluation_summary.json` against `outputs/mixed_rule_evaluation_summary.json`.

This creates a critique-revise workflow: run evaluation, review the result, revise extractor rules or prompts, then rerun evaluation. The current reviewer is deterministic so it can be tested and demonstrated reliably.

## Engineering Quality

The project demonstrates test-backed AI engineering rather than one-shot generation:

- default tests run locally with real LLM integration gated by environment variables
- deterministic rule baseline remains the default extractor
- mock LLM tests simulate hallucinated source URLs, malformed output, and low confidence
- OpenAI-compatible integration is optional and requires local `.env` configuration
- no API key is committed
- prompts, docs, schemas, business analysis fields, and harness constraints are versioned
- final artifacts are generated from traceable intermediate outputs

## Known Limitations

- The expected category fixtures cover the 13-item real-world sample and the 16-item mixed-channel showcase sample.
- Evidence grounding uses a conservative heuristic based on raw title and summary text.
- Real news collection is manually curated in this phase.
- The reviewer does not yet perform multi-round automatic prompt repair.
- Category labels are useful for demonstration but not yet a full ontology of AI market events.

## Future Work

- Add RSS or API-based collector with source allowlists.
- Add reviewer-driven prompt refinement for repeatable critique-revise loops.
- Track multi-day trends and deltas across reports.
- Add richer multi-day visualization and dashboard states.
- Add CI workflow for default tests, fixture validation, and artifact checks.
