"""Run a bounded local faster-whisper smoke test and persist proposals to SSOT."""

import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from mtcapcut.config import load_config
from mtcapcut.local_ear import FasterWhisperEar
from mtcapcut.map import UnderstandingMap
from mtcapcut.perception import extract_audio


def main() -> int:
    config = load_config(ROOT / "config.toml")
    project = config.workspace / "road-report-001"
    run_dir = project / "artifacts" / f"local-ear-smoke-{uuid4().hex[:8]}"
    run_dir.mkdir(parents=True, exist_ok=False)
    artifact = extract_audio(
        config.ffmpeg,
        project / "assets/originals/audio/โป้ง - หัวใจไม่เคยหยุดทำ1.mp3",
        run_dir / "audio-30-45s.wav",
        start_us=30_000_000,
        end_us=45_000_000,
    )
    ear = FasterWhisperEar(config.local_ear)
    with UnderstandingMap(project / "understanding.sqlite3") as understanding:
        observations = ear.transcribe(artifact)
        ids = understanding.add_observations(
            "f436de92-7a02-4d35-8405-e820f1e3d877",
            [{
                "modality": "speech",
                "start_us": item.start_us,
                "end_us": item.end_us,
                "text": item.text,
                "confidence": item.confidence,
                "producer": f"faster-whisper:{config.local_ear.model_size}",
                "producer_version": ear.producer_version,
            } for item in observations],
        ) if observations else []
    print(json.dumps({
        "status": "PASS" if observations else "FAIL",
        "model": config.local_ear.model_size,
        "device": config.local_ear.device,
        "compute_type": config.local_ear.compute_type,
        "run_dir": str(run_dir),
        "observation_ids": ids,
        "observations": [item.__dict__ for item in observations],
    }, ensure_ascii=False, indent=2))
    return 0 if observations else 1


if __name__ == "__main__":
    raise SystemExit(main())
