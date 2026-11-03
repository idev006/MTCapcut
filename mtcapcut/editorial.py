"""Long-form editorial hierarchy, timeline placements, and provenance receipts.

The hierarchy answers *why the story is structured this way*. ElementPlacement
answers *what appears on the timeline*. Receipt answers *how a result was
produced and verified*. Keeping these concerns separate allows music, captions,
and evidence to span more than one edit segment without duplicating records.
"""

from dataclasses import dataclass
from pathlib import Path

from .timeline import Segment as TimelineSegment
from .timeline import TimelinePlan


@dataclass(frozen=True)
class Chapter:
    chapter_id: str
    title: str
    scene_ids: tuple[str, ...]


@dataclass(frozen=True)
class Scene:
    scene_id: str
    chapter_id: str
    purpose: str
    segment_ids: tuple[str, ...]


@dataclass(frozen=True)
class EditSegment:
    segment_id: str
    scene_id: str
    start_us: int
    end_us: int
    intent: str = ""


@dataclass(frozen=True)
class ElementPlacement:
    element_id: str
    kind: str
    track: str
    start_us: int
    end_us: int
    segment_ids: tuple[str, ...]
    asset_version_id: str | None = None
    source_path: Path | None = None
    source_start_us: int = 0
    text: str | None = None
    parameters: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Receipt:
    """Append-only provenance record; persistence must reject replacement."""

    receipt_id: str
    kind: str
    revision_id: str
    subject_ids: tuple[str, ...]
    producer: str
    producer_version: str
    input_hashes: tuple[str, ...] = ()
    output_hashes: tuple[str, ...] = ()
    config_hash: str = ""
    model_id: str | None = None
    model_version: str | None = None
    details: tuple[tuple[str, str], ...] = ()
    created_at: str = ""


@dataclass(frozen=True)
class EditRecipe:
    """Reusable editing policy, distinct from a receipt of one execution."""

    recipe_id: str
    version: str
    purpose: str
    parameters: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class EditorialRevision:
    revision_id: str
    parent_revision_id: str | None
    chapters: tuple[Chapter, ...]
    scenes: tuple[Scene, ...]
    segments: tuple[EditSegment, ...]
    elements: tuple[ElementPlacement, ...]


@dataclass(frozen=True)
class EditScope:
    requested_start_us: int
    requested_end_us: int
    context_start_us: int
    context_end_us: int
    editable_segment_ids: tuple[str, ...]
    context_segment_ids: tuple[str, ...]
    affected_element_ids: tuple[str, ...]


def _duplicates(values: list[str]) -> set[str]:
    return {value for value in values if values.count(value) > 1}


