from pathlib import Path
import tempfile
import unittest

from mtcapcut.map import UnderstandingMap
from mtcapcut.media_readiness import MediaReadinessAssessor, semantic_observation_ids_for_range


class MediaReadinessTests(unittest.TestCase):
    def test_shot_rows_never_count_as_semantic_range_evidence(self):
        observations = [{"observation_id":"shot","asset_id":"v","modality":"shot",
                         "start_us":0,"end_us":20_000_000}]
        self.assertEqual(semantic_observation_ids_for_range(observations, "v", 12_000_000, 18_000_000), ())

    def test_semantic_evidence_must_overlap_source_range(self):
        observations = [{"observation_id":"vision","asset_id":"v","modality":"vision",
                         "start_us":8_000_000,"end_us":8_000_001}]
        self.assertEqual(semantic_observation_ids_for_range(observations, "v", 12_000_000, 18_000_000), ())
        self.assertEqual(semantic_observation_ids_for_range(observations, "v", 8_000_000, 9_000_000), ("vision",))

    def test_visual_range_does_not_accept_audio_only_evidence(self):
        observations = [{"observation_id":"sound", "asset_id":"v", "modality":"sound",
                         "start_us":0, "end_us":10_000_000}]
        self.assertEqual(semantic_observation_ids_for_range(
            observations, "v", 0, 5_000_000, frozenset({"vision", "ocr"})), ())

    def test_assessor_reports_unobserved_and_missing_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                mapping.add_asset({"asset_id":"p","path":str(root / "p.jpg"),"kind":"picture",
                    "role":"photo","source":"user","rights_status":"owned","content_hash":"h",
                    "size_bytes":1,"technical":{}})
                report = MediaReadinessAssessor(mapping).assess()
                self.assertEqual(report.status, "blocked")
                self.assertEqual(set(report.assets[0].blockers),
                                 {"no_semantic_observations", "external_ai_policy_missing"})


if __name__ == "__main__":
    unittest.main()
