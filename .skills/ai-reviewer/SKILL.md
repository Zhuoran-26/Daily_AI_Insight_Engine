---
name: ai-reviewer
description: Use this skill for an independent AI review pass over specs, prompts, schemas, pipeline logic, reports, and tests in the Daily AI Insight Engine project.
---

# AI Reviewer

## Purpose

Provide a structured review workflow that catches weak specs, unverifiable AI outputs, missing tests, prompt leakage, shallow analysis, and assignment misalignment before final delivery.

## When To Use

Use this skill after a spec, implementation, prompt, schema, test plan, or report draft exists and before considering the task complete.

## Workflow

1. Read the relevant spec, generated artifacts, and changed files.
2. Review against the assignment goals:
   - structured extraction
   - analysis process
   - design decisions
   - AI usage transparency
3. Check whether inputs, outputs, and schemas are traceable.
4. Look for one-shot AI behavior that bypasses the pipeline.
5. Check whether model-derived claims include evidence or provenance.
6. Check failure handling for missing fields, malformed data, low confidence, and conflicting sources.
7. Check Harness Engineering constraints:
   - no claim appears without a source or supporting event ID
   - no URL or source name is generated without appearing in raw source data
   - no LLM output reaches downstream stages without schema validation
   - no agent loop can run without a step budget, retry limit, and stop condition
   - no core logic is missing automated test coverage after implementation
8. Check whether tests or validation checks cover the highest-risk behavior.
9. Produce findings ordered by severity.
10. For each finding, include a concrete fix or a documented reason to accept the risk.
11. Confirm that addressed findings are reflected in docs, tests, or code.

## Deliverables

- Review findings ordered by severity.
- Explicit pass/fail judgment for assignment alignment.
- List of required fixes before completion.
- List of accepted risks or known limitations.
- Harness review notes for source grounding, validation, confidence thresholds, loop budgets, and missing tests.
- Final reviewer sign-off only after critical findings are resolved.
