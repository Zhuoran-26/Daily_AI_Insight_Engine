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
7. Check whether tests or validation checks cover the highest-risk behavior.
8. Produce findings ordered by severity.
9. For each finding, include a concrete fix or a documented reason to accept the risk.
10. Confirm that addressed findings are reflected in docs, tests, or code.

## Deliverables

- Review findings ordered by severity.
- Explicit pass/fail judgment for assignment alignment.
- List of required fixes before completion.
- List of accepted risks or known limitations.
- Final reviewer sign-off only after critical findings are resolved.
