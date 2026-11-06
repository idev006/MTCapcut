import unittest

from mtcapcut.studio_quality import (longform_diversity_report,
                                     validate_longform_diversity, visual_evidence_report)


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

    def test_one_sampled_frame_is_not_counted_as_a_five_second_observed_shot(self):
        candidate = {"segments": [{"segment_id":"s1", "kind":"video", "asset_id":"v",
                                   "source_start_us":0, "duration_us":5_000_000}]}
        observations = [{"asset_id":"v", "modality":"vision", "start_us":1_000_000,
                         "end_us":1_000_001, "observation_id":"frame"},
                        {"asset_id":"v", "modality":"speech", "start_us":0,
                         "end_us":5_000_000, "observation_id":"audio"}]
        report = visual_evidence_report(candidate, observations)
        self.assertEqual(report["observed_video_source_us"], 1)
        self.assertEqual(report["shots"][0]["status"], "sampled_only")
        self.assertEqual(report["sampled_only_shot_count"], 1)

    def test_overlapping_visual_observations_are_not_double_counted(self):
        candidate = {"segments": [{"segment_id":"s1", "kind":"video", "asset_id":"v",
                                   "source_start_us":0, "duration_us":5_000_000}]}
        observations = [{"asset_id":"v", "modality":"vision", "start_us":0,
                         "end_us":3_000_000},
                        {"asset_id":"v", "modality":"ocr", "start_us":2_000_000,
                         "end_us":5_000_000}]
        report = visual_evidence_report(candidate, observations)
        self.assertEqual(report["observed_video_source_us"], 5_000_000)
        self.assertEqual(report["shots"][0]["status"], "observed_interval")


if __name__ == "__main__":
    unittest.main()
