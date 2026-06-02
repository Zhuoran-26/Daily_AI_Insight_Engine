import importlib
from pathlib import Path

from daily_ai_insight import evaluate, pipeline, reviewer


def test_app_imports_without_starting_streamlit_server():
    app = importlib.import_module("app")

    assert callable(app.main)


def test_ui_reuses_existing_pipeline_evaluate_and_reviewer_functions():
    app = importlib.import_module("app")

    assert app.run_pipeline is pipeline.run_pipeline
    assert app.run_evaluation is evaluate.run_evaluation
    assert app.run_review is reviewer.run_review


def test_ui_detects_bundled_real_sample():
    app = importlib.import_module("app")

    assert app.is_bundled_real_sample(Path("data/raw/real_ai_news_sample.json"))
    assert not app.is_bundled_real_sample(Path("data/raw/sample_ai_news.json"))


def test_ui_openai_key_helper_handles_missing_key(monkeypatch):
    app = importlib.import_module("app")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    assert app.is_openai_key_configured() is False
