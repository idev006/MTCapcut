from pathlib import Path
import tempfile
import unittest

from mtcapcut.assets import InputAsset, inspect_bundle
from mtcapcut.config import Config
from mtcapcut.map import UnderstandingMap


class AssetMapVersionTests(unittest.TestCase):
    def test_bundle_inspects_before_registration_and_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            text = root / "brief.txt"
            text.write_text("เริ่มงาน", encoding="utf-8")
            config = Config(root, root / "ffprobe.exe", root)
            with self.assertRaises(FileNotFoundError):
                inspect_bundle([InputAsset(text, "brief"), InputAsset(root / "missing.txt", "brief")], config)
            with self.assertRaises(ValueError):
                inspect_bundle([InputAsset(text, "brief"), InputAsset(text, "brief")], config)
            self.assertEqual(inspect_bundle([InputAsset(text, "brief")], config)[0]["kind"], "text")

    def test_version_change_preserves_old_evidence_and_invalidates_current_view(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            text = root / "facts.txt"
            text.write_text("กำลังดำเนินการ", encoding="utf-8")
            config = Config(root, root / "ffprobe.exe", root)
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                first = mapping.register_bundle(inspect_bundle([InputAsset(text, "confirmed_facts")], config))[0]
                obs = mapping.add_observations(first["asset_id"], [{"modality": "text", "text": "กำลังดำเนินการ",
                    "producer": "text-reader", "producer_version": "1"}])[0]
                claim = mapping.add_claim("งานยังดำเนินการ", [(obs, "supports")], "user text")
                self.assertEqual(len(mapping.current_asset_timeline(first["asset_id"])), 1)
                same = mapping.register_bundle(inspect_bundle([InputAsset(text, "confirmed_facts")], config))[0]
                self.assertFalse(same["changed"])
                self.assertEqual(same["asset_version_id"], first["asset_version_id"])
                text.write_text("งานแล้วเสร็จ", encoding="utf-8")
                changed = mapping.register_bundle(inspect_bundle([InputAsset(text, "confirmed_facts")], config))[0]
                self.assertEqual(changed["asset_id"], first["asset_id"])
                self.assertNotEqual(changed["asset_version_id"], first["asset_version_id"])
                self.assertEqual(mapping.current_asset_timeline(first["asset_id"]), [])
                self.assertEqual(len(mapping.asset_timeline(first["asset_id"])), 1)
                previous_evidence = mapping.explain_claim(claim)["evidence"][0]
                self.assertEqual(previous_evidence["observation_id"], obs)
                self.assertFalse(previous_evidence["source_is_current"])
                self.assertEqual(len(mapping.list_assets()), 1)

    def test_bundle_transaction_and_artifact_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            asset = {"asset_id": "a1", "path": "a.txt", "kind": "text", "role": "brief",
                     "source": "user", "rights_status": "unknown", "content_hash": "abc",
                     "size_bytes": 3, "technical": {}}
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                with self.assertRaises(KeyError):
                    mapping.register_bundle([asset, {key: value for key, value in {**asset, "asset_id": "a2", "path": "b.txt", "role": "caption"}.items() if key != "size_bytes"}])
                self.assertEqual(mapping.list_assets(), [])
                mapping.register_bundle([asset])
                artifact = mapping.register_artifact("a1", "thumbnail", "frame.png", "def", "ffmpeg", "1", "cfg")
                row = mapping.connection.execute("SELECT producer,content_hash FROM artifacts WHERE artifact_id=?", (artifact,)).fetchone()
                self.assertEqual(row, ("ffmpeg", "def"))


if __name__ == "__main__":
    unittest.main()
