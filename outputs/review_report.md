# AI Reviewer Report

## Summary

- Final verdict: reviewed_with_warnings
- Total issues: 7
- Errors: 0
- Warnings: 1
- Info: 6

## Issues

| Severity | Area | Title | Suggested Action |
| --- | --- | --- | --- |
| info | schema | No failed evaluation items | Keep the current schema and harness checks in the evaluation path. |
| warning | category | Category mismatches detected | Review mismatched titles and update extractor rules, prompts, or expected fixture notes if justified. |
| info | grounding | Grounding pass rate is complete | Keep source and URL preservation mandatory for all extractor modes. |
| info | confidence | Average confidence meets threshold | Continue reporting confidence distribution alongside accuracy. |
| info | category | Extractor improves over baseline | Use this comparison in the showcase, while still explaining remaining mismatches. |
| info | report | Evaluation report exists | Use the report as the human-readable quality artifact. |
| info | report | Daily report exists | Use the daily report as the final generated artifact after validating evaluation results. |


## Details

### No failed evaluation items

- Severity: info
- Area: schema
- Detail: All 13 items produced valid evaluation results.
- Suggested action: Keep the current schema and harness checks in the evaluation path.

### Category mismatches detected

- Severity: warning
- Area: category
- Detail: 4 successful items were classified differently from the expected fixture.
- Suggested action: Review mismatched titles and update extractor rules, prompts, or expected fixture notes if justified.

### Grounding pass rate is complete

- Severity: info
- Area: grounding
- Detail: Every evaluated item passed source grounding checks.
- Suggested action: Keep source and URL preservation mandatory for all extractor modes.

### Average confidence meets threshold

- Severity: info
- Area: confidence
- Detail: Average confidence is 0.92, meeting the 0.70 threshold.
- Suggested action: Continue reporting confidence distribution alongside accuracy.

### Extractor improves over baseline

- Severity: info
- Area: category
- Detail: openai-compatible accuracy is 0.69; rule baseline accuracy is 0.38; delta is 0.31.
- Suggested action: Use this comparison in the showcase, while still explaining remaining mismatches.

### Evaluation report exists

- Severity: info
- Area: report
- Detail: Found evaluation report at outputs/llm_evaluation_report.md.
- Suggested action: Use the report as the human-readable quality artifact.

### Daily report exists

- Severity: info
- Area: report
- Detail: Found daily report at outputs/daily_report.md.
- Suggested action: Use the daily report as the final generated artifact after validating evaluation results.

## Methodology Note

This deterministic reviewer is a critique layer over evaluation artifacts. It does not replace harness validation, and it does not call an LLM. Its purpose is to surface mismatch patterns, failed items, confidence risks, missing artifacts, and baseline comparison signals so the next revise step can be deliberate.