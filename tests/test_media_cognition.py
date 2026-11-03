from pathlib import Path
import tempfile
import unittest

from mtcapcut.ai_provider import ChatResponse
from mtcapcut.config import AIProviderSettings
from mtcapcut.media_cognition import MediaCognitionEngine
from mtcapcut.perception import EvidenceArtifact


class FakeProvider:
    def __init__(self, text, base_url="http://127.0.0.1:8000/v1"):
        self.text = text
        self.requests = []
        self.settings = AIProviderSettings(
            "test", "local_openai", base_url, "test-model", enabled=True,
        )

    def complete(self, request):
        self.requests.append(request)
        return ChatResponse("test", "test-model", self.text)


class MediaCognitionTests(unittest.TestCase):
    def test_frame_becomes_validated_structured_observations(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "frame.jpg"
            path.write_bytes(b"fake-image")
            provider = FakeProvider(
                '{"observations":[{"modality":"vision","text":"two people in a room","confidence":0.8}]}'
            )
            result = MediaCognitionEngine(provider).analyze(
                EvidenceArtifact("frame", 5_000_000, 5_000_000, path, "hash")
            )
            self.assertEqual(result[0].start_us, 5_000_000)
            self.assertEqual(result[0].end_us, 5_000_001)
            self.assertEqual(result[0].modality, "vision")
            content = provider.requests[0].messages[1].content
            self.assertEqual(content[1]["type"], "image_url")
            self.assertTrue(content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))

    def test_invalid_response_and_open_ended_audio_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "audio.wav"
            path.write_bytes(b"fake-audio")
            engine = MediaCognitionEngine(FakeProvider("not-json"))
            with self.assertRaises(ValueError):
                engine.analyze(EvidenceArtifact("audio", 0, -1, path, "hash"))
            with self.assertRaises(ValueError):
                MediaCognitionEngine(FakeProvider('{"observations":[]}')).analyze(
                    EvidenceArtifact("audio", 0, 1_000_000, path, "hash")
                )

    def test_empty_ocr_row_is_ignored_when_a_factual_row_exists(self):
        result = MediaCognitionEngine._validated(
            '{"observations":['
            '{"modality":"ocr","text":"","confidence":0.9},'
            '{"modality":"vision","text":"a person is standing","confidence":0.7}'
            ']}', 0, 1,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].modality, "vision")

    def test_json_fence_is_unwrapped_and_zero_confidence_placeholder_is_dropped(self):
        result = MediaCognitionEngine._validated(
            '```json\n{"observations":['
            '{"modality":"speech","text":"Transcription of speech content","confidence":0.0},'
            '{"modality":"music","text":"A steady drum beat is audible","confidence":0.75}'
            ']}\n```', 0, 10,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "A steady drum beat is audible")

    def test_external_provider_without_policy_gate_fails_before_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "frame.jpg"
            path.write_bytes(b"fake-image")
            provider = FakeProvider('{"observations":[]}', "https://example.invalid/v1")
            with self.assertRaises(PermissionError):
                MediaCognitionEngine(provider).analyze(
                    EvidenceArtifact("frame", 0, 0, path, "hash"), asset_id="asset-1",
                )
            self.assertEqual(provider.requests, [])


if __name__ == "__main__":
    unittest.main()
