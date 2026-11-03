"""Read-only semantic readiness and temporal evidence coverage."""

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .map import UnderstandingMap


SEMANTIC_MODALITIES = frozenset({"vision", "ocr", "speech", "sound", "music"})
STRUCTURAL_MODALITIES = frozenset({"shot"})


def semantic_observation_ids_for_range(observations: Iterable[dict[str, Any]], asset_id: str,
                                       start_us: int, end_us: int) -> tuple[str, ...]:
    """Return semantic evidence overlapping the source range; structural rows never qualify."""
    return tuple(sorted(item["observation_id"] for item in observations
        if item.get("asset_id") == asset_id
        and item.get("modality") in SEMANTIC_MODALITIES
        and (item.get("start_us") is None or (
            item.get("end_us") is not None and item["start_us"] < end_us and item["end_us"] > start_us
        ))))


@dataclass(frozen=True)
class AssetReadiness:
    asset_id: str
    kind: str
    status: str
    semantic_observation_count: int
    structural_observation_count: int
    semantic_coverage: float | None
    uncovered_structural_count: int
    external_ai_policy: str
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MediaReadinessReport:
    status: str
    assets: tuple[AssetReadiness, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "assets": [item.to_dict() for item in self.assets]}


class MediaReadinessAssessor:
    """Conservative inventory gate. It does not open or decode media."""

    def __init__(self, understanding: UnderstandingMap):
        self.understanding = understanding

    def assess(self) -> MediaReadinessReport:
        results = []
        for listed in self.understanding.list_assets():
            asset = self.understanding.get_asset(listed["asset_id"])
            if asset["kind"] == "text":
                continue
            observations = self.understanding.current_asset_timeline(asset["asset_id"])
            semantic = [item for item in observations if item["modality"] in SEMANTIC_MODALITIES]
            structural = [item for item in observations if item["modality"] in STRUCTURAL_MODALITIES]
            policy = self.understanding.current_asset_ai_policy(asset["asset_id"])
            blockers = []
            if not semantic:
                blockers.append("no_semantic_observations")
            uncovered_structural = 0
            if structural:
                indexed = [{**item, "asset_id": asset["asset_id"]} for item in semantic]
                uncovered_structural = sum(not semantic_observation_ids_for_range(
                    indexed, asset["asset_id"], item["start_us"], item["end_us"]
                ) for item in structural)
                if uncovered_structural:
                    blockers.append("semantic_shot_coverage_incomplete")
            coverage = _duration_coverage(semantic, asset["technical"])
            if asset["kind"] == "audio" and coverage is not None and coverage < 0.95:
                blockers.append("semantic_duration_coverage_incomplete")
            if policy is None:
                blockers.append("external_ai_policy_missing")
            elif not policy["external_ai_allowed"]:
                blockers.append("external_ai_not_allowed")
            results.append(AssetReadiness(
                asset["asset_id"], asset["kind"], "ready" if not blockers else "blocked",
                len(semantic), len(structural), coverage, uncovered_structural,
                "missing" if policy is None else ("allowed" if policy["external_ai_allowed"] else "denied"),
                tuple(blockers),
            ))
        status = "ready" if results and all(item.status == "ready" for item in results) else "blocked"
        return MediaReadinessReport(status, tuple(results))


def _duration_coverage(observations: list[dict[str, Any]], technical: dict[str, Any]) -> float | None:
    raw_duration = technical.get("format", {}).get("duration")
    try:
        duration_us = round(float(raw_duration) * 1_000_000)
    except (TypeError, ValueError):
        return None
    intervals = sorted((max(0, item["start_us"]), min(duration_us, item["end_us"]))
                       for item in observations
                       if item.get("start_us") is not None and item.get("end_us") is not None)
    if not intervals or duration_us <= 0:
        return 0.0
    covered = 0
    start, end = intervals[0]
    for next_start, next_end in intervals[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            covered += end - start
            start, end = next_start, next_end
    covered += end - start
    return min(1.0, covered / duration_us)
