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

## Phase 8.1 Mixed-channel Sample

Phase 8.1 adds `data/raw/mixed_channel_ai_news_sample.json` as the final showcase-oriented sample. It is manually curated from recent public AI information and is designed to better match the assignment scenarios:

- AI 行业趋势分析
- 舆情监测与风险预警
- 信息快速理解与决策辅助

The mixed sample includes English and Chinese sources across four channels:

| source_channel | Purpose |
|---|---|
| `official` | Company or product announcements used as primary source evidence. |
| `tech_media` | News coverage that adds reporting context and external framing. |
| `aggregator` | News aggregation or digest pages that show how events are summarized for fast scanning. |
| `social_media` | Public community discussions that expose user sentiment, cost concerns, adoption friction, or risk signals. |

Every mixed sample record keeps:

- `source`
- `url`
- `published_at`
- `source_channel`
- `source_language`
- `selection_reason`
- `collected_at`

`selection_reason` explains why the event matters for trend analysis, public-opinion monitoring, risk warning, or decision support. These provenance fields are raw input metadata. They are not generated or overwritten by the LLM.

The mixed sample is still a static product demo fixture. It does not claim to be a full real-time public-opinion collection system, and tests do not fetch live websites.

During Phase 8.1 source review, most mixed sample URLs were checked with `curl -L --head` or GET fallback. Some public community or official sites may reject automated curl requests even when the URL is a real public page. For example, OpenAI can return a Cloudflare challenge response, Hacker News rejects HEAD but serves GET/API checks, and V2EX reset curl connections from the local environment. These cases are treated as verification limitations and are not used as proof of source content beyond the recorded public URL and title/path review.

## Avoiding Hallucinated Sources

The project avoids hallucinated sources by requiring every real sample record to include:

- `source`
- `url`
- `title`
- `summary`
- `published_at`
- `language`

For the mixed sample, records must also include:

- `source_channel`
- `source_language`
- `selection_reason`
- `collected_at`

Records are excluded if the source URL cannot be confirmed. The harness also rejects suspicious source URLs such as `fake://`, `hallucinated://`, or `example.com/unknown`, and every structured event must be grounded in an existing raw record's title, source, and URL.

English sources can enter the system, but user-facing analysis should be Chinese. Schema keys, category enums, and extractor names remain English for compatibility and reproducibility.

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
