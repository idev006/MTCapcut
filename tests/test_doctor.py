from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from mtcapcut.config import Config
from mtcapcut.config import load_config
from mtcapcut.doctor import diagnose


class DoctorTests(unittest.TestCase):
    def test_reports_required_components_without_mutating_environment(self):
        config = Config(
            Path("D:/dev/MTCapcut/workspace"),
            Path("D:/libs/ffmpeg/bin/ffprobe.exe"),
            Path("C:/Users/acer/AppData/Local/CapCut/Apps"),
        )
        report = diagnose(config)
        self.assertIn("python", report["checks"])
        self.assertIn("ffmpeg", report["checks"])
        self.assertEqual(report["checks"]["pycapcut"]["required"], "0.0.4")

    def test_missing_dependencies_produce_failed_report(self):
        missing = Path("Z:/definitely-missing-mtcapcut")
        with patch("mtcapcut.doctor.version", side_effect=Exception("unexpected")):
            # Unknown package metadata errors must remain visible to callers.
            with self.assertRaises(Exception):
                diagnose(Config(missing / "work", missing / "ffprobe.exe", missing / "apps"))
        report = diagnose(Config(missing / "work", missing / "ffprobe.exe", missing / "apps"))
        self.assertFalse(report["ok"])
        self.assertFalse(report["checks"]["ffmpeg"]["ok"])
        self.assertFalse(report["checks"]["capcut"]["ok"])

    def test_doctor_can_load_config_when_ffprobe_is_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config_path = root / "config.toml"
            config_path.write_text(
                'schema_version=1\n[paths]\nworkspace="' + (root / "work").as_posix() +
                '"\n[ffmpeg]\nffprobe="' + (root / "missing-ffprobe.exe").as_posix() +
                '"\n[capcut]\napps_root="' + (root / "missing-capcut").as_posix() + '"\n',
                encoding="utf-8",
            )
            config = load_config(config_path, validate_paths=False)
            self.assertFalse(diagnose(config)["ok"])

    def test_doctor_cli_returns_json_and_failure_code_for_missing_binary(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config_path = root / "config.toml"
            config_path.write_text(
                'schema_version=1\n[paths]\nworkspace="' + (root / "work").as_posix() +
                '"\n[ffmpeg]\nffprobe="' + (root / "missing-ffprobe.exe").as_posix() +
                '"\n[capcut]\napps_root="' + (root / "missing-capcut").as_posix() + '"\n',
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "-m", "mtcapcut", "--config", str(config_path), "doctor"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["ok"])
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
