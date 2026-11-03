from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from mtcapcut.config import Config, ShotAnalysisSettings
from mtcapcut.map import UnderstandingMap
from mtcapcut.perception import EvidenceArtifact
from mtcapcut.shot_detection import ShotCandidate
from mtcapcut.shot_map_service import ShotMapService


class FakeShotEngine:
    producer_version = "fake-1"

    def __init__(self):
        self.calls = 0

    def detect(self, source):
        self.calls += 1
        return [ShotCandidate(0, 1_000_000, None), ShotCandidate(1_000_000, 2_000_000, 42.0)]


class ShotMapServiceTests(unittest.TestCase):
    def test_persists_once_and_reuses_same_asset_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "clip.mp4"
            source.write_bytes(b"clip")
            ffprobe = root / "ffprobe.exe"
            ffprobe.write_bytes(b"probe")
            config = Config(root, ffprobe, root, shot_analysis=ShotAnalysisSettings(
                enabled=True, frames_per_shot=1, frame_width=320,
            ))
            engine = FakeShotEngine()
            extracts = []

            def extract(ffmpeg, input_path, destination, at_us, width):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(f"frame:{at_us}:{width}".encode())
                extracts.append(at_us)
                return EvidenceArtifact("frame", at_us, at_us, destination,
                                        sha256(destination.read_bytes()).hexdigest())

            with UnderstandingMap(root / "understanding.sqlite3") as understanding:
                understanding.add_asset({
                    "asset_id": "clip-1", "path": str(source), "kind": "clip", "role": "broll",
                    "source": "test", "rights_status": "test", "content_hash": sha256(b"clip").hexdigest(),
                    "size_bytes": 4, "technical": {"duration_us": 2_000_000},
                })
                service = ShotMapService(config, understanding, root, engine=engine, frame_extractor=extract)
                first = service.analyze("clip-1")
                second = service.analyze("clip-1")
                timeline = understanding.current_asset_timeline("clip-1")
                artifacts = understanding.current_artifacts("clip-1")
            self.assertFalse(first.cache_hit)
            self.assertTrue(second.cache_hit)
            self.assertEqual(engine.calls, 1)
            self.assertEqual(extracts, [500_000, 1_500_000])
            self.assertEqual(len(timeline), 2)
            self.assertEqual(len(artifacts), 2)
            self.assertEqual(first.observation_ids, second.observation_ids)


if __name__ == "__main__":
    unittest.main()
