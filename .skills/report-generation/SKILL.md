---
name: report-generation
description: Use this skill when designing or reviewing the AI analysis daily report structure, evidence flow, trend sections, and human-readable output requirements.
---

# Report Generation

## Purpose

Design report outputs that are readable for humans while staying grounded in validated structured data and traceable analysis logic.

## When To Use

Use this skill when:

- defining the DailyInsightReport schema
- drafting the daily AI insight report format
- reviewing report completeness
- connecting visual summaries to structured events
- documenting how analysis claims are supported

## Workflow

1. Read `docs/project_spec_v1.md` and the validated event schema.
2. Define the report audience and decision purpose.
3. Build report sections from structured inputs:
   - top AI hotspots
   - key event deep dives
   - trend judgments
   - risks and opportunities
   - source and validation notes
4. For each claim, require supporting event IDs or source references.
5. Separate factual summaries from analytical judgments.
6. Define how confidence, uncertainty, and missing data are shown.
7. Ensure visualizations answer a specific report question rather than decorating the report.
8. Review whether the report can be regenerated from the same structured inputs.
9. Document any human edits or overrides.

## Deliverables

- Report outline with required sections.
- Field design for `DailyInsightReport`.
- Evidence mapping from report claims to structured events.
- Visualization requirements tied to report questions.
- Review checklist for readability, grounding, and completeness.
