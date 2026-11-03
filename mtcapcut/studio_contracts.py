"""Strict contracts for autonomous Studio Council reasoning."""

from dataclasses import asdict, dataclass
import json
from typing import Any
from uuid import uuid4

from .editorial_findings import (EditorialFinding, FindingCategory, FindingSeverity,
                                 ReleaseScope)


STUDIO_ROLES = (
    "intent_insight", "story_architect", "footage_curator",
    "rhythm_sound", "motion_graphics", "fact_ethics_critic",
)


@dataclass(frozen=True)
class StudioRecommendation:
    recommendation_id: str
    role: str
    recommendation: str
    confidence: float
    evidence: tuple[str, ...]
    risks: tuple[str, ...]
    alternatives: tuple[str, ...]
    objections: tuple[EditorialFinding, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StudioSynthesis:
    creative_direction: str
    premise: str
    audience_effect: str
    story_beats: tuple[str, ...]
    accepted_recommendation_ids: tuple[str, ...]
    unresolved_objections: tuple[str, ...]
    confidence: float
    risks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate[candidate.find("\n") + 1:candidate.rfind("```")].strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as error:
        raise ValueError("studio response is not valid JSON") from error
    if not isinstance(value, dict):
        raise ValueError("studio response must be a JSON object")
    return value


def _strings(value: Any, field: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValueError(f"{field} must be a {'possibly empty ' if allow_empty else 'nonempty '}string array")
    output = tuple(str(item).strip() for item in value)
    if any(not item for item in output):
        raise ValueError(f"{field} contains an empty value")
    return output


def _confidence(value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
        raise ValueError("confidence must be from 0 to 1")
    return float(value)


def _findings(value: Any, role: str, valid_evidence_ids: set[str]) -> tuple[EditorialFinding, ...]:
    if not isinstance(value, list):
        raise ValueError("objections must be an array")
    findings = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("objections must be typed objects")
        text = str(item.get("finding", "")).strip()
        if text.casefold().startswith(("no objection", "no explicit objection", "ไม่มีข้อคัดค้าน")):
            raise ValueError("absence of an objection is not an editorial finding")
        try:
            category = FindingCategory(item.get("category"))
            severity = FindingSeverity(item.get("severity"))
        except ValueError as error:
            raise ValueError("objection category or severity is invalid") from error
        evidence = _strings(item.get("evidence"), "objection evidence")
        if not set(evidence) <= valid_evidence_ids:
            raise ValueError("objection cites unknown evidence")
        scopes: tuple[ReleaseScope, ...] = ()
        if category == FindingCategory.RIGHTS:
            scopes = (ReleaseScope.PUBLICATION,)
        # Specialist findings are produced before a candidate exists. They are review requirements,
        # not proof that the eventual candidate violates them. Candidate validators create scoped
        # blockers after inspecting actual timeline content; pre-candidate rights findings still
        # block publication by policy.
        findings.append(EditorialFinding(
            str(uuid4()), role, category, severity, text, evidence,
            str(item.get("required_action", "")).strip(), str(item.get("owner_role", "")).strip(), scopes,
        ))
    return tuple(findings)


def parse_recommendation(text: str, expected_role: str,
                         valid_evidence_ids: set[str]) -> StudioRecommendation:
    if expected_role not in STUDIO_ROLES:
        raise ValueError("unknown studio role")
    value = _object(text)
    recommendation = str(value.get("recommendation", "")).strip()
    if not recommendation:
        raise ValueError("recommendation is required")
    evidence = _strings(value.get("evidence"), "evidence")
    if not set(evidence) <= valid_evidence_ids:
        raise ValueError("recommendation cites unknown evidence")
    return StudioRecommendation(
        str(uuid4()), expected_role, recommendation, _confidence(value.get("confidence")), evidence,
        _strings(value.get("risks"), "risks"), _strings(value.get("alternatives"), "alternatives"),
        _findings(value.get("objections", []), expected_role, valid_evidence_ids),
    )


def parse_synthesis(text: str, recommendation_ids: set[str],
                    required_objections: set[str]) -> StudioSynthesis:
    value = _object(text)
    fields = ("creative_direction", "premise", "audience_effect")
    strings = {field: str(value.get(field, "")).strip() for field in fields}
    if any(not item for item in strings.values()):
        raise ValueError("synthesis direction, premise and audience effect are required")
    accepted = _strings(value.get("accepted_recommendation_ids"), "accepted_recommendation_ids")
    if not set(accepted) <= recommendation_ids:
        raise ValueError("synthesis accepts an unknown recommendation")
    unresolved = _strings(value.get("unresolved_objections", []), "unresolved_objections", allow_empty=True)
    unresolved = tuple(dict.fromkeys((*unresolved, *sorted(required_objections))))
    return StudioSynthesis(
        strings["creative_direction"], strings["premise"], strings["audience_effect"],
        _strings(value.get("story_beats"), "story_beats"), accepted, unresolved,
        _confidence(value.get("confidence")), _strings(value.get("risks"), "risks"),
    )


def parse_timeline_candidate(text: str) -> dict[str, Any]:
    value = _object(text)
    if value.get("authorship") != "autonomous_studio":
        raise ValueError("candidate authorship must be autonomous_studio")
    for field in ("width", "height", "fps"):
        if not isinstance(value.get(field), int) or value[field] < 1:
            raise ValueError(f"candidate {field} must be a positive integer")
    segments = value.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("candidate segments must be nonempty")
    ids: set[str] = set()
    for segment in segments:
        if not isinstance(segment, dict):
            raise ValueError("candidate segment must be an object")
        segment_id = str(segment.get("segment_id", "")).strip()
        if not segment_id or segment_id in ids:
            raise ValueError("candidate segment IDs must be nonempty and unique")
        ids.add(segment_id)
        if segment.get("kind") not in {"video", "picture", "audio", "text"}:
            raise ValueError("candidate segment has unsupported kind")
        if not isinstance(segment.get("start_us"), int) or not isinstance(segment.get("duration_us"), int):
            raise ValueError("candidate segment times must be integers")
        if segment["start_us"] < 0 or segment["duration_us"] <= 0:
            raise ValueError("candidate segment has invalid time range")
        if not str(segment.get("track", "")).strip() or not str(segment.get("rationale", "")).strip():
            raise ValueError("candidate segment requires track and rationale")
        _strings(segment.get("evidence"), "segment evidence")
    return value

