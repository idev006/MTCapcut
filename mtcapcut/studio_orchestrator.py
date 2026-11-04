"""Autonomous Studio Council orchestration and candidate-plan validation."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Callable

from .ai_provider import OpenAICompatibleProvider
from .config import Config
from .data_policy import DataPolicyGate
from .map import UnderstandingMap
from .media_readiness import semantic_observation_ids_for_range
from .editorial_findings import compute_release_gates
from .project_brief import BriefComplianceValidator, BriefInterpreterEngine
from .studio_contracts import STUDIO_ROLES, StudioRecommendation
from .studio_roles import PROMPT_VERSION, StudioRoleEngine
from .studio_snapshot import authorize_studio_snapshot, build_studio_snapshot
from .timeline import Segment, TimelinePlan, validate_plan


@dataclass(frozen=True)
class StudioRunResult:
    run_id: str
    output: Path
    status: str
    recommendation_count: int
    unresolved_objections: tuple[str, ...]
    private_preview_eligible: bool
    publication_eligible: bool


class BriefNonComplianceError(ValueError):
    """A mechanically valid candidate that violates the typed brief."""


class AutonomousStudioOrchestrator:
    def __init__(self, config: Config, understanding: UnderstandingMap,
                 provider: OpenAICompatibleProvider,
                 authority_asset_ids: set[str] | None = None,
                 progress: Callable[[str, int, int], None] | None = None):
        self.config = config
        self.understanding = understanding
        self.provider = provider
        self.authority_asset_ids = authority_asset_ids
        self.progress = progress

    def run(self, output: Path) -> StudioRunResult:
        output = output.resolve()
        if output.exists():
            raise FileExistsError(output)
        snapshot = build_studio_snapshot(self.understanding, self.authority_asset_ids)
        authorize_studio_snapshot(DataPolicyGate(self.config, self.understanding),
                                  self.provider.settings, snapshot)
        run_id = self.understanding.start_studio_run(
            snapshot.content_hash, self.provider.settings.name, self.provider.settings.model,
            PROMPT_VERSION, snapshot.document,
        )
        engine = StudioRoleEngine(self.provider)
        recommendations: list[StudioRecommendation] = []
        try:
            brief = BriefInterpreterEngine(self.provider).interpret(snapshot)
            self.understanding.append_studio_brief(run_id, brief.to_dict())
            snapshot = type(snapshot)(
                {**snapshot.document, "project_brief": brief.to_dict()}, snapshot.content_hash,
            )
            total = len(STUDIO_ROLES) + 2
            for index, role in enumerate(STUDIO_ROLES, 1):
                if self.progress:
                    self.progress(role, index, total)
                recommendation = engine.recommend(role, snapshot)
                self.understanding.append_studio_recommendation(run_id, recommendation.to_dict())
                recommendations.append(recommendation)
            if self.progress:
                self.progress("clip_director", len(STUDIO_ROLES) + 1, total)
            synthesis = engine.synthesize(snapshot, tuple(recommendations))
            if self.progress:
                self.progress("lead_editor", total, total)
            raw_candidate = engine.create_timeline(snapshot, synthesis, tuple(recommendations))
            candidate = None
            # Long-form plans can require several provider-authored semantic repairs (runtime,
            # exact copy, source ranges) while every revision remains behind the same validators.
            max_candidate_attempts = 6
            for attempt in range(max_candidate_attempts):
                try:
                    findings = tuple(item for recommendation in recommendations
                                     for item in recommendation.objections)
                    candidate = self._validated_candidate(raw_candidate, snapshot.evidence_ids,
                                                          findings, brief.delivery_scope, run_id)
                    asset_catalog = {item["asset_id"]: self.understanding.get_asset(item["asset_id"])
                                     for item in self.understanding.list_assets()}
                    compliance = BriefComplianceValidator().validate(candidate, brief, asset_catalog)
                    if compliance:
                        raise BriefNonComplianceError(json.dumps({
                            "brief_compliance_findings": [item.to_dict() for item in compliance]
                        }, ensure_ascii=False, sort_keys=True))
                    candidate["project_brief"] = brief.to_dict()
                    candidate["brief_compliance"] = {"status": "pass", "findings": []}
                    candidate["gates"]["publication_eligible"] = (
                        candidate["gates"]["publication_eligible"] and brief.publication_allowed
                    )
                    break
                except ValueError as error:
                    if attempt == max_candidate_attempts - 1:
                        if isinstance(error, BriefNonComplianceError):
                            self.understanding.reject_studio_run(
                                run_id, synthesis.to_dict(), candidate or raw_candidate, str(error),
                            )
                            return StudioRunResult(
                                run_id, output, "candidate_rejected", len(recommendations),
                                synthesis.unresolved_objections, False, False,
                            )
                        raise
                    raw_candidate = engine.revise_timeline(
                        snapshot, synthesis, tuple(recommendations), raw_candidate, str(error),
                    )
            if candidate is None:
                raise RuntimeError("candidate validation did not produce a result")
            self.understanding.complete_studio_run(run_id, synthesis.to_dict(), candidate)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as error:
            self.understanding.fail_studio_run(run_id, f"{type(error).__name__}: {error}")
            raise
        return StudioRunResult(
            run_id, output, "candidate_ready", len(recommendations), synthesis.unresolved_objections,
            candidate["gates"]["private_preview_eligible"], candidate["gates"]["publication_eligible"],
        )

    def _validated_candidate(self, candidate: dict, evidence_ids: set[str], findings: tuple,
                             delivery_scope: str, run_id: str) -> dict:
        raw_segments = [dict(item) for item in candidate["segments"]]
        raw_visuals = sorted((item for item in raw_segments if item["kind"] in {"video", "picture"}),
                             key=lambda item: (item["start_us"], item["segment_id"]))
        if {item["track"] for item in raw_visuals} - {"main"}:
            raise ValueError("autonomous preview supports visuals only on the main track")
        packed_cursor = 0
        for visual in raw_visuals:
            original_start = visual["start_us"]
            visual["start_us"] = packed_cursor
            if original_start != packed_cursor:
                visual["start_us_provider"] = original_start
                visual["timing_auto_normalized"] = True
            packed_cursor += visual["duration_us"]
        candidate = {**candidate, "segments": raw_segments}
        asset_catalog = {item["asset_id"]: item for item in self.understanding.list_assets()}
        observation_index = {}
        for asset_id in asset_catalog:
            for observation in self.understanding.current_asset_timeline(asset_id):
                observation_index[observation["observation_id"]] = {**observation, "asset_id": asset_id}
        segments = []
        used_assets: set[str] = set()
        output_segments = []
        rejected_segments = []
        for raw in candidate["segments"]:
            kind = raw["kind"]
            if kind not in {"video", "picture"}:
                if raw["start_us"] >= packed_cursor:
                    rejected_segments.append({**raw, "rejection_reason": "segment starts after main visual end"})
                    continue
                if raw["start_us"] + raw["duration_us"] > packed_cursor:
                    raw["duration_us_provider"] = raw["duration_us"]
                    raw["duration_us"] = packed_cursor - raw["start_us"]
                    raw["timing_auto_normalized"] = True
            rejected_unknown = tuple(item for item in raw["evidence"] if item not in evidence_ids)
            cited = tuple(item for item in raw["evidence"] if item in evidence_ids)
            auto_attached: tuple[str, ...] = ()
            asset_id = raw.get("asset_id")
            source_start_us = int(raw.get("source_start_us", 0))
            source_path = None
            if kind != "text":
                if asset_id not in asset_catalog:
                    raise ValueError("timeline segment cites unknown asset")
                source_end_us = source_start_us + raw["duration_us"]
                matching = semantic_observation_ids_for_range(
                    observation_index.values(), asset_id, source_start_us, source_end_us,
                )
                if not matching:
                    raise ValueError("timeline media source range has no machine observation")
                if not any(observation_index[item]["asset_id"] == asset_id for item in cited):
                    auto_attached = matching
                    cited = tuple(dict.fromkeys((*cited, *matching)))
                asset = self.understanding.get_asset(asset_id)
                source_path = Path(asset["path"])
                used_assets.add(asset_id)
                duration_us = _asset_duration_us(asset["technical"])
                if kind in {"video", "audio"}:
                    if duration_us is None or source_start_us + raw["duration_us"] > duration_us:
                        raise ValueError("timeline source range exceeds asset duration")
            else:
                text = str(raw.get("text", "")).strip()
                if not text:
                    rejected_segments.append({**raw, "rejection_reason": "on-screen text is empty"})
                    continue
                text_lines = tuple(part.strip() for part in re.split(r"[|\n]+", text) if part.strip())
                exact_support = tuple(sorted(
                    observation_id for observation_id, observation in observation_index.items()
                    if observation["modality"] == "text"
                    and text_lines and all(line in observation["text"] for line in text_lines)
                ))
                if not exact_support:
                    rejected_segments.append({
                        **raw, "evidence_rejected_unknown": list(rejected_unknown),
                        "rejection_reason": "on-screen text is not verbatim in authority evidence",
                    })
                    continue
                if not any(all(line in observation_index[item]["text"] for line in text_lines) for item in cited):
                    auto_attached = exact_support
                    cited = tuple(dict.fromkeys((*cited, *exact_support)))
            segments.append(Segment(
                kind, raw["start_us"], raw["duration_us"], raw["track"], asset_id,
                source_path, source_start_us, raw.get("text"), raw["rationale"], raw["segment_id"], (),
            ))
            output_segments.append({**raw, "evidence": list(cited),
                                    "evidence_auto_attached": list(auto_attached),
                                    "evidence_rejected_unknown": list(rejected_unknown),
                                    **({"source_path": str(source_path)} if source_path else {})})
        plan = TimelinePlan(candidate["width"], candidate["height"], candidate["fps"], tuple(segments))
        errors = validate_plan(plan)
        if errors:
            raise ValueError("; ".join(errors))
        visuals = sorted((item for item in segments if item.kind in {"video", "picture"}),
                         key=lambda item: item.start_us)
        if not visuals:
            raise ValueError("autonomous plan requires a visual track")
        cursor = 0
        for visual in visuals:
            if visual.start_us != cursor:
                raise ValueError("autonomous main visual track must be gapless from zero")
            cursor += visual.duration_us
        if cursor != plan.duration_us:
            raise ValueError("autonomous visual track must cover the plan duration")
        rights_blockers = [asset_id for asset_id in sorted(used_assets)
                           if asset_catalog[asset_id]["rights_status"] in {"unknown", "permission-required"}]
        release = compute_release_gates(findings, tuple(rights_blockers), delivery_scope)
        candidate = {**candidate, "segments": output_segments,
                     "rejected_segments": rejected_segments,
                     "studio_run_id": run_id, "prompt_version": PROMPT_VERSION,
                     "gates": {
                         "unresolved_objections": [item.finding_id for item in findings],
                         "editorial_findings": [item.to_dict() for item in findings],
                         "rights_blocker_asset_ids": rights_blockers,
                         "validation_findings": [item["rejection_reason"] for item in rejected_segments],
                         "private_preview_eligible": release.private_preview_eligible,
                         "publication_eligible": release.publication_eligible,
                         "publication_decision": (
                             "engine_validated" if release.publication_eligible
                             else "responsible_person_approval_required"
                         ),
                     }}
        return candidate


def _asset_duration_us(technical: dict) -> int | None:
    value = technical.get("format", {}).get("duration")
    if value is None:
        value = next((item.get("duration") for item in technical.get("streams", [])
                      if item.get("duration") is not None), None)
    try:
        return round(float(value) * 1_000_000) if value is not None else None
    except (TypeError, ValueError):
        return None

