# Project Spec v1

## Problem Statement

Daily AI Insight Engine is an MVP system for producing an "AI analysis daily report" from recent AI-related news and information.

The assignment requires the project to:

- collect or prepare 10 to 20 recent AI-related news items
- include source, title, content or summary, and publication time
- design a structured data schema for extraction
- avoid simple summary stitching or one-shot AI generation
- show data processing, validation, analysis logic, and design decisions
- generate a daily report with top events, deep analysis, trend judgment, and optional risk or opportunity notes
- include clear visual output in a suitable form
- document data sources, system design, AI usage, prompts, error handling, and the end-to-end flow

The project should demonstrate engineering judgment under a short delivery window: prioritize a small but complete pipeline over broad features that cannot be verified.

## MVP Scope

The first version should include:

- A documented set of 10 to 20 AI-related news items.
- A raw news data format with source metadata.
- A structured extraction schema for AI events.
- Validation rules for required fields, dates, categories, and provenance.
- A trend analysis process based on validated structured events.
- A daily report format with traceable claims.
- A simple visualization design that communicates event categories, importance, timeline, source distribution, or trend signals.
- Documentation explaining data source choices, AI usage, prompt strategy, validation strategy, and limitations.

The first version should not require:

- a production crawler
- real-time monitoring
- user accounts
- deployment infrastructure
- large-scale data storage
- fully automated fact checking
- investment advice or financial recommendation output

## Architecture Draft

The MVP architecture follows a staged pipeline:

Collector / Loader -> Extractor Strategy -> Schema Validation -> Harness Verification -> Analyzer -> Reporter

The showcase evaluation flow extends the pipeline with quality measurement and critique:

RawNewsItem -> Extractor Strategy -> Item-level LLM Extraction -> Schema Validation -> Harness Verification -> Evaluation Harness -> AI Reviewer -> Report Generation

### Collector / Loader

Collects or prepares raw AI-related news items from documented sources. For the MVP, static manually curated data is acceptable if sources and selection reasons are documented.

Responsibilities:

- capture title, source, URL, publication time, language, and content or summary
- record why the source is trusted or useful
- avoid duplicates where possible
- preserve enough raw context for extraction

### Extractor Strategy

Transforms each `RawNewsItem` into one or more `StructuredAIEvent` records. The extractor is a strategy interface so the project can run deterministic rules by default while leaving space for optional LLM extraction.

Responsibilities:

- extract event type, entities, technologies, affected markets, and key facts
- separate facts from model interpretation
- include confidence and evidence fields
- preserve provenance back to raw news records
- support `rule`, `mock-llm`, and OpenAI-compatible LLM modes
- fail clearly when the OpenAI-compatible extractor is selected without required configuration
- process OpenAI-compatible LLM extraction one raw item at a time
- retry invalid LLM output for the failed item up to two times without silently falling back to rules

### Schema Validation

Checks structured records before harness verification and analysis.

Responsibilities:

- verify required fields
- validate enum values and date formats
- check provenance links
- flag low-confidence or malformed records
- produce validation status and failure reasons

### Harness Verification

Blocks unsafe extractor output before analysis.

Responsibilities:

- check source integrity
- check extractor name
- check schema compliance
- check source and URL grounding
- check evidence grounding
- enforce confidence threshold
- enforce loop or step budget
- fail fast instead of silently repairing unsafe output

### Item-Level LLM Extraction

OpenAI-compatible LLM extraction is item-level rather than batch-level. For each `RawNewsItem`, the extractor builds a single-item prompt, calls the LLM, parses one JSON object, validates one structured event, forces immutable source fields from the raw item, applies grounding and confidence checks, and retries only that item when needed.

This design reduces token pressure and whole-batch JSON failure risk. It also makes errors easier to locate because failures include item index, title, and reason. Source grounding is easier to enforce because each event is checked against exactly one raw item. This matches the project's Agentic Engineering goal: bounded, inspectable, and recoverable execution steps.

### Evaluation Harness

The project includes a separate evaluation harness for extractor comparison. It runs an extractor against raw input, compares predicted categories against an expected fixture, and reports category accuracy, valid output rate, grounding pass rate, confidence distribution, and failed item count.

Evaluation is intentionally distinct from production pipeline behavior. The pipeline remains fail-fast to avoid generating misleading reports. Evaluation records item-level failures so the team can inspect extractor weaknesses, compare `rule`, `mock-llm`, and `openai-compatible`, and demonstrate quality measurement during an interview.

### AI Reviewer / Critique-Revise Workflow

The project includes a deterministic reviewer layer for evaluation artifacts. It reviews `EvaluationSummary` outputs, compares an extractor against the rule baseline when available, checks for category mismatches, failed items, grounding gaps, low confidence, and missing report artifacts, then emits a structured review summary and Markdown review report.

This reviewer is not a replacement for harness validation. Harness checks block unsafe data before downstream use. The reviewer explains what the results mean, what should be revised, and what can be safely claimed in a showcase. The critique-revise loop is bounded and inspectable: review findings are structured, severity-ranked, and tied to concrete follow-up actions.

### Analyzer

Turns validated events into daily insights.

Responsibilities:

- rank top events
- group events by theme
- identify trend signals
- distinguish technology, application, policy, capital, and product movements
- summarize uncertainty and evidence

### Reporter

Generates the final daily report from analysis outputs.

Responsibilities:

- produce readable sections for hotspots, deep dives, trends, and risks or opportunities
- connect claims to supporting event IDs and sources
- include visualization-ready summaries
- document validation notes and limitations

## Harness Engineering Requirements

