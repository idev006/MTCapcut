import unittest

from mtcapcut.studio_quality import longform_diversity_report, validate_longform_diversity


class StudioQualityTests(unittest.TestCase):
    def test_revised_candidate_cannot_reintroduce_repeated_picture(self):
        candidate = {"segments": [
            {"kind": "picture", "asset_id": "photo-a", "duration_us": 5_000_000},
            {"kind": "picture", "asset_id": "photo-a", "duration_us": 5_000_000},
        ]}
        with self.assertRaisesRegex(ValueError, "repeats picture"):
            validate_longform_diversity(candidate)

    def test_distinct_video_starts_still_fail_if_source_intervals_overlap(self):
        candidate = {"segments": [
            {"kind": "video", "asset_id": "clip-a", "source_start_us": 0,
             "duration_us": 6_000_000},
            {"kind": "video", "asset_id": "clip-a", "source_start_us": 4_000_000,
             "duration_us": 6_000_000},
        ]}
        self.assertEqual(longform_diversity_report(candidate)["reused_video_source_us"], 2_000_000)
        with self.assertRaisesRegex(ValueError, "reuses video source time"):
            validate_longform_diversity(candidate)

    def test_small_boundary_overlap_remains_within_tolerance(self):
        candidate = {"segments": [
            {"kind": "video", "asset_id": "clip-a", "source_start_us": 0,
             "duration_us": 6_000_000},
            {"kind": "video", "asset_id": "clip-a", "source_start_us": 5_900_000,
             "duration_us": 6_000_000},
            {"kind": "picture", "asset_id": "photo-a", "duration_us": 5_000_000},
        ]}
        report = validate_longform_diversity(candidate)
        self.assertEqual(report["reused_video_source_us"], 100_000)
        self.assertEqual(report["unique_picture_assets"], 1)


if __name__ == "__main__":
    unittest.main()
