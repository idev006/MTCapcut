import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

from mtcapcut.assets import InputAsset, inspect_asset
from mtcapcut.config import Config, load_config
from mtcapcut.map import UnderstandingMap


class FoundationTests(unittest.TestCase):
    def test_real_ffprobe_media_intake(self):
        ffmpeg = Path("D:/libs/ffmpeg/bin/ffmpeg.exe")
        ffprobe = Path("D:/libs/ffmpeg/bin/ffprobe.exe")
        if not ffmpeg.is_file() or not ffprobe.is_file():
            self.skipTest("FFmpeg binaries unavailable")
        with tempfile.TemporaryDirectory() as folder:
            media = Path(folder) / "เสียงทดสอบ.mp3"
            subprocess.run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                            "-i", "sine=frequency=440:duration=1", "-metadata", "title=เสียงภาษาไทย",
                            "-y", str(media)], check=True)
            asset = inspect_asset(InputAsset(media, "music"), Config(Path(folder), ffprobe, Path(folder)))
            self.assertEqual(asset["kind"], "audio")
            self.assertEqual(asset["technical"]["format"]["tags"]["title"], "เสียงภาษาไทย")
            self.assertTrue(any(stream["codec_type"] == "audio" for stream in asset["technical"]["streams"]))

    def test_config_and_text_intake(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            executable = root / "ffprobe.exe"
            executable.write_bytes(b"test")
            config_path = root / "config.toml"
            config_path.write_text(
                'schema_version = 1\n[paths]\nworkspace = "' + root.as_posix() +
                '"\n[ffmpeg]\nffprobe = "' + executable.as_posix() +
                '"\n[capcut]\napps_root = "' + root.as_posix() + '"\n', encoding="utf-8")
            config = load_config(config_path)
            brief = root / "brief.txt"
            brief.write_text("กำลังดำเนินการ", encoding="utf-8")
            asset = inspect_asset(InputAsset(brief, "confirmed_facts"), config)
            self.assertEqual(asset["kind"], "text")
            self.assertEqual(len(asset["content_hash"]), 64)
            with self.assertRaises(ValueError):
                inspect_asset(InputAsset(brief, "unclassified"), config)

    def test_map_transaction_and_trace(self):
        with tempfile.TemporaryDirectory() as folder:
            with UnderstandingMap(Path(folder) / "map.sqlite3") as mapping:
                asset_id = mapping.add_asset({"asset_id": "a1", "path": "brief.txt", "kind": "text",
                    "role": "confirmed_facts", "source": "user", "rights_status": "owned",
                    "content_hash": "abc", "size_bytes": 3, "technical": {}})
                with self.assertRaises(ValueError):
                    mapping.add_observations(asset_id, [
                        {"modality": "text", "text": "กำลังดำเนินการ", "producer": "reader", "producer_version": "1"},
                        {"modality": "video", "text": "bad", "start_us": 5, "end_us": 2,
                         "producer": "vision", "producer_version": "1"},
                    ])
                self.assertEqual(mapping.asset_timeline(asset_id), [])
                observation_id = mapping.add_observations(asset_id, [
                    {"modality": "text", "text": "กำลังดำเนินการ", "producer": "reader", "producer_version": "1"}
                ])[0]
                claim_id = mapping.add_claim("งานกำลังดำเนินการ", [(observation_id, "supports")], "ข้อความที่ผู้ใช้ให้")
                result = mapping.explain_claim(claim_id)
                self.assertEqual(result["evidence"][0]["asset_id"], asset_id)
                self.assertEqual(result["status"], "inferred")
                mapping.review("claim", claim_id, "user", "verify", "ยืนยันสถานะ")
                self.assertEqual(mapping.connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0], 1)
                with self.assertRaises(sqlite3.IntegrityError):
                    mapping.add_claim("unsupported", [("missing", "supports")], "bad reference")
                self.assertEqual(mapping.connection.execute("SELECT COUNT(*) FROM claims").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
