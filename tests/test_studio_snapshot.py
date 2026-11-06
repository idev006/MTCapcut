from pathlib import Path
import tempfile
import unittest

from mtcapcut.config import AIProviderSettings, Config, SecuritySettings, DataPolicySettings
from mtcapcut.data_policy import DataPolicyGate
from mtcapcut.map import UnderstandingMap
from mtcapcut.studio_snapshot import authorize_studio_snapshot, build_studio_snapshot


class StudioSnapshotTests(unittest.TestCase):
    def test_snapshot_is_deterministic_current_and_contains_no_raw_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            mapping = UnderstandingMap(root / "map.sqlite3")
            mapping.add_asset({"asset_id":"a1","path":str(root / "secret.mp4"),"kind":"clip","role":"footage",
                "source":"user","rights_status":"private","content_hash":"hash","size_bytes":3,
                "technical":{"format":{"duration":"2.5"},"streams":[{"codec_type":"video","width":10,"height":20}]}})
            mapping.add_observations("a1", [{"modality":"vision","start_us":0,"end_us":1,
                "text":"one person","confidence":0.8,"producer":"eye","producer_version":"1"}])
            first = build_studio_snapshot(mapping)
            second = build_studio_snapshot(mapping)
            mapping.close()
            self.assertEqual(first.content_hash, second.content_hash)
            self.assertNotIn("secret.mp4", str(first.document))
            self.assertEqual(first.document["assets"][0]["duration_us"], 2_500_000)
            self.assertEqual(len(first.evidence_ids), 1)

    def test_external_snapshot_requires_policy_for_every_asset(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                for asset_id in ("a1", "a2"):
                    mapping.add_asset({"asset_id":asset_id,"path":asset_id,"kind":"text","role":"brief",
                        "source":"user","rights_status":"owned","content_hash":asset_id,
                        "size_bytes":2,"technical":{}})
                config = Config(root, root / "ffprobe.exe", root,
                                security=SecuritySettings(allow_remote_ai=True))
                gate = DataPolicyGate(config, mapping)
                remote = AIProviderSettings("remote", "local_openai", "https://example.invalid/v1", "model")
                snapshot = build_studio_snapshot(mapping)
                mapping.set_asset_ai_policy("a1", "internal_test", True, "owner", "test")
                with self.assertRaises(PermissionError):
                    authorize_studio_snapshot(gate, remote, snapshot)
                mapping.set_asset_ai_policy("a2", "internal_test", True, "owner", "test")
                authorize_studio_snapshot(gate, remote, snapshot)

    def test_authority_selection_excludes_superseded_text_and_unobserved_media(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                for asset_id, kind, role in (("brief-old", "text", "brief"),
                                             ("brief-active", "text", "brief"),
                                             ("unseen", "picture", "event_photo")):
                    mapping.add_asset({"asset_id":asset_id,"path":asset_id,"kind":kind,"role":role,
                        "source":"user","rights_status":"owned","content_hash":asset_id,
                        "size_bytes":1,"technical":{}})
                mapping.add_observations("brief-active", [{"modality":"text","text":"active",
                    "producer":"reader","producer_version":"1"}])
                snapshot = build_studio_snapshot(mapping, {"brief-active"})
                self.assertEqual(snapshot.asset_ids, {"brief-active"})

    def test_external_snapshot_checks_full_outbound_payload_size(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                for asset_id in ("a1", "a2"):
                    mapping.add_asset({"asset_id":asset_id, "path":asset_id, "kind":"text",
                        "role":"brief", "source":"user", "rights_status":"owned",
                        "content_hash":asset_id, "size_bytes":2, "technical":{}})
                    mapping.set_asset_ai_policy(asset_id, "internal_test", True, "owner", "test")
                config = Config(root, root / "ffprobe.exe", root,
                    security=SecuritySettings(allow_remote_ai=True),
                    data_policy=DataPolicySettings(max_evidence_bytes=250))
                remote = AIProviderSettings("remote", "local_openai", "https://example.invalid/v1", "model")
                snapshot = build_studio_snapshot(mapping)
                with self.assertRaisesRegex(PermissionError, "size limit"):
                    authorize_studio_snapshot(DataPolicyGate(config, mapping), remote, snapshot)

    def test_word_level_transcript_stays_local_to_avoid_large_studio_prompt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with UnderstandingMap(root / "map.sqlite3") as mapping:
                mapping.add_asset({"asset_id":"a", "path":str(root / "a.wav"), "kind":"audio",
                    "role":"speech", "source":"user", "rights_status":"owned",
                    "content_hash":"h", "size_bytes":1, "technical":{}})
                mapping.add_observations("a", [
                    {"modality":"speech", "text":"hello", "start_us":0, "end_us":1_000_000,
                     "producer":"ear", "producer_version":"1"},
                    {"modality":"speech_word", "text":"hello", "start_us":0, "end_us":500_000,
                     "producer":"ear", "producer_version":"1"},
                ])
                snapshot = build_studio_snapshot(mapping)
                self.assertEqual([row["modality"] for row in snapshot.document["observations"]], ["speech"])


if __name__ == "__main__":
    unittest.main()
