"""Application service orchestrating shot detection, sampling and SSOT writes."""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable

from .config import Config
from .map import UnderstandingMap
from .perception import EvidenceArtifact, extract_frame, hash_file
from .shot_detection import SceneDetectShotEngine, sample_times


@dataclass(frozen=True)
class ShotMapResult:
    asset_id: str
    shot_count: int
    sample_count: int
    observation_ids: tuple[str, ...]
    frame_artifact_ids: tuple[str, ...]
    cache_hit: bool
    config_hash: str


class ShotMapService:
    def __init__(self, config: Config, understanding: UnderstandingMap, project_root: Path, *,
                 engine=None, frame_extractor: Callable[..., EvidenceArtifact] = extract_frame):
        self.config = config
        self.understanding = understanding
        self.project_root = project_root.resolve()
        self.engine = engine or SceneDetectShotEngine(config.shot_analysis)
        self.frame_extractor = frame_extractor

    def analyze(self, asset_id: str) -> ShotMapResult:
        asset = self.understanding.get_asset(asset_id)
        if asset["kind"] != "clip":
            raise ValueError("shot analysis requires a clip asset")
        source = Path(asset["path"]).resolve(strict=True)
        config_document = {"settings": asdict(self.config.shot_analysis),
                           "producer_version": self.engine.producer_version}
        config_hash = sha256(json.dumps(config_document, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=True).encode("utf-8")).hexdigest()
        producer = f"shot-map:{self.engine.producer_version}:{config_hash[:12]}"
        existing = [item for item in self.understanding.current_asset_timeline(asset_id)
                    if item["modality"] == "shot" and item["producer"] == producer]
        if existing:
            artifacts = self.understanding.current_artifacts(asset_id, producer=producer)
            return ShotMapResult(asset_id, len(existing), len(artifacts),
                                 tuple(item["observation_id"] for item in existing),
                                 tuple(item["artifact_id"] for item in artifacts), True, config_hash)

        shots = self.engine.detect(source)
        samples = sample_times(shots, self.config.shot_analysis.frames_per_shot)
        run_root = (self.project_root / "artifacts" / "shot-map" / asset_id /
                    f"{asset['content_hash'][:16]}-{config_hash[:16]}").resolve()
        if not run_root.is_relative_to(self.project_root):
            raise ValueError("shot artifact path escaped project root")
        run_root.mkdir(parents=True, exist_ok=True)
        artifact_entries = []
        sample_ordinals: dict[int, int] = {}
        for sample in samples:
            ordinal = sample_ordinals.get(sample.shot_index, 0)
            sample_ordinals[sample.shot_index] = ordinal + 1
            destination = run_root / f"shot-{sample.shot_index:05d}-sample-{ordinal:02d}-{sample.at_us}.jpg"
            if destination.exists():
                if destination.stat().st_size == 0:
                    raise RuntimeError(f"empty cached frame artifact: {destination}")
                artifact = EvidenceArtifact("frame", sample.at_us, sample.at_us,
                                            destination, hash_file(destination))
            else:
                artifact = self.frame_extractor(
                    self.config.ffmpeg, source, destination, sample.at_us,
                    width=self.config.shot_analysis.frame_width,
                )
            artifact_entries.append({
                "kind": "sampled_frame", "path": str(artifact.path),
                "content_hash": artifact.content_hash, "producer": producer,
                "producer_version": self.engine.producer_version, "config_hash": config_hash,
            })
        observations = [{
            "modality": "shot", "start_us": shot.start_us, "end_us": shot.end_us,
            "text": json.dumps({"type": "shot_candidate", "index": index,
                                "boundary_score": shot.boundary_score}, ensure_ascii=False),
            "confidence": None, "producer": producer,
            "producer_version": self.engine.producer_version,
        } for index, shot in enumerate(shots)]
        stored = self.understanding.add_analysis_bundle(asset_id, observations, artifact_entries)
        return ShotMapResult(asset_id, len(shots), len(samples),
                             tuple(stored["observation_ids"]), tuple(stored["artifact_ids"]),
                             False, config_hash)
