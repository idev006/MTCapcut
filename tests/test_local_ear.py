from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from mtcapcut.config import LocalEarSettings
from mtcapcut.local_ear import FasterWhisperEar
from mtcapcut.perception import EvidenceArtifact


class FakeWhisperModel:
    def transcribe(self, path, **kwargs):
        return iter([
            SimpleNamespace(text=" สวัสดีครับ ", start=0.5, end=1.75,
                            avg_logprob=-0.1, no_speech_prob=0.05),
            SimpleNamespace(text="", start=2.0, end=2.5,
                            avg_logprob=-0.1, no_speech_prob=0.0),
        ]), SimpleNamespace(language="th")


class LocalEarTests(unittest.TestCase):
    def test_local_ear_offsets_segments_to_source_time(self):
        calls = []

        def factory(model_size, **kwargs):
            calls.append((model_size, kwargs))
            return FakeWhisperModel()

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "audio.wav"
            path.write_bytes(b"audio")
            ear = FasterWhisperEar(
                LocalEarSettings(enabled=True, model_size="small", device="cpu", compute_type="int8"),
                model_factory=factory,
            )
            result = ear.transcribe(EvidenceArtifact("audio", 30_000_000, 45_000_000, path, "hash"))
        self.assertEqual(calls[0][0], "small")
        self.assertEqual(calls[0][1]["compute_type"], "int8")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "สวัสดีครับ")
        self.assertEqual((result[0].start_us, result[0].end_us), (30_500_000, 31_750_000))
        self.assertGreater(result[0].confidence, 0.8)

    def test_local_ear_rejects_disabled_and_open_ended_inputs(self):
        with self.assertRaises(ValueError):
            FasterWhisperEar(LocalEarSettings(enabled=False))
        ear = FasterWhisperEar(LocalEarSettings(enabled=True), model_factory=lambda *args, **kwargs: FakeWhisperModel())
        with self.assertRaises(ValueError):
            ear.transcribe(EvidenceArtifact("audio", 0, -1, Path("missing.wav"), "hash"))

    def test_low_confidence_transcription_is_rejected(self):
        class LowConfidenceModel:
            def transcribe(self, path, **kwargs):
                return iter([SimpleNamespace(
                    text="uncertain", start=0.0, end=1.0,
                    avg_logprob=-3.0, no_speech_prob=0.2,
                )]), SimpleNamespace(language="th")

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "audio.wav"
            path.write_bytes(b"audio")
            ear = FasterWhisperEar(
                LocalEarSettings(enabled=True, min_confidence=0.25),
                model_factory=lambda *args, **kwargs: LowConfidenceModel(),
            )
            result = ear.transcribe(EvidenceArtifact("audio", 0, 1_000_000, path, "hash"))
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
