import importlib
from pathlib import Path

from daily_ai_insight import evaluate, pipeline, reviewer
from daily_ai_insight.models import DailyInsightReport, StructuredAIEvent, TopicClusterSummary


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


def test_ui_defaults_to_mixed_sample_paths():
    app = importlib.import_module("app")

    assert app.MIXED_SAMPLE_PATH == Path("data/raw/mixed_channel_ai_news_sample.json")
    assert app.EXPECTED_MIXED_SAMPLE_PATH == Path("data/eval/expected_mixed_sample_categories.json")
    assert app.is_bundled_mixed_sample(Path("data/raw/mixed_channel_ai_news_sample.json"))
    assert app.expected_fixture_for_input(Path("data/raw/mixed_channel_ai_news_sample.json")) == app.EXPECTED_MIXED_SAMPLE_PATH
    assert app.expected_fixture_for_input(Path("data/raw/real_ai_news_sample.json")) == app.EXPECTED_REAL_SAMPLE_PATH
    assert app.expected_fixture_for_input(Path("custom.json")) is None


def test_ui_openai_key_helper_handles_missing_key(monkeypatch):
    app = importlib.import_module("app")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    assert app.is_openai_key_configured() is False


def test_ui_pipeline_chart_helpers_use_report_data():
    app = importlib.import_module("app")
    event = StructuredAIEvent(
        id="evt-001",
        title="OpenAI launches model update",
        source="OpenAI",
        url="https://openai.com/news/",
        published_at="2026-05-20",
        language="en",
        category="model",
        event_type="release",
        entities=["OpenAI"],
        impact_areas=["model_capabilities"],
        importance_score=7.0,
        confidence=0.7,
        summary="OpenAI describes a model launch.",
        evidence="OpenAI: OpenAI describes a model launch.",
        source_channel="official",
        source_language="en",
        canonical_topic="openai-model-update",
        topic_role="primary_announcement",
        industry_impact="模型更新影响企业应用。",
        industry_opportunity="AI coding 存在机会。",
        industry_risk="平台锁定风险需要关注。",
    )
    report = DailyInsightReport(
        date="2026-06-02",
        total_events=1,
        events=[event],
        top_events=[event],
        category_counts={"model": 1},
        source_channel_counts={"official": 1},
        source_language_counts={"en": 1},
        topic_clusters=[
            TopicClusterSummary(
                canonical_topic="openai-model-update",
                source_count=1,
                source_channels=["官方渠道"],
                source_languages=["英文来源"],
                representative_title="OpenAI launches model update",
                representative_sources=["OpenAI"],
                has_official_source=True,
                has_community_feedback=False,
            )
        ],
        key_takeaways=["model leads the sample."],
        trend_signals=["model momentum is visible."],
        risks_and_opportunities=["Opportunity: model launch."],
        harness_summary={
            "input_count": 1,
            "output_count": 1,
            "extractor_name": "rule",
            "source_integrity_passed": True,
            "schema_compliance_passed": True,
            "grounding_passed": True,
            "evidence_grounding_passed": True,
            "loop_guard_passed": True,
            "min_confidence": 0.5,
        },
    )

    assert app.category_label("model") == "模型能力"
    assert app.source_channel_label("official") == "官方渠道"
    assert app.source_language_label("en") == "英文"
    assert app.category_distribution_chart_data(report) == [{"分类": "模型能力", "数量": 1}]
    assert app.top_events_importance_chart_data(report) == [
        {"标题": "OpenAI launches model update", "重要性评分": 7.0}
    ]
    assert {"来源渠道": "官方渠道", "来源语言": "英文", "数量": 1} in app.source_coverage_matrix_data(report)
    assert app.event_timeline_chart_data(report) == [{"发布日期": "2026-05-20", "事件数": 1}]
    assert app.importance_confidence_scatter_data(report)[0]["分类"] == "模型能力"
    assert app.impact_area_distribution_chart_data(report) == [
        {"影响领域": "model_capabilities", "事件数": 1}
    ]
    assert app.topic_cluster_table(report) == [
        {
            "canonical_topic": "openai-model-update",
            "覆盖来源数量": 1,
            "覆盖渠道": "官方渠道",
            "覆盖语言": "英文来源",
            "代表标题": "OpenAI launches model update",
            "包含官方来源": "是",
            "包含社区反馈": "否",
        }
    ]
    assert app.harness_checklist_table(report)[0] == {"检查项": "输入数量检查", "结果": "通过"}

    for chart in (
        app.source_coverage_matrix_chart(report),
        app.event_timeline_chart(report),
        app.category_distribution_chart(report),
        app.importance_confidence_scatter_chart(report),
        app.impact_area_distribution_chart(report),
    ):
        assert chart.to_dict()


def test_ui_business_event_table_uses_chinese_friendly_columns():
    app = importlib.import_module("app")

    table = app.structured_events_business_table(
        [
            {
                "title": "OpenAI launches model update",
                "source": "OpenAI",
                "published_at": "2026-05-20",
                "source_channel": "official",
                "category": "model",
                "event_type": "release",
                "importance_score": 7.0,
                "confidence": 0.7,
                "summary": "中文摘要",
                "industry_impact": "行业影响",
                "industry_opportunity": "行业机会",
                "industry_risk": "行业风险",
                "url": "https://openai.com/news/",
            }
        ]
    )

    assert table == [
        {
            "标题": "OpenAI launches model update",
            "来源": "OpenAI",
            "发布日期": "2026-05-20",
            "来源渠道": "官方渠道",
            "分类": "模型能力",
            "事件类型": "release",
            "重要性": 7.0,
            "置信度": 0.7,
            "中文摘要": "中文摘要",
            "行业影响": "行业影响",
            "行业机会": "行业机会",
            "行业风险": "行业风险",
            "URL": "https://openai.com/news/",
        }
    ]


def test_ui_source_provenance_table_for_mixed_sample():
    app = importlib.import_module("app")

    rows = app.source_provenance_table(app.MIXED_SAMPLE_PATH)

    assert rows
    assert {"标题", "来源", "URL", "发布日期", "来源渠道", "来源语言", "选择理由", "采集日期"} == set(rows[0])
    assert {row["来源语言"] for row in rows} == {"英文", "中文"}
    assert "官方渠道" in {row["来源渠道"] for row in rows}


def test_ui_extractor_accuracy_comparison_handles_missing_files(tmp_path):
    app = importlib.import_module("app")

    assert app.extractor_accuracy_comparison_chart_data(
        rule_path=tmp_path / "missing_rule.json",
        llm_path=tmp_path / "missing_llm.json",
    ) == []
