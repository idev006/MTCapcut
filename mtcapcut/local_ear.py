"""Local speech ear backed by faster-whisper with timestamped SSOT output."""

from dataclasses import dataclass
from math import exp
from typing import Callable, Any

from .config import LocalEarSettings
from .map import UnderstandingMap
from .perception import EvidenceArtifact


@dataclass(frozen=True)
class SpeechObservation:
    text: str
    start_us: int
    end_us: int
    confidence: float


class FasterWhisperEar:
    producer_version = "1"

    def __init__(self, settings: LocalEarSettings, *, model_factory: Callable[..., Any] | None = None):
        if not settings.enabled:
            raise ValueError("local ear is disabled")
        self.settings = settings
        self._model_factory = model_factory
        self._loaded_model = None

    def _model(self):
        if self._loaded_model is None:
            factory = self._model_factory
            if factory is None:
                from faster_whisper import WhisperModel
                factory = WhisperModel
            kwargs = {"device": self.settings.device, "compute_type": self.settings.compute_type}
            if self.settings.cache_dir is not None:
                self.settings.cache_dir.mkdir(parents=True, exist_ok=True)
                kwargs["download_root"] = str(self.settings.cache_dir)
            self._loaded_model = factory(self.settings.model_size, **kwargs)
        return self._loaded_model

    def transcribe(self, artifact: EvidenceArtifact) -> list[SpeechObservation]:
        if artifact.kind != "audio":
            raise ValueError("local ear requires an audio evidence artifact")
        if artifact.source_end_us <= artifact.source_start_us:
            raise ValueError("audio evidence requires a closed source time range")
        segments, _ = self._model().transcribe(
            str(artifact.path), language=self.settings.language,
            vad_filter=self.settings.vad_filter, word_timestamps=True,
        )
        output = []
        for segment in segments:
            text = str(segment.text).strip()
            start_us = artifact.source_start_us + round(float(segment.start) * 1_000_000)
            end_us = artifact.source_start_us + round(float(segment.end) * 1_000_000)
            if not text or end_us <= start_us:
                continue
            avg_logprob = float(getattr(segment, "avg_logprob", -10.0))
            no_speech = float(getattr(segment, "no_speech_prob", 0.0))
            confidence = max(0.0, min(1.0, exp(min(0.0, avg_logprob)) * (1.0 - no_speech)))
            if confidence < self.settings.min_confidence:
                continue
            output.append(SpeechObservation(text, start_us, end_us, confidence))
        return output

    def transcribe_and_store(self, understanding: UnderstandingMap, asset_id: str,
                             artifact: EvidenceArtifact) -> list[str]:
        observations = self.transcribe(artifact)
        if not observations:
            return []
        return understanding.add_observations(asset_id, [{
            "modality": "speech",
            "start_us": item.start_us,
            "end_us": item.end_us,
            "text": item.text,
            "confidence": item.confidence,
            "producer": f"faster-whisper:{self.settings.model_size}",
            "producer_version": self.producer_version,
        } for item in observations])
