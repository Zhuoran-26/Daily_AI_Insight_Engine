# Data Source Notes

## Why Phase 2 Used Synthetic Fixture Data

Phase 2 used `data/raw/sample_ai_news.json` as a synthetic fixture so the pipeline could be developed with stable, reproducible inputs. The goal was to validate schema design, harness behavior, deterministic extraction, report generation, and automated tests without depending on changing websites or network access.

The synthetic fixture is still useful for regression tests because its records are intentionally small, predictable, and controlled.

## Why Phase 3 Adds Real-world Sample Data

Phase 3 adds `data/raw/real_ai_news_sample.json` so the project no longer looks like a toy pipeline that only works on fabricated examples. The real-world sample is manually curated from public sources and is intended for interview demonstration, qualitative review, and deterministic baseline evaluation.

The real-world sample remains a local fixture. Tests do not fetch live websites.

## Current Source Types

The current real-world sample uses public sources from:

- official AI company blogs and news pages
- official developer blogs
- official infrastructure vendor blogs
- official product announcement pages

These sources were chosen because they are traceable, stable enough for a local fixture, and closely aligned with the assignment's AI industry monitoring goal.

## Avoiding Hallucinated Sources

The project avoids hallucinated sources by requiring every real sample record to include:

- `source`
- `url`
- `title`
- `summary`
- `published_at`
- `language`

Records are excluded if the source URL cannot be confirmed. The harness also rejects suspicious source URLs such as `fake://`, `hallucinated://`, or `example.com/unknown`, and every structured event must be grounded in an existing raw record's title, source, and URL.

## Why There Is No Complex Crawler Yet

The project intentionally avoids a crawler in this phase. A crawler would add changing network behavior, parsing edge cases, rate-limit concerns, source-specific logic, and test instability before the core harnessed pipeline is mature.

Manual curation is enough for Phase 3 because the goal is to demonstrate real inputs while preserving repeatable tests and deterministic outputs.

## Future Collector Upgrade Path

A future collector can be added behind the same harness controls:

- RSS or official API ingestion for known sources
- source allowlist and URL validation
- deduplication by canonical URL and title
- raw snapshot storage for reproducibility
- schema validation before extraction
- deterministic fallback when a source cannot be fetched or parsed

Collector output should still become `RawNewsItem` records before any extractor or reporter stage uses it.
