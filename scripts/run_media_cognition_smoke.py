"""Run a bounded live Eye/Ear/Brain smoke test without human media inspection."""

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from mtcapcut.ai_provider import create_provider
from mtcapcut.config import load_config
from mtcapcut.data_policy import DataPolicyGate
from mtcapcut.map import UnderstandingMap
from mtcapcut.media_cognition import MediaCognitionEngine
from mtcapcut.perception import EvidenceArtifact, extract_audio, extract_frame


PROJECT = ROOT / "workspace" / "road-report-001"


def digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("picture", "video_frame", "audio"))
    selected_case = parser.parse_args().case
    config = load_config(ROOT / "config.toml")
    provider_name = config.ai.default_provider
    if not provider_name:
        raise ValueError("ai.default_provider is not configured")
    vision_settings = replace(
        config.ai.providers[provider_name],
        model=config.ai.vision_model or config.ai.providers[provider_name].model,
    )
    audio_settings = replace(
        config.ai.providers[provider_name],
        model=config.ai.audio_model or config.ai.providers[provider_name].model,
    )
    run_dir = PROJECT / "artifacts" / f"media-cognition-smoke-{uuid4().hex[:8]}"
    run_dir.mkdir(parents=True, exist_ok=False)

    picture_path = PROJECT / "assets/originals/pictures/official/prd-546764/prd-transfer-cover.jpg"
    video_path = PROJECT / "assets/derived/clips/northernnews-140824-handover-silent.mp4"
    audio_path = PROJECT / "assets/originals/audio/โป้ง - หัวใจไม่เคยหยุดทำ1.mp3"
    video_frame = extract_frame(config.ffmpeg, video_path, run_dir / "video-frame-8s.jpg", 8_000_000)
    audio_chunk = extract_audio(
        config.ffmpeg, audio_path, run_dir / "audio-30-45s.wav",
        start_us=30_000_000, end_us=45_000_000,
    )
    evidence = [
        ("picture", "4be3d062-2395-419d-991b-b6a69cccf439",
         EvidenceArtifact("frame", 0, 0, picture_path, digest(picture_path))),
        ("video_frame", "32d26d67-21bd-4a26-b56c-8871ce3acd22", video_frame),
        ("audio", "f436de92-7a02-4d35-8405-e820f1e3d877", audio_chunk),
    ]
    if selected_case:
        evidence = [item for item in evidence if item[0] == selected_case]

    report = {"provider": provider_name, "vision_model": vision_settings.model,
              "audio_model": audio_settings.model, "run_dir": str(run_dir), "cases": []}
    with UnderstandingMap(PROJECT / "understanding.sqlite3") as understanding:
        policy_gate = DataPolicyGate(config, understanding)
        vision_engine = MediaCognitionEngine(create_provider(vision_settings), policy_gate=policy_gate)
        audio_engine = MediaCognitionEngine(create_provider(audio_settings), policy_gate=policy_gate)
        for label, asset_id, artifact in evidence:
            case = {"case": label, "asset_id": asset_id}
            try:
                engine = audio_engine if label == "audio" else vision_engine
                observations = engine.analyze(artifact, asset_id=asset_id)
                producer = f"media-cognition:{engine.provider.settings.name}:{engine.provider.settings.model}"
                observation_ids = understanding.add_observations(asset_id, [{
                    "modality": item.modality,
                    "start_us": item.start_us,
                    "end_us": item.end_us,
                    "text": item.text,
                    "confidence": item.confidence,
                    "producer": producer,
                    "producer_version": engine.producer_version,
                } for item in observations])
                case.update({
                    "status": "PASS",
                    "observation_ids": observation_ids,
                    "observations": [
                        {"modality": item.modality, "text": item.text,
                         "confidence": item.confidence, "start_us": item.start_us,
                         "end_us": item.end_us}
                        for item in observations
                    ],
                })
            except Exception as error:
                case.update({"status": "FAIL", "error_type": type(error).__name__, "error": str(error)[:500]})
            report["cases"].append(case)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(case["status"] == "PASS" for case in report["cases"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
