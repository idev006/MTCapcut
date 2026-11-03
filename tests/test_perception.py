from pathlib import Path
import subprocess
import tempfile
import unittest

from mtcapcut.perception import extract_audio, extract_frame


class PerceptionTests(unittest.TestCase):
    def test_timestamped_frame_and_audio_artifacts(self):
        ffmpeg = Path("D:/libs/ffmpeg/bin/ffmpeg.exe")
        if not ffmpeg.is_file():
            self.skipTest("FFmpeg unavailable")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.mp4"
            subprocess.run([str(ffmpeg), "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "testsrc=size=160x90:rate=10:duration=2",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                "-c:v", "mpeg4", "-c:a", "aac", "-shortest", str(source)], check=True)
            frame = extract_frame(ffmpeg, source, root / "evidence" / "frame.jpg", 500_000)
            audio = extract_audio(ffmpeg, source, root / "evidence" / "speech.wav",
                                  start_us=250_000, end_us=1_250_000)
            self.assertEqual(frame.source_start_us, 500_000)
            self.assertEqual(audio.source_end_us, 1_250_000)
            self.assertEqual(len(frame.content_hash), 64)
            self.assertGreater(audio.path.stat().st_size, 1000)
            with self.assertRaises(FileExistsError):
                extract_frame(ffmpeg, source, frame.path, 500_000)


if __name__ == "__main__":
    unittest.main()
