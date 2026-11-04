"""Provider-interpreted typed brief and deterministic compliance checks."""

from dataclasses import asdict, dataclass, replace
from pathlib import Path
import json
import re
from typing import Any
from uuid import uuid4

from .ai_provider import ChatMessage, ChatRequest, OpenAICompatibleProvider
from .editorial_findings import EditorialFinding, FindingCategory, FindingSeverity, ReleaseScope
from .studio_snapshot import StudioInputSnapshot


@dataclass(frozen=True)
class ProjectBrief:
    schema_version: str
    duration_min_us: int
    duration_max_us: int
    width: int
    height: int
    delivery_scope: str
    audience: str
    tone: tuple[str, ...]
    story_beats: tuple[str, ...]
    required_messages: tuple[str, ...]
    required_asset_roles: tuple[str, ...]
    required_asset_names: tuple[str, ...]
    forbidden_asset_names: tuple[str, ...]
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "1":
            raise ValueError("unsupported project brief schema")
        if not 0 < self.duration_min_us <= self.duration_max_us:
            raise ValueError("invalid brief duration range")
        if self.width < 1 or self.height < 1:
            raise ValueError("invalid brief frame size")
        if self.delivery_scope not in {"private_preview", "publication"}:
            raise ValueError("invalid brief delivery scope")
        if not self.audience.strip() or not self.evidence:
            raise ValueError("brief audience and evidence are required")

    @property
    def publication_allowed(self) -> bool:
        return self.delivery_scope == "publication"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any], valid_evidence_ids: set[str],
                  valid_asset_roles: set[str] | None = None) -> "ProjectBrief":
        required = {
            "schema_version", "duration_min_us", "duration_max_us", "width", "height",
            "delivery_scope", "audience", "tone", "story_beats", "required_messages",
            "required_asset_roles", "required_asset_names", "forbidden_asset_names", "evidence",
        }
        if set(value) != required:
            raise ValueError("project brief fields do not match the contract")
        arrays = {}
        for field in required - {"schema_version", "duration_min_us", "duration_max_us", "width",
                                 "height", "delivery_scope", "audience"}:
            items = value[field]
            if not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items):
                raise ValueError(f"project brief {field} must be a string array")
            arrays[field] = tuple(item.strip() for item in items)
        if not set(arrays["evidence"]) <= valid_evidence_ids:
            raise ValueError("project brief cites unknown authority evidence")
        if valid_asset_roles is not None and not set(arrays["required_asset_roles"]) <= valid_asset_roles:
            unknown = sorted(set(arrays["required_asset_roles"]) - valid_asset_roles)
            raise ValueError(f"project brief uses unknown required asset roles: {unknown}")
        integer_fields = ("duration_min_us", "duration_max_us", "width", "height")
        if any(not isinstance(value[item], int) or isinstance(value[item], bool) for item in integer_fields):
            raise ValueError("project brief numeric fields must be integers")
        return cls(str(value["schema_version"]), value["duration_min_us"], value["duration_max_us"],
                   value["width"], value["height"], str(value["delivery_scope"]),
                   str(value["audience"]), arrays["tone"], arrays["story_beats"],
                   arrays["required_messages"], arrays["required_asset_roles"],
                   arrays["required_asset_names"], arrays["forbidden_asset_names"], arrays["evidence"])


def _brief_response_format() -> dict[str, Any]:
    array = {"type": "array", "items": {"type": "string"}}
    return {"type": "json_schema", "json_schema": {"name": "mtcapcut_project_brief", "strict": True,
        "schema": {"type": "object", "additionalProperties": False, "properties": {
            "schema_version": {"type": "string", "enum": ["1"]},
            "duration_min_us": {"type": "integer", "minimum": 1},
            "duration_max_us": {"type": "integer", "minimum": 1},
            "width": {"type": "integer", "minimum": 1}, "height": {"type": "integer", "minimum": 1},
            "delivery_scope": {"type": "string", "enum": ["private_preview", "publication"]},
            "audience": {"type": "string"}, "tone": array, "story_beats": array,
            "required_messages": array, "required_asset_roles": array,
            "required_asset_names": array, "forbidden_asset_names": array,
            "evidence": {**array, "minItems": 1},
        }, "required": ["schema_version", "duration_min_us", "duration_max_us", "width", "height",
            "delivery_scope", "audience", "tone", "story_beats", "required_messages",
            "required_asset_roles", "required_asset_names", "forbidden_asset_names", "evidence"]}}}


