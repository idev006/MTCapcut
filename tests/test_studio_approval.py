from pathlib import Path
import json
import tempfile
import unittest

from mtcapcut.map import UnderstandingMap
from mtcapcut.studio_approval import authorize_private_preview


class StudioApprovalTests(unittest.TestCase):
    def test_blocked_candidate_requires_append_only_human_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "candidate.json"
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                run_id = mapping.start_studio_run("hash", "provider", "model", "v1", {})
                candidate = {"authorship":"autonomous_studio","studio_run_id":run_id,
                             "brief_compliance":{"status":"pass"},
                             "gates":{"private_preview_eligible":False},"segments":[]}
                mapping.complete_studio_run(run_id, {"premise":"p"}, candidate)
                path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(PermissionError):
                    authorize_private_preview(mapping, path)
                mapping.review_studio_run(run_id, "private_preview", "approve", "owner", "private test")
                self.assertEqual(authorize_private_preview(mapping, path)["studio_run_id"], run_id)
                mapping.review_studio_run(run_id, "private_preview", "reject", "owner", "withdrawn")
                with self.assertRaises(PermissionError):
                    authorize_private_preview(mapping, path)

    def test_tampered_candidate_is_denied_even_with_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "candidate.json"
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                run_id = mapping.start_studio_run("hash", "provider", "model", "v1", {})
                candidate = {"authorship":"autonomous_studio","studio_run_id":run_id,
                             "brief_compliance":{"status":"pass"},
                             "gates":{"private_preview_eligible":False},"segments":[]}
                mapping.complete_studio_run(run_id, {}, candidate)
                mapping.review_studio_run(run_id, "private_preview", "approve", "owner", "test")
                path.write_text(json.dumps({**candidate, "tampered":True}), encoding="utf-8")
                with self.assertRaises(PermissionError):
                    authorize_private_preview(mapping, path)

    def test_legacy_candidate_without_brief_compliance_is_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "candidate.json"
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                run_id = mapping.start_studio_run("hash", "provider", "model", "v1", {})
                candidate = {"authorship":"autonomous_studio","studio_run_id":run_id,
                             "gates":{"private_preview_eligible":True},"segments":[]}
                mapping.complete_studio_run(run_id, {}, candidate)
                path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(PermissionError):
                    authorize_private_preview(mapping, path)


if __name__ == "__main__":
    unittest.main()
