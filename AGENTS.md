# AGENTS.md

## Project Goal

Daily AI Insight Engine is an AI-assisted analysis system for transforming daily AI-related news into structured insights, validated event records, trend analysis, visual summaries, and a readable daily report.

The final project should demonstrate that the system is not a one-shot AI summary tool. It should show a clear engineering process:

- Raw AI news is collected from documented sources.
- News items are normalized into a structured schema.
- Structured outputs are validated before downstream use.
- Validated events are analyzed for hotspots, trends, risks, and opportunities.
- Final reports are generated from traceable inputs and reviewable intermediate artifacts.

## Development Workflow

Every development task must follow this order:

1. Spec
2. Implementation
3. Review
4. Test
5. Documentation

Agents must not skip the Spec step. Before implementing any feature, define:

- the user-facing requirement
- input and output contracts
- schema or interface changes
- validation expectations
- test expectations
- documentation updates

Implementation should only begin after the spec is clear enough to review.

## AI Coding Methodology

This project uses the following AI engineering methodology.

### Context Engineering

Agents must gather and preserve the task context before acting:

- read the relevant project spec, skill, and existing docs
- identify source data assumptions and constraints
- keep implementation decisions traceable to the project goal
- avoid hidden one-shot prompting that bypasses the pipeline

### Spec-driven Development

Features must be driven by explicit specs rather than informal prompts. A feature spec should define scope, non-goals, data contracts, acceptance criteria, and failure cases before code is written.

### Structured Output

AI-generated content must be treated as structured data whenever possible. Extracted events, analysis inputs, and report sections should have explicit schemas, required fields, and validation rules.

### Self Verification

Agents must verify their own work before handing it off:

- check schema consistency
- inspect generated artifacts
- run applicable tests or validation commands
- document known gaps and assumptions

### AI Reviewer

Subsequent feature work should include an AI review pass that evaluates correctness, traceability, failure handling, prompt quality, schema quality, and missing tests. Reviewer feedback should be addressed or explicitly documented.

## Git Boundaries

Agents must respect these repository boundaries:

- Do not push to any remote.
- Do not merge `main` or any long-lived branch unless the user explicitly requests it.
- Do not rewrite history.
- Do not run destructive git commands such as `git reset --hard` or forced checkout unless the user explicitly requests it.
- Keep commits focused and explain what changed.

## Definition of Done

A task is done only when all of the following are true:

- The requested scope is completed without adding unrelated changes.
- The spec, implementation, review, test, and documentation expectations have been addressed for that task.
- Structured outputs and schemas are validated where relevant.
- Generated reports or artifacts are inspectable and traceable to inputs.
- Tests or validation checks have been run when applicable, or skipped with a clear reason.
- Documentation reflects the current behavior and known limitations.
- Git status has been checked and the final changes are ready for user review.
