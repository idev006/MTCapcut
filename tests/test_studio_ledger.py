from pathlib import Path
import tempfile
import unittest

from mtcapcut.map import UnderstandingMap


class StudioLedgerTests(unittest.TestCase):
    def test_run_recommendations_and_completion_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "map.sqlite3"
            with UnderstandingMap(path) as mapping:
                run_id = mapping.start_studio_run("hash", "provider", "model", "v1", {"assets": []})
                mapping.append_studio_recommendation(run_id, {"recommendation_id":"r1","role":"story"})
                mapping.complete_studio_run(run_id, {"premise":"p"}, {"authorship":"autonomous_studio"})
                with self.assertRaises(ValueError):
                    mapping.append_studio_recommendation(run_id, {"recommendation_id":"r2","role":"story"})
            with UnderstandingMap(path) as reopened:
                result = reopened.get_studio_run(run_id)
                self.assertEqual(result["status"], "candidate_ready")
                self.assertEqual(result["recommendations"][0]["recommendation_id"], "r1")

    def test_failed_run_preserves_error_and_cannot_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            with UnderstandingMap(Path(folder) / "map.sqlite3") as mapping:
                run_id = mapping.start_studio_run("hash", "provider", "model", "v1", {})
                mapping.fail_studio_run(run_id, "provider failed")
                with self.assertRaises(ValueError):
                    mapping.complete_studio_run(run_id, {}, {})
                self.assertEqual(mapping.get_studio_run(run_id)["status"], "failed")


if __name__ == "__main__":
    unittest.main()
