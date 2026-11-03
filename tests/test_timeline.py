import unittest
from pathlib import Path
import json
import tempfile

from mtcapcut.timeline import Segment, TimelinePlan, load_plan, validate_plan


class TimelineTests(unittest.TestCase):
    def test_valid_multitrack_plan(self):
        plan = TimelinePlan(1080, 1920, 30, (
            Segment("video", 0, 5_000_000, "main", "asset-1", Path("a.mp4")),
            Segment("picture", 5_000_000, 3_000_000, "main", "asset-2", Path("b.jpg")),
            Segment("audio", 0, 8_000_000, "music", "asset-3", Path("c.mp3")),
            Segment("text", 0, 2_000_000, "title", text="รายงานความคืบหน้า"),
        ))
        self.assertEqual(validate_plan(plan), [])
        self.assertEqual(plan.duration_us, 8_000_000)

    def test_overlap_and_missing_source_are_rejected(self):
        plan = TimelinePlan(1080, 1920, 30, (
            Segment("video", 0, 5_000_000, "main", "a", Path("a.mp4")),
            Segment("video", 4_000_000, 2_000_000, "main", "b", Path("b.mp4")),
            Segment("audio", 0, 1_000_000, "sound"),
        ))
        errors = validate_plan(plan)
        self.assertTrue(any("overlapping" in error for error in errors))
        self.assertTrue(any("source_path" in error for error in errors))

    def test_load_plan_resolves_media_relative_to_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            media = root / "image.png"
            media.touch()
            plan_file = root / "plan.json"
            plan_file.write_text(json.dumps({"width": 1080, "height": 1920, "fps": 30,
                "segments": [{"kind": "picture", "start_us": 0, "duration_us": 1_000_000,
                              "track": "main", "asset_id": "a", "source_path": "image.png"}]}), encoding="utf-8")
            plan = load_plan(plan_file)
            self.assertEqual(plan.segments[0].source_path, media.resolve())


if __name__ == "__main__":
    unittest.main()