class BriefInterpreterEngine:
    def __init__(self, provider: OpenAICompatibleProvider):
        self.provider = provider

    def interpret(self, snapshot: StudioInputSnapshot) -> ProjectBrief:
        authority = [item for item in snapshot.document["observations"] if item.get("modality") == "text"]
        if not authority:
            raise ValueError("brief interpretation requires authority text observations")
        request = ChatRequest(messages=(
            ChatMessage("system", "You are the MTCapcut Brief Interpreter. Convert only the supplied authority observations into the strict typed contract. Times are integer microseconds. required_asset_roles may contain only exact allowed asset-role tokens; image quality requirements belong in tone or story beats, never as roles. Evidence may contain only authority observation IDs. Unknown arrays stay empty. Never infer facts from asset IDs."),
            ChatMessage("user", json.dumps({
                "authority_observations": authority,
                "allowed_asset_roles": sorted({item["role"] for item in snapshot.document["assets"]
                                                if item["kind"] != "text"}),
                "allowed_authority_evidence_ids": sorted(item["observation_id"] for item in authority),
            }, ensure_ascii=False, sort_keys=True)),
        ), temperature=0.0, max_tokens=4800, response_format=_brief_response_format())
        response = self._complete(request)
        candidate_text = response.text
        for attempt in range(3):
            try:
                value = json.loads(candidate_text)
                if not isinstance(value, dict):
                    raise ValueError("project brief response must be an object")
                authority_ids = {item["observation_id"] for item in authority}
                asset_roles = {item["role"] for item in snapshot.document["assets"]
                               if item["kind"] != "text"}
                brief = ProjectBrief.from_dict(value, authority_ids, asset_roles)
                # Preserve an explicit quoted music-file lock even if the provider omits it.
                # This extracts only the user's literal filename; it makes no creative choice.
                authority_text = "\n".join(item["text"] for item in authority)
                literal_music = set(re.findall(
                    r'(?:เพลง|music)\s*:\s*(?:ใช้ไฟล์|use\s+(?:the\s+)?file)\s*["“]([^"”]+)["”]',
                    authority_text, flags=re.IGNORECASE))
                if len(literal_music) == 1:
                    music_name = next(iter(literal_music))
                    if music_name in brief.forbidden_asset_names:
                        raise ValueError("required music conflicts with forbidden assets")
                    if music_name not in brief.required_asset_names:
                        brief = replace(brief, required_asset_names=(*brief.required_asset_names,
                                                                      music_name))
                return brief
            except (json.JSONDecodeError, ValueError) as error:
                if attempt == 2:
                    if isinstance(error, json.JSONDecodeError):
                        raise ValueError("project brief response is not valid JSON") from error
                    raise
                repaired = self._complete(ChatRequest(messages=(
                    ChatMessage("system", "You are the MTCapcut Brief Interpreter contract-repair step. Correct only the schema or evidence-ID violation. Preserve the interpreted meaning. Evidence must use exact allowed observation IDs. Return one complete JSON object only."),
                    ChatMessage("user", json.dumps({
                        "validation_error": str(error), "invalid_response": candidate_text,
                        "allowed_evidence_ids": sorted(item["observation_id"] for item in authority),
                        "allowed_asset_roles": sorted({item["role"] for item in snapshot.document["assets"]
                                                       if item["kind"] != "text"}),
                    }, ensure_ascii=False, sort_keys=True)),
                ), temperature=0.0, max_tokens=4800, response_format=_brief_response_format()))
                candidate_text = repaired.text
        raise RuntimeError("brief interpreter repair loop ended unexpectedly")

    def _complete(self, request: ChatRequest):
        response = self.provider.complete(request)
        if response.finish_reason == "length":
            response = self.provider.complete(replace(request, max_tokens=max(8000, (request.max_tokens or 0) * 2)))
        if response.finish_reason == "length":
            raise ValueError("brief interpreter response was truncated after retry")
        if not response.text.strip():
            raise ValueError("brief interpreter returned empty content")
        return response


class BriefComplianceValidator:
    def validate(self, candidate: dict[str, Any], brief: ProjectBrief,
                 asset_catalog: dict[str, dict[str, Any]]) -> tuple[EditorialFinding, ...]:
        findings: list[EditorialFinding] = []
        visuals = [item for item in candidate.get("segments", []) if item.get("kind") in {"video", "picture"}]
        duration = max((item["start_us"] + item["duration_us"] for item in visuals), default=0)
        if not brief.duration_min_us <= duration <= brief.duration_max_us:
            findings.append(self._finding("duration_out_of_range",
                f"candidate duration {duration}us is outside {brief.duration_min_us}-{brief.duration_max_us}us",
                brief.evidence))
        if candidate.get("width") * brief.height != candidate.get("height") * brief.width:
            findings.append(self._finding("aspect_ratio_mismatch", "candidate aspect ratio does not match brief",
                                          brief.evidence))
        used = [asset_catalog.get(item.get("asset_id"), {}) for item in candidate.get("segments", [])
                if item.get("asset_id")]
        used_names = {Path(str(item.get("path", ""))).name.casefold() for item in used}
        used_roles = {str(item.get("role", "")) for item in used}
        for role in brief.required_asset_roles:
            if role not in used_roles:
                findings.append(self._finding("required_asset_missing", f"required asset role is missing: {role}",
                                              brief.evidence))
        for name in brief.required_asset_names:
            if name.casefold() not in used_names:
                findings.append(self._finding("required_asset_missing", f"required asset is missing: {name}",
                                              brief.evidence))
        for name in brief.forbidden_asset_names:
            if name.casefold() in used_names:
                findings.append(self._finding("forbidden_asset_used", f"forbidden asset is used: {name}",
                                              brief.evidence))
        visible_text = " ".join(str(item.get("text", "")) for item in candidate.get("segments", [])
                                if item.get("kind") == "text")
        visible_text = re.sub(r"\s+", " ", re.sub(r"[|\n]+", " ", visible_text)).strip()
        for message in brief.required_messages:
            normalized_message = re.sub(r"\s+", " ", message).strip()
            if normalized_message not in visible_text:
                findings.append(self._finding("required_message_missing", f"required message is missing: {message}",
                                              brief.evidence))
        return tuple(findings)

    @staticmethod
    def _finding(code: str, text: str, evidence: tuple[str, ...]) -> EditorialFinding:
        return EditorialFinding(code, "brief_compliance_validator", FindingCategory.BRIEF_COMPLIANCE,
                                FindingSeverity.HIGH, text, evidence, "Lead Editor must revise the candidate",
                                "lead_editor", (ReleaseScope.PRIVATE_PREVIEW, ReleaseScope.PUBLICATION))
