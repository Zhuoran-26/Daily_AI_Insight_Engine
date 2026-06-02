import json
from pathlib import Path

from daily_ai_insight.normalize import load_raw_news


SAMPLE_PATH = Path("data/raw/sample_ai_news.json")


def test_loads_sample_ai_news():
    items = load_raw_news(SAMPLE_PATH)
    assert len(items) == 12
    assert all(item.title for item in items)
    assert all(item.url for item in items)


def test_skips_empty_title_or_summary(tmp_path):
    payload = {
        "items": [
            {
                "title": "  ",
                "summary": "valid summary",
                "source": "Source",
                "url": "https://source.example/",
                "published_at": "2026-05-20",
                "language": "en",
            },
            {
                "title": "Valid title",
                "summary": "",
                "source": "Source",
                "url": "https://source.example/",
                "published_at": "2026-05-20",
                "language": "en",
            },
            {
                "title": " Valid title ",
                "summary": " Valid summary ",
                "source": " Source ",
                "url": " https://source.example/ ",
                "published_at": "2026-05-20",
                "language": "en",
            },
        ]
    }
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    items = load_raw_news(path)

    assert len(items) == 1
    assert items[0].title == "Valid title"
    assert items[0].summary == "Valid summary"


def test_language_defaults_unknown(tmp_path):
    payload = {
        "items": [
            {
                "title": "Valid title",
                "summary": "Valid summary",
                "source": "Source",
                "url": "https://source.example/",
                "published_at": "2026-05-20",
                "language": "  ",
            }
        ]
    }
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    items = load_raw_news(path)

    assert items[0].language == "unknown"


def test_missing_optional_provenance_defaults_to_none():
    items = load_raw_news(SAMPLE_PATH)

    assert items[0].source_channel is None
    assert items[0].source_language is None
    assert items[0].selection_reason is None
    assert items[0].collected_at is None
    assert items[0].canonical_topic is None
    assert items[0].topic_role is None


def test_preserves_topic_provenance_fields(tmp_path):
    payload = {
        "items": [
            {
                "title": "Valid title",
                "summary": "Valid summary",
                "source": "Source",
                "url": "https://source.example/",
                "published_at": "2026-05-20",
                "language": "en",
                "source_channel": "official",
                "source_language": "en",
                "selection_reason": "官方渠道用于确认技术发布事实。",
                "collected_at": "2026-06-03",
                "canonical_topic": "source-topic",
                "topic_role": "primary_announcement",
            }
        ]
    }
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    item = load_raw_news(path)[0]

    assert item.canonical_topic == "source-topic"
    assert item.topic_role == "primary_announcement"
