# AI Coding Showcase

## Why This Is Not Just Vibe Coding

This project is designed to avoid one-shot prompting. The goal is not to paste raw news into an AI model and accept a polished report. The system is organized as a pipeline where each stage has a contract, validation rule, and review surface.

The important engineering choices are:

- raw inputs are preserved as `RawNewsItem` records
- extracted events use a defined `StructuredAIEvent` schema
- invalid or low-confidence records are blocked before analysis
- report claims must reference supporting event IDs or source evidence
- AI-generated outputs are reviewed as data, not accepted as final truth

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
