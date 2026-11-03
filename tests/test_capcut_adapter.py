from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from mtcapcut.capcut_adapter import SANDBOX_MARKER, create_draft
from mtcapcut.timeline import Segment, TimelinePlan


FFMPEG = Path("D:/libs/ffmpeg/bin/ffmpeg.exe")


class CapCutAdapterTests(unittest.TestCase):
    def test_rejects_unmarked_root_and_existing_draft(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan = TimelinePlan(1080, 1920, 30, (Segment("picture", 0, 1_000_000, "main", "pic1", root / "missing.png"),))
            with self.assertRaises(ValueError):
                create_draft(plan, root, "draft")
            (root / SANDBOX_MARKER).touch()
            (root / "draft").mkdir()
            with self.assertRaises(FileExistsError):
                create_draft(plan, root, "draft")

    @unittest.skipUnless(FFMPEG.is_file(), "FFmpeg executable unavailable")
    def test_creates_editable_draft_with_picture_audio_and_thai_text(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / SANDBOX_MARKER).touch()
            picture = root / "picture.png"
            sound = root / "sound.mp3"
            video = root / "clip.mp4"
            subprocess.run([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                            "-i", "color=c=blue:s=320x240:d=1", "-frames:v", "1", str(picture)], check=True)
            subprocess.run([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                            "-i", "sine=frequency=440:duration=2", str(sound)], check=True)
            subprocess.run([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                            "-i", "color=c=red:s=320x240:r=30:d=1", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", str(video)], check=True)
            plan = TimelinePlan(1080, 1920, 30, (
                Segment("video", 0, 1_000_000, "main", "vid1", video),
                Segment("picture", 1_000_000, 1_000_000, "main", "pic1", picture),
                Segment("audio", 0, 2_000_000, "music", "aud1", sound),
                Segment("text", 0, 2_000_000, "titles", text="รายงานความคืบหน้า"),
            ))
            draft = create_draft(plan, root, "test-draft")
            data = json.loads((draft / "draft_content.json").read_text(encoding="utf-8"))
            self.assertEqual(data["duration"], 2_000_000)
            self.assertEqual(len(data["tracks"]), 3)
            self.assertIn("รายงานความคืบหน้า", (draft / "draft_content.json").read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                create_draft(plan, root, "test-draft")


if __name__ == "__main__":
    unittest.main()
