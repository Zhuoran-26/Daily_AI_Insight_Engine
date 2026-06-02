import json
from pathlib import Path

ALLOWED_CATEGORIES = {"model", "agent", "infrastructure", "application"}
REAL_SAMPLE_PATH = Path("data/raw/real_ai_news_sample.json")
EVAL_FIXTURE_PATH = Path("data/eval/expected_real_sample_categories.json")


def test_expected_real_sample_categories_fixture_exists():
    assert EVAL_FIXTURE_PATH.exists()


def test_expected_categories_are_allowed_and_titles_exist():
    real_payload = json.loads(REAL_SAMPLE_PATH.read_text(encoding="utf-8"))
    eval_payload = json.loads(EVAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    real_titles = {item["title"] for item in real_payload["items"]}

    assert eval_payload
    for item in eval_payload:
        assert item["expected_category"] in ALLOWED_CATEGORIES
        assert item["title"] in real_titles
        assert item["reason"]
