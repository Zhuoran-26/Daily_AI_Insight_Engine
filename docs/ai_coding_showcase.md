# AI Coding Showcase

## Why This Is Not Just Vibe Coding

This project is designed to avoid one-shot prompting. The goal is not to paste raw news into an AI model and accept a polished report. The system is organized as a pipeline where each stage has a contract, validation rule, and review surface.

The important engineering choices are:

- raw inputs are preserved as `RawNewsItem` records
- extracted events use a defined `StructuredAIEvent` schema
- invalid or low-confidence records are blocked before analysis
- report claims must reference supporting event IDs or source evidence
- AI-generated outputs are reviewed as data, not accepted as final truth
- agent loops must have budgets, stop conditions, and deterministic fallback behavior
- completed implementation tasks must be backed by automated tests, not only manual review

This makes the project inspectable. A reviewer can trace a final trend judgment back to structured events and then back to raw news sources.

## Context Engineering Strategy

The project gives agents durable context before implementation begins:

- `AGENTS.md` defines repository rules, development order, methodology, and completion standards.
- `docs/project_spec_v1.md` defines the problem, MVP scope, architecture, schemas, and evaluation criteria.
- `.skills/` provides executable workflows for future agents.

Future prompts should reference the relevant spec and skill before asking for implementation. This reduces ambiguous AI behavior and keeps the work aligned with the interview assignment.

## Agent Workflow Design

The agent workflow is:

1. Spec
2. Implementation
3. Review
4. Test
5. Documentation

The workflow is encoded in both `AGENTS.md` and the project skills.

Each future feature should begin with a small spec that defines scope, data contracts, acceptance criteria, and validation rules. Implementation should then follow the spec. Review should check assignment alignment, schema quality, traceability, and failure handling. Tests should verify the highest-risk assumptions. Documentation should record what changed and what remains limited.

## Validation Strategy

Validation is treated as a first-class part of the pipeline.

Planned validation surfaces include:

- required fields for raw news and structured events
- date and source metadata checks
- enum checks for event type, sentiment, status, and source type
- provenance checks from report claims to event IDs and raw item IDs
- confidence and evidence checks for AI-derived interpretations
- quarantine behavior for malformed or uncertain records

The project should prefer explicit validation failures over silently producing a confident but unsupported report.

## Harness Engineering: Guardrails Against Hallucination

Ordinary vibe coding often works like this:

- let AI directly generate the report
- accept the output if it looks reasonable to a human reviewer

This project uses harness constraints instead:

- original information must preserve `source_name` and `url` when available
- structured results must trace back to `RawNewsItem` records
- future LLM outputs must pass Pydantic schema validation or equivalent schema checks
- low-confidence results must enter review, deterministic fallback, or fail-fast handling
- agent loops must have a step budget and explicit stop condition
- every completed implementation task must add or update automated tests

The harness is a control layer around AI behavior. It prevents hallucinated sources, unsupported claims, unbounded loops, and outputs that cannot be checked by code.

## Optional LLM, Mandatory Verification

The project can run without an LLM. The default `rule` extractor is deterministic and fully local, while `mock-llm` tests the LLM workflow without network access.

If a real LLM extractor is added, its output does not become trusted because "the LLM says so." Every extractor output must pass:

- Pydantic schema validation
- source grounding against `RawNewsItem`
- evidence grounding against raw title or summary
- confidence threshold checks
- loop and step budget controls
- automated tests for hallucinated source URLs and low confidence

The `openai-compatible` extractor is a real OpenAI-compatible adapter path. Without `OPENAI_API_KEY`, it fails clearly. With a key, it must still return `StructuredAIEvent` records and remain behind the same JSON parsing, schema validation, grounding, confidence, retry, and harness verification path.

## Item-Level LLM Extraction

The OpenAI-compatible extractor uses item-level extraction instead of sending the full batch to the model. Each `RawNewsItem` is processed independently: one LLM call, one JSON object, one Pydantic validation pass, one source/evidence grounding check, one confidence check, and item-scoped retries.

This lowers token and JSON failure risk, keeps retry scope small, makes failed news items easy to identify by index and title, and prevents one malformed model response from corrupting an entire batch. It also makes harness verification stricter because `title`, `source`, `url`, `published_at`, and `language` are forced from the raw item rather than trusted from the LLM.

## Human-in-the-loop Design

The MVP should keep human review possible at multiple points:

- source selection can be reviewed before extraction
- structured events can be inspected before trend analysis
- validation failures can be repaired or excluded manually
- report sections can include reviewer notes and overrides
- final documentation can explain which parts were AI-assisted

The intended human role is not to manually redo the whole pipeline. The human reviewer should focus on judgment: source quality, extraction accuracy, trend reasonableness, and final communication quality.

## Future Evolution

After the Agent Workspace is established, the project can evolve in controlled stages:

- add static raw data fixtures and source documentation
- implement schema definitions and validation
- implement extraction prompts and structured output parsing
- add trend analysis over validated events
- generate the daily report from structured inputs
- add visualization from report-ready summaries
- add reviewer prompts and regression checks
- package the final output for interview submission

The same workflow can later support automated data collection, richer visualizations, multilingual processing, and stronger source verification without changing the core engineering philosophy.
