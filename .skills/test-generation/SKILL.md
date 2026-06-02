---
name: test-generation
description: Use this skill to design tests and validation checks for data schemas, extraction behavior, analysis logic, and report generation without relying on manual inspection alone.
---

# Test Generation

## Purpose

Turn specs and schemas into concrete validation cases so the project demonstrates self verification instead of trusting AI outputs by default.

## When To Use

Use this skill when:

- a feature spec defines acceptance criteria
- a schema or prompt changes
- extracted data must be validated
- trend analysis or report generation needs regression coverage
- a reviewer asks how behavior is verified

## Workflow

1. Read the feature spec and relevant schema.
2. Identify the highest-risk assumptions:
   - missing source fields
   - malformed dates
   - duplicate news items
   - unsupported languages
   - invalid enum values
   - hallucinated entities or claims
3. Map each acceptance criterion to at least one validation case.
4. Define positive cases that should pass.
5. Define negative cases that should fail or be quarantined.
6. Define edge cases that should not crash the pipeline.
7. Define snapshot or golden-output checks for stable report sections when appropriate.
8. Specify how test data should remain small, inspectable, and tied to source examples.
9. Document skipped tests and why they are lower priority.

## Deliverables

- Test plan grouped by pipeline stage.
- Validation matrix mapping requirements to cases.
- Minimal fixture design for raw news and structured events.
- Expected pass/fail behavior for each case.
- Notes on manual checks that remain necessary.
