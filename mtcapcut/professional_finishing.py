"""Provider-authored professional finishing decisions for pyCapCut drafts."""

from dataclasses import asdict, dataclass
import json
from typing import Any

from .ai_provider import ChatMessage, ChatRequest, OpenAICompatibleProvider


TRANSITIONS = ("none", "Flash", "Light_Leaks", "Swipe_Left", "Zoom_Transition")
FILTERS = ("none", "Enhance", "Cinematic_Dusk", "Soft_Light", "Vivid")
MOTIONS = ("locked", "slow_push_in", "slow_pull_out")
TEXT_INTROS = ("none", "Wiping_In", "Golden_Dust", "Slanted_Expand")
TEXT_OUTROS = ("none", "Wiping_Out")


@dataclass(frozen=True)
class VisualFinish:
    segment_id: str
    transition: str
    transition_duration_us: int
    filter: str
    filter_intensity: float
    motion: str
    rationale: str


@dataclass(frozen=True)
class TextFinish:
    segment_id: str
    intro: str
    outro: str
    rationale: str


@dataclass(frozen=True)
class ProfessionalFinishingPlan:
    schema: str
    authorship: str
    visual_finishes: tuple[VisualFinish, ...]
    text_finishes: tuple[TextFinish, ...]
    creative_rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any], candidate: dict[str, Any]) -> "ProfessionalFinishingPlan":
        if value.get("schema") != "mtcapcut.finishing.v1" or value.get("authorship") != "autonomous_studio":
            raise ValueError("invalid professional finishing identity")
        visual_ids = {item["segment_id"] for item in candidate["segments"]
                      if item["kind"] in {"video", "picture"}}
        text_ids = {item["segment_id"] for item in candidate["segments"] if item["kind"] == "text"}
        visuals = []
        seen = set()
        for item in value.get("visual_finishes", []):
            segment_id = str(item.get("segment_id", ""))
            if segment_id not in visual_ids or segment_id in seen:
                raise ValueError("finishing plan has unknown or duplicate visual segment")
            seen.add(segment_id)
            transition = str(item.get("transition"))
            filter_name = str(item.get("filter"))
            motion = str(item.get("motion"))
            duration = item.get("transition_duration_us")
            intensity = item.get("filter_intensity")
            rationale = str(item.get("rationale", "")).strip()
            if transition not in TRANSITIONS or filter_name not in FILTERS or motion not in MOTIONS:
                raise ValueError("finishing plan uses an unsupported visual treatment")
            if not isinstance(duration, int) or not 0 <= duration <= 800_000:
                raise ValueError("transition duration must be from 0 to 800000 microseconds")
            if transition == "none" and duration != 0:
                raise ValueError("a none transition must have zero duration")
            if transition != "none" and duration < 200_000:
                raise ValueError("a transition must be at least 200000 microseconds")
            if not isinstance(intensity, (int, float)) or isinstance(intensity, bool) or not 0 <= intensity <= 100:
                raise ValueError("filter intensity must be from 0 to 100")
            if filter_name != "none" and not 10 <= intensity <= 45:
                raise ValueError("a professional filter must use a restrained 10-45 percent intensity")
            if filter_name == "none" and intensity != 0:
                raise ValueError("a none filter must have zero intensity")
            if not rationale:
                raise ValueError("visual finishing rationale is required")
            visuals.append(VisualFinish(segment_id, transition, duration, filter_name,
                                        float(intensity), motion, rationale))
        if seen != visual_ids:
            raise ValueError("finishing plan must cover every visual segment")
        if len(visual_ids) > 1 and not any(item.transition != "none" for item in visuals[:-1]):
            raise ValueError("multi-visual professional finishing requires at least one intentional transition")
        texts = []
        seen = set()
        for item in value.get("text_finishes", []):
            segment_id = str(item.get("segment_id", ""))
            intro, outro = str(item.get("intro")), str(item.get("outro"))
            rationale = str(item.get("rationale", "")).strip()
            if segment_id not in text_ids or segment_id in seen or intro not in TEXT_INTROS or outro not in TEXT_OUTROS:
                raise ValueError("finishing plan has an invalid text treatment")
            if not rationale:
                raise ValueError("text finishing rationale is required")
            seen.add(segment_id)
            texts.append(TextFinish(segment_id, intro, outro, rationale))
        if seen != text_ids:
            raise ValueError("finishing plan must cover every text segment")
        rationale = str(value.get("creative_rationale", "")).strip()
        if not rationale:
            raise ValueError("creative finishing rationale is required")
        return cls("mtcapcut.finishing.v1", "autonomous_studio", tuple(visuals), tuple(texts), rationale)