def _overlaps(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a


def validate_revision(revision: EditorialRevision) -> list[str]:
    errors: list[str] = []
    chapter_by_id = {item.chapter_id: item for item in revision.chapters}
    scene_by_id = {item.scene_id: item for item in revision.scenes}
    segment_by_id = {item.segment_id: item for item in revision.segments}
    element_ids = [item.element_id for item in revision.elements]
    for label, values in (
        ("chapter", [item.chapter_id for item in revision.chapters]),
        ("scene", [item.scene_id for item in revision.scenes]),
        ("segment", [item.segment_id for item in revision.segments]),
        ("element", element_ids),
    ):
        for duplicate in sorted(_duplicates(values)):
            errors.append(f"duplicate {label}_id: {duplicate}")

    referenced_scenes: list[str] = []
    for chapter in revision.chapters:
        for scene_id in chapter.scene_ids:
            referenced_scenes.append(scene_id)
            scene = scene_by_id.get(scene_id)
            if scene is None:
                errors.append(f"chapter {chapter.chapter_id}: missing scene {scene_id}")
            elif scene.chapter_id != chapter.chapter_id:
                errors.append(f"scene {scene_id}: chapter ownership mismatch")
    for scene in revision.scenes:
        if scene.chapter_id not in chapter_by_id:
            errors.append(f"scene {scene.scene_id}: missing chapter {scene.chapter_id}")
        if referenced_scenes.count(scene.scene_id) != 1:
            errors.append(f"scene {scene.scene_id}: must appear in exactly one chapter order")

    referenced_segments: list[str] = []
    for scene in revision.scenes:
        for segment_id in scene.segment_ids:
            referenced_segments.append(segment_id)
            segment = segment_by_id.get(segment_id)
            if segment is None:
                errors.append(f"scene {scene.scene_id}: missing segment {segment_id}")
            elif segment.scene_id != scene.scene_id:
                errors.append(f"segment {segment_id}: scene ownership mismatch")
    for segment in revision.segments:
        if segment.start_us < 0 or segment.end_us <= segment.start_us:
            errors.append(f"segment {segment.segment_id}: invalid time range")
        if segment.scene_id not in scene_by_id:
            errors.append(f"segment {segment.segment_id}: missing scene {segment.scene_id}")
        if referenced_segments.count(segment.segment_id) != 1:
            errors.append(f"segment {segment.segment_id}: must appear in exactly one scene order")

    media_kinds = {"video", "picture", "audio"}
    text_kinds = {"text", "caption"}
    allowed_kinds = media_kinds | text_kinds | {"graphic", "transition", "effect"}
    for element in revision.elements:
        if element.kind not in allowed_kinds:
            errors.append(f"element {element.element_id}: unsupported kind")
        if not element.track:
            errors.append(f"element {element.element_id}: track is required")
        if element.start_us < 0 or element.end_us <= element.start_us or element.source_start_us < 0:
            errors.append(f"element {element.element_id}: invalid time range")
        if not element.segment_ids:
            errors.append(f"element {element.element_id}: at least one segment link is required")
        for segment_id in element.segment_ids:
            segment = segment_by_id.get(segment_id)
            if segment is None:
                errors.append(f"element {element.element_id}: missing segment {segment_id}")
            elif not _overlaps(element.start_us, element.end_us, segment.start_us, segment.end_us):
                errors.append(f"element {element.element_id}: does not overlap segment {segment_id}")
        if element.kind in media_kinds and (element.asset_version_id is None or element.source_path is None):
            errors.append(f"element {element.element_id}: media requires asset_version_id and source_path")
        if element.kind in text_kinds and not element.text:
            errors.append(f"element {element.element_id}: text is required")
    return errors


def scene_range(revision: EditorialRevision, scene_id: str) -> tuple[int, int]:
    segments = [item for item in revision.segments if item.scene_id == scene_id]
    if not segments:
        raise KeyError(scene_id)
    return min(item.start_us for item in segments), max(item.end_us for item in segments)


def select_edit_scope(
    revision: EditorialRevision,
    start_us: int,
    end_us: int,
    *,
    context_us: int = 30_000_000,
) -> EditScope:
    """Resolve a user time request to stable IDs plus cross-boundary elements."""
    if start_us < 0 or end_us <= start_us or context_us < 0:
        raise ValueError("Invalid edit or context range")
    errors = validate_revision(revision)
    if errors:
        raise ValueError("; ".join(errors))
    context_start = max(0, start_us - context_us)
    context_end = end_us + context_us
    editable = tuple(item.segment_id for item in revision.segments
                     if _overlaps(item.start_us, item.end_us, start_us, end_us))
    context = tuple(item.segment_id for item in revision.segments
                    if _overlaps(item.start_us, item.end_us, context_start, context_end))
    editable_set = set(editable)
    affected_elements = tuple(item.element_id for item in revision.elements
                              if editable_set.intersection(item.segment_ids)
                              or _overlaps(item.start_us, item.end_us, start_us, end_us))
    return EditScope(start_us, end_us, context_start, context_end, editable, context, affected_elements)


def to_timeline_plan(revision: EditorialRevision, width: int, height: int, fps: int) -> TimelinePlan:
    """Map supported placements to the provider-neutral timeline adapter model."""
    errors = validate_revision(revision)
    if errors:
        raise ValueError("; ".join(errors))
    timeline_segments = []
    for element in revision.elements:
        kind = "text" if element.kind == "caption" else element.kind
        if kind not in {"video", "picture", "audio", "text"}:
            raise ValueError(f"Element kind is not supported by the current pyCapCut slice: {element.kind}")
        timeline_segments.append(TimelineSegment(
            kind=kind,
            start_us=element.start_us,
            duration_us=element.end_us - element.start_us,
            track=element.track,
            asset_id=element.asset_version_id,
            source_path=element.source_path,
            source_start_us=element.source_start_us,
            text=element.text,
            rationale="editorial placement",
            element_id=element.element_id,
            edit_segment_ids=element.segment_ids,
        ))
    return TimelinePlan(width, height, fps, tuple(timeline_segments))
