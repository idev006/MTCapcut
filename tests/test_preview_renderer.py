from pathlib import Path
import subprocess
import tempfile
import unittest

from mtcapcut.preview_renderer import PreviewRenderEngine
from mtcapcut.timeline import Segment, TimelinePlan


class PreviewRendererTests(unittest.TestCase):
    def test_builds_one_music_review_render_without_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            ffmpeg = root / "ffmpeg.exe"
            ffmpeg.touch()
            picture = root / "picture.jpg"
            picture.touch()
            music = root / "music.mp3"
            music.touch()
            output = root / "preview.mp4"
            calls = []

            def runner(command, **_):
                calls.append(command)
                output.write_bytes(b"mp4")
                return subprocess.CompletedProcess(command, 0, "", "")

            plan = TimelinePlan(1280, 720, 30, (
                Segment("picture", 0, 2_000_000, "main", "picture-1", picture),
                Segment("audio", 0, 2_000_000, "music", "music-1", music),
                Segment("text", 200_000, 1_000_000, "titles", text="ทดสอบระบบ"),
            ))
            result = PreviewRenderEngine(ffmpeg, runner).render(plan, output)
            self.assertEqual(result.visual_count, 1)
            self.assertEqual(result.audio_count, 1)
            self.assertIn("PRIVATE PREVIEW", result.title_artifact.read_text(encoding="utf-8-sig"))
            self.assertIn("loudnorm=I=-16", calls[0][calls[0].index("-filter_complex") + 1])
            with self.assertRaises(FileExistsError):
                PreviewRenderEngine(ffmpeg, runner).render(plan, output)

    def test_rejects_multiple_music_tracks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            ffmpeg = root / "ffmpeg.exe"
            ffmpeg.touch()
            media = root / "media.bin"
            media.touch()
            plan = TimelinePlan(1280, 720, 30, (
                Segment("picture", 0, 1_000_000, "main", "picture", media),
                Segment("audio", 0, 1_000_000, "music-a", "a", media),
                Segment("audio", 0, 1_000_000, "music-b", "b", media),
            ))
            with self.assertRaises(ValueError):
                PreviewRenderEngine(ffmpeg).render(plan, root / "preview.mp4")


if __name__ == "__main__":
    unittest.main()
