from pathlib import Path
import tempfile
import unittest

from mtcapcut.config import load_config


class ConfigCategoryTests(unittest.TestCase):
    def test_grouped_config_loads_provider_profiles_without_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            ffprobe = root / "ffprobe.exe"
            ffprobe.touch()
            config_file = root / "config.toml"
            config_file.write_text(f'''schema_version = 2
[paths]
workspace = "{(root / 'workspace').as_posix()}"
[ffmpeg]
ffprobe = "{ffprobe.as_posix()}"
[capcut]
apps_root = "{root.as_posix()}"
[runtime]
max_workers = 3
[ui_bridge]
poll_interval_ms = 75
[shot_analysis]
enabled = true
threshold = 31.5
min_scene_len_frames = 12
frames_per_shot = 2
frame_width = 800
[ai]
default_provider = "local"
vision_model = "vision/model"
audio_model = "audio/model"
studio_model = "studio/model"
[ai.providers.local]
kind = "local_openai"
base_url = "http://127.0.0.1:11434/v1"
model = "qwen3:8b"
enabled = true
[ai.providers.openrouter]
kind = "openrouter"
base_url = "https://openrouter.ai/api/v1"
model = "vendor/model"
api_key_env = "OPENROUTER_API_KEY"
enabled = false
[storage]
journal_mode = "delete"
[security]
allow_remote_ai = false
[observability]
log_level = "INFO"
''', encoding="utf-8")
            config = load_config(config_file)
            self.assertEqual(config.runtime.max_workers, 3)
            self.assertEqual(config.ui_bridge.poll_interval_ms, 75)
            self.assertTrue(config.shot_analysis.enabled)
            self.assertEqual(config.shot_analysis.threshold, 31.5)
            self.assertEqual(config.shot_analysis.frames_per_shot, 2)
            self.assertEqual(config.ai.default_provider, "local")
            self.assertEqual(config.ai.vision_model, "vision/model")
            self.assertEqual(config.ai.audio_model, "audio/model")
            self.assertEqual(config.ai.studio_model, "studio/model")
            self.assertEqual(config.ai.providers["local"].model, "qwen3:8b")
            self.assertEqual(config.storage.journal_mode, "delete")
            self.assertEqual(config.workspace, (root / "workspace").resolve())

    def test_remote_plain_http_and_unknown_default_provider_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = f'''schema_version = 2
[paths]
workspace = "{root.as_posix()}"
[ffmpeg]
ffprobe = "{(root / 'ffprobe.exe').as_posix()}"
[capcut]
apps_root = "{root.as_posix()}"
[ai]
default_provider = "missing"
[ai.providers.remote]
kind = "local_openai"
base_url = "http://192.168.1.50:8000/v1"
model = "model"
enabled = true
'''
            path = root / "config.toml"
            path.write_text(base, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path, validate_paths=False)

    def test_openrouter_kind_cannot_redirect_secret_to_another_host(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "config.toml"
            path.write_text('''schema_version = 2
[paths]
workspace = "./workspace"
[ffmpeg]
ffprobe = "./ffprobe.exe"
[capcut]
apps_root = "./capcut"
[ai.providers.bad]
kind = "openrouter"
base_url = "https://example.invalid/api/v1"
model = "vendor/model"
api_key_env = "OPENROUTER_API_KEY"
enabled = false
''', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path, validate_paths=False)

    def test_toml_api_key_is_loaded_but_redacted_from_repr(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "config.toml"
            path.write_text('''schema_version = 2
[paths]
workspace = "./workspace"
[ffmpeg]
ffprobe = "./ffprobe.exe"
[capcut]
apps_root = "./capcut"
[ai.providers.openrouter]
kind = "openrouter"
base_url = "https://openrouter.ai/api/v1"
model = "vendor/model"
api_key = "toml-secret-value"
enabled = false
''', encoding="utf-8")
            provider = load_config(path, validate_paths=False).ai.providers["openrouter"]
            self.assertEqual(provider.api_key, "toml-secret-value")
            self.assertNotIn("toml-secret-value", repr(provider))

    def test_invalid_shot_analysis_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "config.toml"
            path.write_text('''schema_version = 2
[paths]
workspace = "./workspace"
[ffmpeg]
ffprobe = "./ffprobe.exe"
[capcut]
apps_root = "./capcut"
[shot_analysis]
threshold = 0
frames_per_shot = 11
''', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path, validate_paths=False)

    def test_invalid_data_policy_classification_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.toml"
            path.write_text('''schema_version = 2
[paths]
workspace = "./workspace"
[ffmpeg]
ffprobe = "./ffprobe.exe"
[capcut]
apps_root = "./capcut"
[data_policy]
allowed_external_classifications = ["secretish"]
''', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path, validate_paths=False)


if __name__ == "__main__":
    unittest.main()
