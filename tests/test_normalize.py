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
