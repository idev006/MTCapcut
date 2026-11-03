import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class BundleCliTests(unittest.TestCase):
    def test_ingest_bundle_and_list_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            brief = root / "บรีฟ.txt"
            brief.write_text("งานยังดำเนินการ", encoding="utf-8")
            manifest = root / "assets.json"
            manifest.write_text(json.dumps([{"path": "บรีฟ.txt", "role": "confirmed_facts"}]), encoding="utf-8")
            config = root / "config.toml"
            config.write_text(
                'schema_version=1\n[paths]\nworkspace="' + (root / "work").as_posix() +
                '"\n[ffmpeg]\nffprobe="D:/libs/ffmpeg/bin/ffprobe.exe"\n'
                '[capcut]\napps_root="C:/Users/acer/AppData/Local/CapCut/Apps"\n', encoding="utf-8")
            if not Path("D:/libs/ffmpeg/bin/ffprobe.exe").is_file():
                self.skipTest("ffprobe unavailable")
            base = [sys.executable, "-m", "mtcapcut", "--config", str(config)]
            first = subprocess.run(base + ["ingest-bundle", "test", str(manifest)],
                                   capture_output=True, text=True, encoding="utf-8", check=True)
            first_record = json.loads(first.stdout)[0]
            second = subprocess.run(base + ["ingest-bundle", "test", str(manifest)],
                                    capture_output=True, text=True, encoding="utf-8", check=True)
            self.assertEqual(json.loads(second.stdout)[0]["asset_id"], first_record["asset_id"])
            self.assertFalse(json.loads(second.stdout)[0]["changed"])
            listing = subprocess.run(base + ["assets", "test"], capture_output=True, text=True,
                                     encoding="utf-8", check=True)
            self.assertEqual(len(json.loads(listing.stdout)), 1)
            self.assertIn("บรีฟ.txt", listing.stdout)


if __name__ == "__main__":
    unittest.main()
