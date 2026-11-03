"""Provider-neutral edit plan and deterministic validation."""

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class Segment:
    kind: str
    start_us: int
    duration_us: int
    track: str
    asset_id: str | None = None
    source_path: Path | None = None
    source_start_us: int = 0
    text: str | None = None
    rationale: str = ""
    element_id: str | None = None
    edit_segment_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TimelinePlan:
    width: int
    height: int
    fps: int
    segments: tuple[Segment, ...]

    @property
    def duration_us(self) -> int:
        return max((s.start_us + s.duration_us for s in self.segments), default=0)


def validate_plan(plan: TimelinePlan) -> list[str]:
    errors: list[str] = []
    if plan.width < 1 or plan.height < 1 or plan.fps < 1:
        errors.append("Canvas width, height and fps must be positive")
    by_track: dict[str, list[Segment]] = {}
    for index, segment in enumerate(plan.segments):
        label = f"segments[{index}]"
        if segment.kind not in {"video", "picture", "audio", "text"}:
            errors.append(f"{label}: unsupported kind")
        if segment.start_us < 0 or segment.duration_us <= 0 or segment.source_start_us < 0:
            errors.append(f"{label}: invalid time range")
        if not segment.track:
            errors.append(f"{label}: track is required")
        if segment.kind == "text" and not segment.text:
            errors.append(f"{label}: text is required")
        if segment.kind != "text" and (segment.source_path is None or segment.asset_id is None):
            errors.append(f"{label}: source_path and asset_id are required")
        by_track.setdefault(segment.track, []).append(segment)
    for track, segments in by_track.items():
        ordered = sorted(segments, key=lambda item: item.start_us)
        for previous, current in zip(ordered, ordered[1:]):
            if current.start_us < previous.start_us + previous.duration_us:
                errors.append(f"track {track}: overlapping segments")
    return errors


def load_plan(path: Path) -> TimelinePlan:
    """Load a plan whose media paths are relative to the JSON file."""
    document = json.loads(path.resolve(strict=True).read_text(encoding="utf-8-sig"))
    if not isinstance(document, dict) or not isinstance(document.get("segments"), list):
        raise ValueError("Timeline plan must be an object with a segments array")
    segments = []
    for raw in document["segments"]:
        if not isinstance(raw, dict):
            raise ValueError("Each timeline segment must be an object")
        source = raw.get("source_path")
        segments.append(Segment(
            kind=raw["kind"], start_us=int(raw["start_us"]), duration_us=int(raw["duration_us"]),
            track=raw["track"], asset_id=raw.get("asset_id"),
            source_path=(path.parent / source).resolve() if source else None,
            source_start_us=int(raw.get("source_start_us", 0)), text=raw.get("text"),
            rationale=raw.get("rationale", ""),
            element_id=raw.get("element_id"),
            edit_segment_ids=tuple(raw.get("edit_segment_ids", ())),
        ))
    plan = TimelinePlan(int(document["width"]), int(document["height"]), int(document["fps"]), tuple(segments))
    errors = validate_plan(plan)
    if errors:
        raise ValueError("; ".join(errors))
    return plan
