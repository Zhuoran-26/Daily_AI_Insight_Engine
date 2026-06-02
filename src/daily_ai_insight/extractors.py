"""Extractor strategies for deterministic and optional LLM-backed extraction."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from daily_ai_insight.errors import HarnessError, PipelineError, ValidationError
from daily_ai_insight.harness import PipelineHarness
from daily_ai_insight.llm_client import OpenAICompatibleClient
from daily_ai_insight.models import RawNewsItem, StructuredAIEvent
from daily_ai_insight.validate import validate_structured_events

MAJOR_ENTITIES = (
    "OpenAI",
    "Google",
    "Anthropic",
    "NVIDIA",
    "Meta",
    "Microsoft",
    "Amazon",
    "Apple",
    "Mistral",
    "Hugging Face",
)

IMPORTANCE_KEYWORDS = ("release", "launch", "benchmark", "funding", "regulation")
SUPPORTED_EXTRACTORS = ("rule", "mock-llm", "openai-compatible")
BUSINESS_ANALYSIS_BY_CATEGORY = {
    "model": {
        "industry_impact": "前沿模型能力更新可能推动企业 AI 应用、开发者工具和模型 API 生态升级。",
        "industry_opportunity": "模型能力提升带来 AI coding、智能客服、内容生成、知识管理等场景机会。",
        "industry_risk": "模型能力集中在头部厂商，可能带来平台锁定、成本上升和生态依赖风险。",
    },
    "agent": {
        "industry_impact": "Agent 和 workflow 类更新说明 AI 正在从单次问答走向多步骤任务执行。",
        "industry_opportunity": "企业流程自动化、研发助手、投研助手和运营自动化可能受益。",
        "industry_risk": "多步骤 Agent 容易出现误执行、权限控制和责任边界问题。",
    },
    "infrastructure": {
        "industry_impact": "云平台、算力和模型分发渠道会影响 AI 应用部署成本和可获得性。",
        "industry_opportunity": "AI infra、推理加速、云服务和企业级模型托管需求上升。",
        "industry_risk": "算力集中、供应链限制和云厂商绑定可能影响中小团队。",
    },
    "application": {
        "industry_impact": "应用层产品更新反映 AI 能力正在进入更具体的业务场景。",
        "industry_opportunity": "垂直行业 Copilot、知识助手、内容工具和办公自动化有增长空间。",
        "industry_risk": "同质化竞争、用户体验不稳定和合规要求可能限制落地。",
    },
}


class BaseExtractor(ABC):
    name: str

    @abstractmethod
    def extract(self, raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
        """Extract structured events from normalized raw news items."""


class RuleBasedExtractor(BaseExtractor):
    name = "rule"

    def extract(self, raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
        events: list[StructuredAIEvent] = []
        for index, item in enumerate(raw_items, start=1):
            category = classify_category(item)
            importance_score = score_importance(item)
            events.append(
                StructuredAIEvent(
                    id=f"evt-{index:03d}",
                    title=item.title,
                    source=item.source,
                    url=item.url,
                    published_at=item.published_at,
                    language=item.language,
                    category=category,
                    event_type=classify_event_type(item),
                    entities=extract_entities(item),
                    impact_areas=impact_areas_for_category(category),
                    importance_score=importance_score,
                    # Deterministic baseline confidence. Future LLM extractors
                    # may emit confidence, but harness checks still gate output.
                    confidence=0.7,
                    summary=item.summary,
                    evidence=f"{item.source}: {item.summary}",
                    source_channel=item.source_channel,
                    source_language=item.source_language,
                    selection_reason=item.selection_reason,
                    collected_at=item.collected_at,
                    **build_business_analysis(item, category, importance_score),
                )
            )
        return events


class MockLLMExtractor(BaseExtractor):
    """Test double for LLM extraction workflows.

    Modes intentionally simulate both valid and unsafe model behavior so tests
    can prove that schema validation, grounding, and confidence gates still run.
    """

    name = "mock-llm"

    def __init__(self, mode: str = "valid") -> None:
        allowed_modes = {"valid", "invalid", "hallucinated", "low-confidence"}
        if mode not in allowed_modes:
            raise PipelineError(f"Unsupported mock LLM mode: {mode}")
        self.mode = mode

    def extract(self, raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
        if self.mode == "invalid":
            return [{"not": "a structured event"}]  # type: ignore[return-value]

        events: list[StructuredAIEvent] = []
        for index, item in enumerate(raw_items, start=1):
            category = semantic_category(item)
            source = item.source
            url = item.url
            confidence = 0.82

            if self.mode == "hallucinated" and index == 1:
                source = "Invented AI Wire"
                url = "hallucinated://invented-source"
            if self.mode == "low-confidence" and index == 1:
                confidence = 0.3
            importance_score = score_importance(item)

            events.append(
                StructuredAIEvent(
                    id=f"mock-evt-{index:03d}",
                    title=item.title,
                    source=source,
                    url=url,
                    published_at=item.published_at,
                    language=item.language,
                    category=category,
                    event_type=classify_event_type(item),
                    entities=extract_entities(item),
                    impact_areas=impact_areas_for_category(category),
                    importance_score=importance_score,
                    confidence=confidence,
                    summary=item.summary,
                    evidence=f"{item.source}: {item.summary}",
                    source_channel=item.source_channel,
                    source_language=item.source_language,
                    selection_reason=item.selection_reason,
                    collected_at=item.collected_at,
                    **build_business_analysis(
                        item,
                        category,
                        importance_score,
                        llm_generated=True,
                        requires_human_review=confidence < 0.75,
                    ),
                )
            )
        return events


class OpenAICompatibleExtractor(BaseExtractor):
    """OpenAI-compatible extractor with item-level retry and harness checks."""

    name = "openai-compatible"

    def __init__(
        self,
        prompt_path: str | Path = "prompts/extraction_prompt.md",
        client: OpenAICompatibleClient | None = None,
        max_retries: int = 2,
    ) -> None:
        self.prompt_path = Path(prompt_path)
        self.client = client
        self.max_retries = max_retries

    def extract(self, raw_items: list[RawNewsItem]) -> list[StructuredAIEvent]:
        client = self.client or OpenAICompatibleClient.from_environment()
        prompt = self._load_prompt()
        events: list[StructuredAIEvent] = []

        for index, raw_item in enumerate(raw_items, start=1):
            events.append(self._extract_one_item(client, prompt, raw_item, index))
        return events

    def _extract_one_item(
        self,
        client: OpenAICompatibleClient,
        prompt: str,
        raw_item: RawNewsItem,
        index: int,
    ) -> StructuredAIEvent:
        feedback: str | None = None
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response_text = client.complete_extraction(
                    prompt=prompt,
                    raw_items=[raw_item],
                    feedback=feedback,
                )
                event = self._parse_and_validate_single_response(response_text, raw_item, index)
                self._run_single_llm_harness(event, raw_item)
                return event
            except (PipelineError, HarnessError, ValidationError) as exc:
                last_error = exc
                feedback = f"Attempt {attempt + 1} failed for item {index}: {exc}"

        raise PipelineError(
            "openai-compatible extractor failed for item "
            f"{index} '{raw_item.title}' after {self.max_retries + 1} attempts: {last_error}"
        ) from last_error

    def _load_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise PipelineError(f"Extraction prompt not found: {self.prompt_path}")
        return self.prompt_path.read_text(encoding="utf-8")

    def _parse_and_validate_single_response(
        self,
        response_text: str,
        raw_item: RawNewsItem,
        index: int,
    ) -> StructuredAIEvent:
        try:
            response = json.loads(self._strip_json_fence(response_text))
        except json.JSONDecodeError as exc:
            raise PipelineError(f"LLM output was not valid JSON: {exc}") from exc

        if isinstance(response, list):
            raise PipelineError("OpenAI-compatible item-level response must be one JSON object, not a list")
        if not isinstance(response, dict):
            raise PipelineError("OpenAI-compatible item-level response must be a JSON object")

        required_llm_analysis_fields = (
            "background",
            "industry_impact",
            "trend_signal",
            "industry_risk",
            "industry_opportunity",
            "decision_hint",
        )
        for field in required_llm_analysis_fields:
            if not str(response.get(field) or "").strip():
                raise PipelineError(f"OpenAI-compatible response missing required analysis field: {field}")

        confidence = response.get("confidence")
        if isinstance(response.get("requires_human_review"), bool):
            requires_human_review = response["requires_human_review"]
        elif isinstance(confidence, (int, float)):
            requires_human_review = confidence < 0.75
        else:
            requires_human_review = True

        event_payload = {
            "id": f"llm-evt-{index:03d}",
            "title": raw_item.title,
            "source": raw_item.source,
            "url": raw_item.url,
            "published_at": raw_item.published_at,
            "language": raw_item.language,
            "category": response.get("category"),
            "event_type": response.get("event_type"),
            "entities": response.get("entities"),
            "impact_areas": response.get("impact_areas"),
            "importance_score": response.get("importance_score"),
            "confidence": confidence,
            "summary": response.get("summary"),
            "evidence": response.get("evidence"),
            "source_channel": raw_item.source_channel,
            "source_language": raw_item.source_language,
            "selection_reason": raw_item.selection_reason,
            "collected_at": raw_item.collected_at,
            "background": response.get("background"),
            "industry_impact": response.get("industry_impact"),
            "trend_signal": response.get("trend_signal"),
            "industry_risk": response.get("industry_risk"),
            "industry_opportunity": response.get("industry_opportunity"),
            "decision_hint": response.get("decision_hint"),
            "llm_generated": True,
            "requires_human_review": requires_human_review,
        }

        try:
            return StructuredAIEvent.model_validate(event_payload)
        except PydanticValidationError as exc:
            raise PipelineError(
                f"OpenAI-compatible extractor response for item {index} failed schema validation: {exc}"
            ) from exc

    @staticmethod
    def _run_single_llm_harness(event: StructuredAIEvent, raw_item: RawNewsItem) -> None:
        validate_structured_events([event])
        harness = PipelineHarness()
        harness.check_schema_compliance([event])
        harness.check_single_event_grounding(event, raw_item)
        harness.check_single_evidence_grounding(event, raw_item)
        harness.check_confidence([event])

    @staticmethod
    def _strip_json_fence(response_text: str) -> str:
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return text


def create_extractor(extractor_name: str) -> BaseExtractor:
    if extractor_name == "rule":
        return RuleBasedExtractor()
    if extractor_name == "mock-llm":
        return MockLLMExtractor()
    if extractor_name == "openai-compatible":
        return OpenAICompatibleExtractor()
    raise PipelineError(f"Unsupported extractor: {extractor_name}")


def classify_category(item: RawNewsItem) -> str:
    text = _combined_text(item)
    if any(keyword in text for keyword in ("model", "llm", "gpt", "claude", "gemini")):
        return "model"
    if "agent" in text:
        return "agent"
    if any(keyword in text for keyword in ("chip", "gpu", "nvidia")):
        return "infrastructure"
    return "application"


def semantic_category(item: RawNewsItem) -> str:
    text = _combined_text(item)
    if any(keyword in text for keyword in ("chip", "gpu", "nvidia", "infrastructure", "blackwell", "graviton")):
        return "infrastructure"
    if any(keyword in text for keyword in ("agent", "agentic", "codex", "sdk", "mcp", "workflow")):
        return "agent"
    if any(keyword in text for keyword in ("app", "android", "accessibility", "finance", "advertising", "application")):
        return "application"
    if any(keyword in text for keyword in ("model", "llm", "gpt", "claude", "gemini")):
        return "model"
    return "application"


def classify_event_type(item: RawNewsItem) -> str:
    text = _combined_text(item)
    if any(keyword in text for keyword in ("release", "launch")):
        return "release"
    if "benchmark" in text:
        return "benchmark"
    if "funding" in text:
        return "funding"
    if "regulation" in text or "policy" in text:
        return "regulation"
    if "agent" in text:
        return "agent_update"
    return "application_update"


def extract_entities(item: RawNewsItem) -> list[str]:
    text = f"{item.title} {item.summary} {item.source}".lower()
    entities = [entity for entity in MAJOR_ENTITIES if entity.lower() in text]
    return entities or [item.source]


def impact_areas_for_category(category: str) -> list[str]:
    return {
        "model": ["model_capabilities"],
        "agent": ["automation"],
        "infrastructure": ["compute"],
        "application": ["productivity"],
    }[category]


def build_business_analysis(
    item: RawNewsItem,
    category: str,
    importance_score: float,
    *,
    llm_generated: bool = False,
    requires_human_review: bool = False,
) -> dict[str, str | bool]:
    template = BUSINESS_ANALYSIS_BY_CATEGORY[category]
    channel_label = source_channel_label(item.source_channel)
    language_label = source_language_label(item.source_language or item.language)
    importance_label = "高优先级" if importance_score >= 6.0 else "常规跟踪"
    background = (
        f"{item.source} 在 {item.published_at} 发布或讨论“{item.title}”。"
        f"该信息来自{channel_label}，{language_label}，摘要显示：{item.summary}"
    )
    trend_signal = trend_signal_for_category(category, channel_label, importance_label)
    decision_hint = decision_hint_for_category(category, item.source_channel, importance_label)
    return {
        "background": background,
        "industry_impact": template["industry_impact"],
        "trend_signal": trend_signal,
        "industry_risk": template["industry_risk"],
        "industry_opportunity": template["industry_opportunity"],
        "decision_hint": decision_hint,
        "llm_generated": llm_generated,
        "requires_human_review": requires_human_review,
    }


def source_channel_label(source_channel: str | None) -> str:
    return {
        "official": "官方渠道",
        "tech_media": "科技媒体",
        "aggregator": "聚合平台",
        "social_media": "社交/社区渠道",
    }.get(source_channel or "", "未标注渠道")


def source_language_label(source_language: str | None) -> str:
    return {
        "en": "英文来源",
        "zh": "中文来源",
    }.get(source_language or "", "未标注语言")


def trend_signal_for_category(category: str, channel_label: str, importance_label: str) -> str:
    category_signals = {
        "model": "模型能力升级仍是 AI 产业竞争的核心信号，后续需要持续观察能力、成本和调用生态变化。",
        "agent": "Agent 化和 workflow 化正在把 AI 从内容生成推向可执行任务，企业流程场景值得持续跟踪。",
        "infrastructure": "云与基础设施分发正在影响模型可获得性、部署成本和企业采购路径。",
        "application": "应用场景落地正在成为 AI 能力商业化的重要观察窗口。",
    }
    return f"{category_signals[category]}本事件来自{channel_label}，属于{importance_label}信息。"


def decision_hint_for_category(
    category: str,
    source_channel: str | None,
    importance_label: str,
) -> str:
    base_hints = {
        "model": "建议关注模型能力变化、API 成本、生态合作和开发者反馈。",
        "agent": "建议关注任务边界、权限控制、工作流集成成本和用户反馈变化。",
        "infrastructure": "建议关注云平台合作、部署成本、供应链稳定性和企业采购可行性。",
        "application": "建议关注目标用户、付费意愿、合规要求和真实使用留存。",
    }
    channel_hints = {
        "official": "官方信息适合用于确认发布时间、能力范围和合作关系。",
        "tech_media": "媒体报道适合用于补充行业解读、竞争态势和市场反馈。",
        "aggregator": "聚合平台适合用于快速判断传播热度和跨来源关注点。",
        "social_media": "社区讨论适合用于捕捉用户体验、成本敏感度和舆论波动。",
    }
    channel_hint = channel_hints.get(source_channel or "", "需要结合更多来源交叉验证。")
    return f"{base_hints[category]}{channel_hint}该事件当前可作为{importance_label}对象。"


def score_importance(item: RawNewsItem) -> float:
    text = _combined_text(item)
    score = 4.0
    if any(entity.lower() in text for entity in MAJOR_ENTITIES):
        score += 2.0
    score += sum(1.0 for keyword in IMPORTANCE_KEYWORDS if keyword in text)
    return min(10.0, round(score, 1))


def _combined_text(item: RawNewsItem) -> str:
    return f"{item.title} {item.summary}".lower()
