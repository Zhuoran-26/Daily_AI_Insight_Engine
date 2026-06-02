# Daily AI Insight Engine - Final Showcase

## What This Project Does

Daily AI Insight Engine turns AI-related news into structured, validated, and reviewable daily insight artifacts.

The current system can load curated raw news, normalize each item into `RawNewsItem`, extract `StructuredAIEvent` records with a selected extractor, enforce schema and harness checks, generate a daily report, evaluate extraction quality, and run a deterministic reviewer over the evaluation output.

## Why This Is More Than Vibe Coding

This project does not ask an LLM to directly write a plausible report. It builds an inspectable workflow around model output:

- source records keep `source` and `url`
- extractor output must conform to schema
- source and evidence grounding are checked before reports
- confidence gates block low-confidence records
- item-level LLM extraction has retry budgets
- evaluation uses an expected fixture instead of subjective impressions
- reviewer output is structured and actionable

The point is not only that AI can generate text. The point is that AI-assisted work can be constrained, measured, reviewed, and explained.

## System Architecture

RawNewsItem -> Extractor Strategy -> Item-level LLM Extraction -> Schema Validation -> Harness Verification -> Evaluation Harness -> AI Reviewer -> Report Generation

The production pipeline stays fail-fast. If schema validation, source grounding, evidence grounding, or confidence checks fail, the pipeline does not produce a misleading final report.

The evaluation pipeline is intentionally more diagnostic. It records item-level failures so extractor quality can be measured without weakening production safety.

## Rule Baseline vs DeepSeek V4

Observed local evaluation result on the 13-item real-world sample:

| Extractor | Accuracy | Grounding | Avg Confidence | Failed Items |
|---|---:|---:|---:|---:|
| Rule baseline | 0.38 | 1.00 | 0.70 | 0 |
| DeepSeek V4 Flash | 0.69 | 1.00 | 0.92 | 0 |

The rule baseline is stable and reproducible, but it over-classifies complex items that mention model names. The DeepSeek V4 Flash run improves category accuracy while preserving grounding, which is the kind of measurable gain the project is designed to expose.

## Harness Engineering

Harness Engineering is the control layer around the AI pipeline:

- source grounding blocks hallucinated source names and URLs
- evidence grounding requires extracted evidence to be traceable to raw title or summary text
- confidence gates prevent low-confidence records from entering final reports
- item-level retry limits prevent uncontrolled LLM repair loops
- fail-fast behavior avoids silently producing unsupported reports
- no structured event can invent a raw source outside the input data

These guardrails make LLM extraction optional but verification mandatory.

## Evaluation Harness

The evaluation harness measures extractor quality instead of relying on a reviewer saying the output "looks right."

It compares predictions against `data/eval/expected_real_sample_categories.json` and reports:

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

This creates a critique-revise workflow: run evaluation, review the result, revise extractor rules or prompts, then rerun evaluation. The current reviewer is deterministic so it can be tested and demonstrated reliably.

## Engineering Quality

The project demonstrates test-backed AI engineering rather than one-shot generation:

- 57 default tests in the Phase 6 suite, with real LLM integration gated by environment variables
- deterministic rule baseline remains the default extractor
- mock LLM tests simulate hallucinated source URLs, malformed output, and low confidence
- OpenAI-compatible integration is optional and requires local `.env` configuration
- no API key is committed
- prompts, docs, schemas, and harness constraints are versioned
- final artifacts are generated from traceable intermediate outputs

## Known Limitations

- The expected category fixture currently covers only 13 real-world sample items.
- Evidence grounding uses a conservative heuristic based on raw title and summary text.
- Real news collection is manually curated in this phase.
- The reviewer does not yet perform multi-round automatic prompt repair.
- Category labels are useful for demonstration but not yet a full ontology of AI market events.

## Future Work

- Add RSS or API-based collector with source allowlists.
- Add reviewer-driven prompt refinement for repeatable critique-revise loops.
- Track multi-day trends and deltas across reports.
- Add a Streamlit or static dashboard for visualization.
- Add CI workflow for default tests, fixture validation, and artifact checks.
