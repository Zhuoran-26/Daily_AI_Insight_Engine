---
name: spec-driven-development
description: Use this skill before implementing any Daily AI Insight Engine feature to turn requirements into a concrete spec with scope, contracts, acceptance criteria, and review checkpoints.
---

# Spec-driven Development

## Purpose

Create a precise feature specification before implementation so later code, prompts, tests, and documentation are traceable to the assignment requirements.

## When To Use

Use this skill when:

- starting a new feature or pipeline stage
- changing a schema, prompt, report format, or validation rule
- deciding what belongs in MVP scope
- translating interview assignment requirements into engineering tasks

Do not use it to write business code directly. This skill produces specs and implementation instructions only.

## Workflow

1. Read `docs/project_spec_v1.md` and `AGENTS.md`.
2. State the feature objective in one sentence.
3. Define in-scope and out-of-scope behavior.
4. Identify inputs, outputs, and ownership boundaries.
5. Define structured contracts:
   - data fields
   - required versus optional fields
   - allowed values
   - validation rules
6. Define acceptance criteria that can be checked without subjective judgment.
7. List failure cases and how the system should respond.
8. Identify required review questions for an AI reviewer.
9. Identify required tests or validation checks.
10. Update the relevant project documentation before or alongside implementation.

## Deliverables

- A feature spec with objective, scope, non-goals, contracts, validation rules, and acceptance criteria.
- A short implementation checklist ordered by dependency.
- A review checklist focused on correctness, schema fit, and assignment alignment.
- A test checklist that names the expected validation cases.
