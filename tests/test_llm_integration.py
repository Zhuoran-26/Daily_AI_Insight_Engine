import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from daily_ai_insight.pipeline import run_pipeline

REAL_SAMPLE_PATH = Path("data/raw/real_ai_news_sample.json").resolve()
load_dotenv()


@pytest.mark.skipif(
    os.getenv("RUN_LLM_INTEGRATION") != "1" or not os.getenv("OPENAI_API_KEY"),
    reason="Set RUN_LLM_INTEGRATION=1 and OPENAI_API_KEY to call the real LLM API.",
)
def test_openai_compatible_real_llm_pipeline(tmp_path):
    report = run_pipeline(
        REAL_SAMPLE_PATH,
        extractor_name="openai-compatible",
        events_output_path=tmp_path / "events.json",
        report_output_path=tmp_path / "report.md",
    )

    assert report.total_events > 0
    assert report.harness_summary["extractor_name"] == "openai-compatible"
    assert report.harness_summary["schema_compliance_passed"] is True
    assert report.harness_summary["grounding_passed"] is True
    assert report.harness_summary["evidence_grounding_passed"] is True