Harness Engineering constrains the pipeline so AI outputs remain verifiable, grounded, and bounded. The goal is not to enhance functionality. The goal is to prevent hallucinated sources, ungrounded events, infinite loops, unverifiable AI output, and low-confidence results from directly entering the final report.

### Source Integrity Check

Each `RawNewsItem` must preserve source identity and URL when available. The system must reject or quarantine records that lack enough source metadata for downstream claims.

### Structured Output Validation

Each `StructuredAIEvent` and `DailyInsightReport` must pass schema validation before use. Required fields, enum values, date formats, provenance links, evidence fields, and validation statuses must be checked.

### Grounding Check

Every extracted event must reference one or more source `RawNewsItem` records. Every report claim must reference supporting event IDs or source evidence. The system must not allow model-created sources, URLs, or unsupported claims.

### Confidence Threshold

Model-derived extraction and analysis outputs must include confidence information. Outputs below the configured threshold must enter human review, deterministic fallback, or fail-fast handling instead of the final report.

### Loop Guard / Step Budget

Any agent loop must have a documented step budget, stop condition, and maximum retry count. This applies to source collection, extraction repair, validation repair, analysis refinement, and reviewer loops.

### Deterministic Baseline

Each AI-assisted stage should define a deterministic baseline or fallback, such as returning a validation error, using rule-based filtering, skipping an invalid record, or producing a minimal report section from validated inputs only.

### Fail-fast Error Handling

The pipeline should fail fast when required inputs, schema validation, source grounding, or confidence thresholds are not satisfied. Silent repair is not allowed for failures that affect report correctness.

### Test-backed Verification

Core pipeline behavior must be backed by automated tests once implementation begins. Tests should cover normal inputs, malformed inputs, missing sources or URLs, hallucinated sources or URLs, low-confidence records, loop budget exhaustion, and empty inputs.

## Data Schema Draft

This section defines fields only. It does not implement code.

### RawNewsItem

- `id`: stable unique identifier for the raw item
- `title`: original title
- `source_name`: publisher, platform, or channel name
- `source_type`: media, official, social, aggregator, academic, other
- `url`: source URL when available
- `published_at`: publication datetime with timezone when available
- `collected_at`: collection datetime
- `language`: detected or recorded language
- `content`: full text when available
- `summary`: source-provided or manually prepared summary when full text is unavailable
- `author`: author or organization when available
- `tags`: source-level tags or manually assigned labels
- `selection_reason`: why this item was included
- `raw_quality_notes`: limitations such as partial text, paywall, or uncertain timestamp

### StructuredAIEvent

- `id`: stable unique identifier for the structured event
- `raw_item_ids`: source `RawNewsItem` identifiers
- `event_title`: normalized event title
- `event_date`: date of the event or publication-derived date
- `event_type`: product_release, model_release, research, policy, funding, partnership, safety, market_signal, infrastructure, other
- `primary_entities`: companies, labs, governments, products, or people central to the event
- `secondary_entities`: supporting or mentioned entities
- `technologies`: models, methods, chips, platforms, datasets, or tools involved
- `application_area`: coding, search, agents, robotics, education, healthcare, finance, media, enterprise, consumer, infrastructure, other
- `geography`: relevant country or region when identifiable
- `key_facts`: factual bullet points extracted from sources
- `impact_summary`: concise interpretation of why the event matters
- `trend_tags`: labels used for grouping trend signals
- `risk_tags`: safety, regulatory, market, reliability, privacy, security, misinformation, other
- `opportunity_tags`: product, investment, ecosystem, adoption, developer_tools, research, other
- `sentiment`: positive, neutral, negative, mixed, unknown
- `importance_score`: numeric score for ranking within the daily report
- `confidence_score`: confidence in extraction quality
- `evidence`: source snippets or paraphrased evidence references
- `validation_status`: pending, valid, invalid, needs_review
- `validation_errors`: field-level validation issues

### DailyInsightReport

- `id`: stable unique identifier for the report
- `report_date`: date covered by the report
- `source_item_count`: number of raw news items considered
- `valid_event_count`: number of validated structured events used
- `top_events`: ranked list of important `StructuredAIEvent` IDs with reasons
- `theme_groups`: grouped trend themes and supporting event IDs
- `deep_dives`: detailed analysis sections for selected events
- `trend_judgments`: technology, application, policy, capital, and market trend conclusions
- `risk_notes`: risks with supporting evidence and uncertainty
- `opportunity_notes`: opportunities with supporting evidence and uncertainty
- `visualization_specs`: chart-ready summaries, dimensions, labels, and supporting event IDs
- `source_coverage_notes`: source mix, language mix, and coverage limitations
- `validation_summary`: validation pass rate, quarantined items, and review notes
- `generated_at`: generation datetime
- `human_review_status`: not_reviewed, reviewed, revised
- `human_review_notes`: reviewer comments or overrides

## Evaluation Criteria

### Software Engineering Ability

- Clear staged architecture with separable responsibilities.
- Explicit data contracts between pipeline stages.
- Validation before analysis and reporting.
- Small MVP scope that can be completed and inspected.
- Documentation that explains tradeoffs and limitations.

### AI Coding Ability

- AI is used as a structured extraction and reasoning component, not as a black-box report writer.
- Prompts and outputs are designed around schemas.
- Model-derived claims include evidence, provenance, and confidence.
- AI outputs are reviewed and validated before downstream use.
- Failure cases are anticipated and documented.

### Agent Workflow

- Agents follow Spec -> Implementation -> Review -> Test -> Documentation.
- Skills encode repeatable workflows for specification, structured output, review, tests, and reporting.
- Review steps evaluate both code quality and AI-output quality.
- The project keeps intermediate artifacts inspectable for human review.
- Final delivery can explain how each result was produced from source data.
