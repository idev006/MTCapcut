from pathlib import Path
import subprocess
import tempfile
import unittest

from mtcapcut.config import ShotAnalysisSettings
from mtcapcut.shot_detection import SceneDetectShotEngine, ShotCandidate, sample_times


class ShotDetectionTests(unittest.TestCase):
    def test_detects_gapless_hard_cut_scenes(self):
        ffmpeg = Path("D:/libs/ffmpeg/bin/ffmpeg.exe")
        if not ffmpeg.is_file():
            self.skipTest("FFmpeg unavailable")
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "cuts.mp4"
            subprocess.run([
                str(ffmpeg), "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "color=c=red:s=160x90:r=10:d=1",
                "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=10:d=1",
                "-f", "lavfi", "-i", "color=c=green:s=160x90:r=10:d=1",
                "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p",
                "-c:v", "mpeg4", str(source),
            ], check=True)
            engine = SceneDetectShotEngine(ShotAnalysisSettings(
                enabled=True, threshold=10.0, min_scene_len_frames=5,
            ))
            shots = engine.detect(source)
        self.assertEqual(len(shots), 3)
        self.assertEqual(shots[0].start_us, 0)
        self.assertAlmostEqual(shots[-1].end_us, 3_000_000, delta=150_000)
        self.assertTrue(all(b.start_us == a.end_us for a, b in zip(shots, shots[1:])))
        self.assertIsNone(shots[0].boundary_score)
        self.assertTrue(all(item.boundary_score is not None for item in shots[1:]))

    def test_sampling_is_deterministic_and_bounded(self):
        shots = [ShotCandidate(0, 1_000_000, None), ShotCandidate(1_000_000, 1_000_003, 30.0)]
        samples = sample_times(shots, 3)
        self.assertEqual([item.at_us for item in samples[:3]], [250_000, 500_000, 750_000])
        self.assertTrue(all(shots[item.shot_index].start_us <= item.at_us < shots[item.shot_index].end_us
                            for item in samples))
        self.assertEqual(samples, sample_times(shots, 3))


if __name__ == "__main__":
    unittest.main()
