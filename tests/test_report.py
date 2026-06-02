from daily_ai_insight.models import StructuredAIEvent
from daily_ai_insight.report import build_daily_report, build_topic_clusters, write_report


def test_report_markdown_is_generated(tmp_path):
    event = StructuredAIEvent(
        id="evt-001",
        title="OpenAI launches model update",
        source="OpenAI News",
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
        evidence="OpenAI News: OpenAI describes a model launch.",
        source_channel="official",
        source_language="en",
        selection_reason="官方渠道用于确认技术发布信息。",
        collected_at="2026-06-03",
        canonical_topic="openai-model-update",
        topic_role="primary_announcement",
        background="OpenAI 发布模型更新，企业可关注能力变化。",
        industry_impact="前沿模型能力更新可能推动企业 AI 应用。",
        trend_signal="模型能力升级仍是 AI 产业竞争的核心信号。",
        industry_risk="平台锁定、成本上升和生态依赖风险需要关注。",
        industry_opportunity="AI coding、智能客服和知识管理存在机会。",
        decision_hint="建议关注企业采用成本、生态合作和用户反馈变化。",
    )
    report = build_daily_report(
        [event],
        {
            "input_count": 1,
            "output_count": 1,
            "source_integrity_passed": True,
            "grounding_passed": True,
            "loop_guard_passed": True,
            "min_confidence": 0.5,
            "deterministic_baseline": True,
            "steps_used": 7,
            "max_processing_steps": 8,
        },
        report_date="2026-05-27",
    )

    path = write_report(report, tmp_path / "daily_report.md")
    text = path.read_text(encoding="utf-8")

    assert "数据来源概览" in text
    assert "热点聚类与多源覆盖" in text
    assert "今日主要热点 Top 3–5" in text
    assert "重点事件深度解读" in text
    assert "行业影响" in text
    assert "行业机会" in text
    assert "行业风险" in text
    assert "决策提示" in text
    assert "舆情监测与风险预警" in text
    assert "可视化结果说明" in text
    assert "Harness 校验摘要" in text
    assert "方法说明" in text
    assert "deterministic baseline" in text
    assert "OpenAI News" in text
    assert "https://openai.com/news/" in text
    assert "2026-05-20" in text
    assert "published_at" in text
    assert "collected_at" in text
    assert "社区源用于观察反馈和舆情，不作为事实主来源" in text
    assert "openai-model-update" in text
    assert "官方渠道用于确认技术发布信息" in text
    assert report.trend_signals
    assert report.risks_and_opportunities
    assert report.opportunity_signals
    assert report.topic_clusters


def test_topic_clusters_summarize_multisource_coverage():
    events = [
        StructuredAIEvent(
            id="evt-001",
            title="OpenAI launches model update",
            source="OpenAI News",
            url="https://openai.com/news/",
            published_at="2026-05-20",
            language="en",
            category="model",
            event_type="release",
            entities=["OpenAI"],
            impact_areas=["model_capabilities"],
            importance_score=8.0,
            confidence=0.7,
            summary="OpenAI describes a model launch.",
            evidence="OpenAI News: OpenAI describes a model launch.",
            source_channel="official",
            source_language="en",
            canonical_topic="openai-model-update",
            topic_role="primary_announcement",
        ),
        StructuredAIEvent(
            id="evt-002",
            title="Developers discuss OpenAI model update",
            source="Reddit",
            url="https://www.reddit.com/r/artificial/",
            published_at="2026-05-21",
            language="en",
            category="application",
            event_type="discussion",
            entities=["OpenAI"],
            impact_areas=["developer_experience"],
            importance_score=5.0,
            confidence=0.7,
            summary="Developers discuss model update experience.",
            evidence="Reddit: Developers discuss model update experience.",
            source_channel="social_media",
            source_language="en",
            canonical_topic="openai-model-update",
            topic_role="community_feedback",
        ),
    ]

    cluster = build_topic_clusters(events)[0]

    assert cluster.canonical_topic == "openai-model-update"
    assert cluster.source_count == 2
    assert cluster.has_official_source is True
    assert cluster.has_community_feedback is True


def test_report_industry_risks_do_not_include_system_risk_terms():
    event = StructuredAIEvent(
        id="evt-001",
        title="OpenAI launches model update",
        source="OpenAI News",
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
        evidence="OpenAI News: OpenAI describes a model launch.",
        industry_risk="平台锁定和成本上升需要关注。",
        industry_opportunity="模型 API 和开发者工具存在机会。",
    )
    report = build_daily_report(
        [event],
        {
            "input_count": 1,
            "output_count": 1,
            "source_integrity_passed": True,
            "schema_compliance_passed": True,
            "grounding_passed": True,
            "evidence_grounding_passed": True,
            "loop_guard_passed": True,
            "min_confidence": 0.5,
            "extractor_name": "rule",
        },
    )

    forbidden = ("LLM", "幻觉", "人工复核", "可信度", "Harness", "Schema")
    risk_text = "\n".join(report.risks_and_opportunities)
    assert not any(term in risk_text for term in forbidden)
