---
name: structured-output
description: Use this skill when designing, validating, or reviewing structured AI outputs such as RawNewsItem, StructuredAIEvent, or DailyInsightReport records.
---

# Structured Output

## Purpose

Ensure AI-generated outputs are machine-checkable, consistent, and usable by later pipeline stages instead of being loose prose summaries.

## When To Use

Use this skill when:

- designing or revising schemas
- extracting events from raw news
- generating analysis inputs for trend detection
- producing report data that needs validation
- reviewing whether an output is structured enough for downstream use

## Workflow

1. Identify the pipeline stage that owns the output.
2. Select the target schema from `docs/project_spec_v1.md` or propose a documented schema update.
3. For each field, define:
   - data type
   - whether it is required
   - valid value range or enum
   - source of truth
   - fallback behavior when data is missing
4. Separate extracted facts from model interpretation.
5. Include provenance fields that connect structured records to raw input items.
6. Preserve source grounding fields for every event:
   - source name
   - source URL when available
   - raw item IDs
   - evidence references
7. Define confidence or evidence fields for model-derived claims.
8. Run schema validation before passing any structured output downstream.
9. Reject model-generated source names or URLs that do not exist in the raw source data.
10. Compare confidence against the configured threshold.
11. Send low-confidence records to review, deterministic fallback, or fail-fast handling.
12. Reject, repair, or quarantine records that fail validation.
13. Record validation failures in a reviewable format.

## Deliverables

- Schema definition or schema change proposal.
- Field-level validation checklist.
- Example valid record and example invalid record when useful.
- Notes on provenance, confidence, and repair behavior.
- Validation result summary for generated structured data.
- Harness check summary for schema validation, source grounding, hallucinated source or URL detection, and confidence threshold handling.
