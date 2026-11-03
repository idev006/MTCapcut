"""Safe pyCapCut 0.0.4 adapter for a small, provider-neutral timeline.

The output root must carry a sandbox marker. No CapCut application folders are
modified by this module. Draft compatibility still requires a manual check.
"""

from importlib.metadata import version
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from .timeline import TimelinePlan, validate_plan


SANDBOX_MARKER = ".mtcapcut-draft-sandbox"


def validate(plan: TimelinePlan, output_root: Path, draft_name: str) -> int:
    root = output_root.resolve(strict=True)
    if not root.is_dir() or not (root / SANDBOX_MARKER).is_file():
        raise ValueError("Output root needs an explicit draft sandbox marker")
    if not draft_name or draft_name in {".", ".."} or Path(draft_name).name != draft_name or any(c in draft_name for c in '<>:"/\\|?*'):
        raise ValueError("Draft name must be one safe path component")
    if (root / draft_name).exists():
        raise FileExistsError(root / draft_name)
    errors = validate_plan(plan)
    if errors:
        raise ValueError("; ".join(errors))
    visuals = sorted((s for s in plan.segments if s.kind in {"video", "picture"}), key=lambda s: s.start_us)
    if not visuals or len({s.track for s in visuals}) != 1:
        raise ValueError("One main visual track is required")
    cursor = 0
    for item in visuals:
        if item.start_us != cursor:
            raise ValueError("Main visual track must be gapless and start at zero")
        cursor += item.duration_us
    for item in plan.segments:
        if item.kind != "text" and not item.source_path.is_file():
            raise FileNotFoundError(item.source_path)
        if item.start_us + item.duration_us > cursor:
            raise ValueError("Segment exceeds main visual timeline")
    return cursor


def create_draft(plan: TimelinePlan, output_root: Path, draft_name: str) -> Path:
    """Create a new draft under a marked sandbox, never replacing an old draft."""
    duration = validate(plan, output_root, draft_name)
    if version("pycapcut") != "0.0.4":
        raise RuntimeError("This adapter requires pycapcut==0.0.4")
    import pycapcut as cc

    root = output_root.resolve(strict=True)
    final = root / draft_name
    with TemporaryDirectory(prefix="mtcapcut-stage-", dir=root) as stage:
        script = cc.DraftFolder(stage).create_draft(draft_name, plan.width, plan.height, plan.fps, allow_replace=False)
        visuals = sorted((s for s in plan.segments if s.kind in {"video", "picture"}), key=lambda s: s.start_us)
        visual_track = visuals[0].track
        script.add_track(cc.TrackType.video, visual_track)
        for visual in visuals:
            source_range = None if visual.kind == "picture" else cc.Timerange(visual.source_start_us, visual.duration_us)
            segment = cc.VideoSegment(str(visual.source_path.resolve()), cc.Timerange(visual.start_us, visual.duration_us),
                                      source_timerange=source_range)
            script.add_segment(segment, visual_track)
        for track in sorted({s.track for s in plan.segments if s.kind == "audio"}):
            script.add_track(cc.TrackType.audio, track)
            for audio in sorted((s for s in plan.segments if s.kind == "audio" and s.track == track), key=lambda s: s.start_us):
                segment = cc.AudioSegment(str(audio.source_path.resolve()), cc.Timerange(audio.start_us, audio.duration_us),
                                          source_timerange=cc.Timerange(audio.source_start_us, audio.duration_us),
                                          volume=1.0)
                script.add_segment(segment, track)
        for track in sorted({s.track for s in plan.segments if s.kind == "text"}):
            script.add_track(cc.TrackType.text, track)
            for title in sorted((s for s in plan.segments if s.kind == "text" and s.track == track), key=lambda s: s.start_us):
                script.add_segment(cc.TextSegment(title.text, cc.Timerange(title.start_us, title.duration_us)), track)
        script.save()
        draft_dir = Path(stage) / draft_name
        content = draft_dir / "draft_content.json"
        saved = json.loads(content.read_text(encoding="utf-8"))
        if saved.get("duration") != duration:
            raise ValueError("Saved draft duration differs from the plan")
        if final.exists():
            raise FileExistsError(final)
        os.rename(draft_dir, final)
    return final