def _response_format() -> dict[str, Any]:
    visual = {"type":"object","additionalProperties":False,"properties":{
        "segment_id":{"type":"string"}, "transition":{"type":"string","enum":list(TRANSITIONS)},
        "transition_duration_us":{"type":"integer","minimum":0,"maximum":800000},
        "filter":{"type":"string","enum":list(FILTERS)},
        "filter_intensity":{"type":"number","minimum":0,"maximum":45},
        "motion":{"type":"string","enum":list(MOTIONS)}, "rationale":{"type":"string"}},
        "required":["segment_id","transition","transition_duration_us","filter","filter_intensity","motion","rationale"]}
    text = {"type":"object","additionalProperties":False,"properties":{
        "segment_id":{"type":"string"},"intro":{"type":"string","enum":list(TEXT_INTROS)},
        "outro":{"type":"string","enum":list(TEXT_OUTROS)},"rationale":{"type":"string"}},
        "required":["segment_id","intro","outro","rationale"]}
    schema = {"type":"object","additionalProperties":False,"properties":{
        "schema":{"type":"string","enum":["mtcapcut.finishing.v1"]},
        "authorship":{"type":"string","enum":["autonomous_studio"]},
        "visual_finishes":{"type":"array","items":visual},
        "text_finishes":{"type":"array","items":text},"creative_rationale":{"type":"string"}},
        "required":["schema","authorship","visual_finishes","text_finishes","creative_rationale"]}
    return {"type":"json_schema","json_schema":{"name":"mtcapcut_professional_finishing","strict":True,"schema":schema}}


class ProfessionalFinishingEngine:
    def __init__(self, provider: OpenAICompatibleProvider):
        self.provider = provider

    def design(self, candidate: dict[str, Any]) -> ProfessionalFinishingPlan:
        safe_segments = [{key:item.get(key) for key in
            ("segment_id", "kind", "start_us", "duration_us", "track", "rationale")}
            for item in candidate["segments"]]
        response = self.provider.complete(ChatRequest(messages=(
            ChatMessage("system", "You are MTCapcut Senior Finishing Editor. Design restrained, intentional professional finishing for a factual leadership profile. When there are two or more visual segments, use at least one non-none transition on a non-final visual so the review demonstrates transition craft, but use transitions sparingly. Filter intensity is a percentage: use 10-45 for a selected filter and exactly 0 for none. Avoid novelty effects, use motion only where it supports dignity, and give a concrete rationale for every decision. Do not change edit timing, facts, text, assets, or music. Return strict JSON only."),
            ChatMessage("user", json.dumps({"segments":safe_segments,
                "creative_direction":candidate.get("project_brief"),
                "allowed_transitions":TRANSITIONS,"allowed_filters":FILTERS,
                "allowed_motion":MOTIONS,"allowed_text_intros":TEXT_INTROS,
                "allowed_text_outros":TEXT_OUTROS}, ensure_ascii=False, sort_keys=True)),
        ), temperature=0.15, max_tokens=3000, response_format=_response_format()))
        candidate_text = response.text
        for attempt in range(3):
            try:
                value = json.loads(candidate_text)
                if not isinstance(value, dict):
                    raise ValueError("professional finishing response must be an object")
                return ProfessionalFinishingPlan.from_dict(value, candidate)
            except (json.JSONDecodeError, ValueError) as error:
                if attempt == 2:
                    if isinstance(error, json.JSONDecodeError):
                        raise ValueError("professional finishing response is not valid JSON") from error
                    raise
                repaired = self.provider.complete(ChatRequest(messages=(
                    ChatMessage("system", "You are the MTCapcut professional-finishing contract repair step. Correct only the validator finding. Preserve the editorial intent, cover every segment exactly once, use at least one intentional transition for multiple visuals, and use filter intensity 10-45 percent or zero when filter is none. Return complete strict JSON only."),
                    ChatMessage("user", json.dumps({"validation_error":str(error),
                        "invalid_response":candidate_text}, ensure_ascii=False, sort_keys=True)),
                ), temperature=0.0, max_tokens=3000, response_format=_response_format()))
                candidate_text = repaired.text
        raise RuntimeError("professional finishing repair loop ended unexpectedly")
