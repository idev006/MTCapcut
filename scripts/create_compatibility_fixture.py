"""Build a deterministic synthetic media set and an isolated pyCapCut draft."""

import argparse
import json
from pathlib import Path
import subprocess

from mtcapcut.capcut_adapter import SANDBOX_MARKER, create_draft
from mtcapcut.timeline import Segment, TimelinePlan


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("draft_name")
    parser.add_argument("--ffmpeg", type=Path, default=Path("D:/libs/ffmpeg/bin/ffmpeg.exe"))
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to reuse fixture directory: {output}")
    output.mkdir(parents=True)
    (output / SANDBOX_MARKER).touch()
    video = output / "clip.mp4"
    picture = output / "picture.png"
    audio = output / "music.mp3"
    common = [str(args.ffmpeg.resolve(strict=True)), "-hide_banner", "-loglevel", "error"]
    run(common + ["-f", "lavfi", "-i", "testsrc2=size=540x960:rate=30:duration=2",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)])
    run(common + ["-f", "lavfi", "-i", "color=c=0x164E63:s=540x960:d=1",
                   "-frames:v", "1", str(picture)])
    run(common + ["-f", "lavfi", "-i", "sine=frequency=440:duration=3",
                   "-q:a", "4", str(audio)])
    plan = TimelinePlan(1080, 1920, 30, (
        Segment("video", 0, 2_000_000, "main", "synthetic-video", video,
                rationale="Technical compatibility fixture"),
        Segment("picture", 2_000_000, 1_000_000, "main", "synthetic-picture", picture,
                rationale="Technical compatibility fixture"),
        Segment("audio", 0, 3_000_000, "music", "synthetic-audio", audio,
                rationale="Technical compatibility fixture"),
        Segment("text", 0, 3_000_000, "titles", text="MT AI: ทดสอบความเข้ากันได้",
                rationale="Verify UTF-8 Thai text"),
    ))
    plan_document = {
        "width": plan.width,
        "height": plan.height,
        "fps": plan.fps,
        "segments": [
            {
                "kind": segment.kind,
                "start_us": segment.start_us,
                "duration_us": segment.duration_us,
                "track": segment.track,
                "asset_id": segment.asset_id,
                "source_path": segment.source_path.name if segment.source_path else None,
                "source_start_us": segment.source_start_us,
                "text": segment.text,
                "rationale": segment.rationale,
            }
            for segment in plan.segments
        ],
    }
    (output / "timeline-plan.json").write_text(
        json.dumps(plan_document, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    draft = create_draft(plan, output, args.draft_name)
    print(json.dumps({"fixture": str(output), "draft": str(draft)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
