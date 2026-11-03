from pathlib import Path
import tempfile
import unittest

from mtcapcut.config import AIProviderSettings, Config, DataPolicySettings, SecuritySettings
from mtcapcut.data_policy import DataPolicyGate
from mtcapcut.map import UnderstandingMap


def asset(asset_id="asset-1"):
    return {"asset_id": asset_id, "path": "asset.jpg", "kind": "picture", "role": "visual",
            "source": "user", "rights_status": "unknown", "content_hash": "abc",
            "size_bytes": 3, "technical": {}}


class DataPolicyTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        root = Path(self.folder.name)
        self.mapping = UnderstandingMap(root / "map.sqlite3")
        self.mapping.add_asset(asset())
        self.config = Config(
            root, root / "ffprobe.exe", root,
            security=SecuritySettings(allow_remote_ai=True),
            data_policy=DataPolicySettings(max_evidence_bytes=100),
        )
        self.remote = AIProviderSettings("remote", "local_openai", "https://example.invalid/v1", "model")
        self.local = AIProviderSettings("local", "local_openai", "http://127.0.0.1:8000/v1", "model")
        self.gate = DataPolicyGate(self.config, self.mapping)

    def tearDown(self):
        self.mapping.close()
        self.folder.cleanup()

    def test_missing_policy_is_denied_and_local_loopback_is_allowed(self):
        with self.assertRaises(PermissionError):
            self.gate.authorize(self.remote, "asset-1", 10)
        decision = self.gate.authorize(self.local, "asset-1", 10)
        self.assertFalse(decision.external)

    def test_explicit_allowed_classification_authorizes_external_evidence(self):
        policy_id = self.mapping.set_asset_ai_policy(
            "asset-1", "public_source", True, "owner", "approved test",
        )
        decision = self.gate.authorize(self.remote, "asset-1", 10)
        self.assertTrue(decision.external)
        self.assertEqual(decision.policy_id, policy_id)

    def test_latest_append_only_policy_can_revoke_approval(self):
        self.mapping.set_asset_ai_policy("asset-1", "internal_test", True, "owner", "initial")
        self.mapping.set_asset_ai_policy("asset-1", "internal_test", False, "owner", "revoked")
        with self.assertRaises(PermissionError):
            self.gate.authorize(self.remote, "asset-1", 10)
        count = self.mapping.connection.execute(
            "SELECT COUNT(*) FROM asset_ai_policies WHERE asset_id='asset-1'"
        ).fetchone()[0]
        self.assertEqual(count, 2)

    def test_restricted_and_oversized_evidence_are_denied(self):
        self.mapping.set_asset_ai_policy("asset-1", "restricted", True, "owner", "classification")
        with self.assertRaises(PermissionError):
            self.gate.authorize(self.remote, "asset-1", 10)
        self.mapping.set_asset_ai_policy("asset-1", "public_source", True, "owner", "reclassified")
        with self.assertRaises(PermissionError):
            self.gate.authorize(self.remote, "asset-1", 101)

    def test_central_remote_ai_switch_overrides_asset_approval(self):
        self.mapping.set_asset_ai_policy("asset-1", "public_source", True, "owner", "approved")
        blocked = Config(
            self.config.workspace, self.config.ffprobe, self.config.capcut_apps_root,
            security=SecuritySettings(allow_remote_ai=False),
        )
        with self.assertRaises(PermissionError):
            DataPolicyGate(blocked, self.mapping).authorize(self.remote, "asset-1", 10)


if __name__ == "__main__":
    unittest.main()
