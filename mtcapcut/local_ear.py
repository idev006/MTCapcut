"""Local speech ear backed by faster-whisper with timestamped SSOT output."""

from dataclasses import dataclass
from hashlib import sha256
import json
from math import exp
from typing import Callable, Any

from .config import LocalEarSettings
from .map import UnderstandingMap
from .perception import EvidenceArtifact
from .take_review import WordToken


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

    @property
    def producer(self) -> str:
        """Stable ASR settings key for current-asset cache and provenance."""
        settings = {"model": self.settings.model_size, "language": self.settings.language,
                    "vad_filter": self.settings.vad_filter,
                    "min_confidence": self.settings.min_confidence,
                    "device": self.settings.device, "compute_type": self.settings.compute_type,
                    "engine_version": self.producer_version}
        digest = sha256(json.dumps(settings, sort_keys=True).encode("utf-8")).hexdigest()[:12]
        return f"faster-whisper:{self.settings.model_size}:{digest}"

    def transcribe(self, artifact: EvidenceArtifact) -> list[SpeechObservation]:
        return self.transcribe_detail(artifact)[0]

    def transcribe_detail(self, artifact: EvidenceArtifact) -> tuple[list[SpeechObservation], list[WordToken]]:
        if artifact.kind != "audio":
            raise ValueError("local ear requires an audio evidence artifact")
        if artifact.source_end_us <= artifact.source_start_us:
            raise ValueError("audio evidence requires a closed source time range")
        segments, _ = self._model().transcribe(
            str(artifact.path), language=self.settings.language,
            vad_filter=self.settings.vad_filter, word_timestamps=True,
        )
        output = []
        words: list[WordToken] = []
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
            for word in getattr(segment, "words", None) or ():
                word_text = str(getattr(word, "word", "")).strip()
                word_start = artifact.source_start_us + round(float(word.start) * 1_000_000)
                word_end = artifact.source_start_us + round(float(word.end) * 1_000_000)
                probability = float(getattr(word, "probability", confidence))
                if (word_text and word_start >= artifact.source_start_us
                        and word_end > word_start and word_end <= artifact.source_end_us
                        and 0 <= probability <= 1):
                    words.append(WordToken(word_text, word_start, word_end, probability))
        return output, words

    def transcribe_and_store(self, understanding: UnderstandingMap, asset_id: str,
                             artifact: EvidenceArtifact) -> list[str]:
        observations, words = self.transcribe_detail(artifact)
        if not observations:
            return []
        rows = [{
            "modality": "speech",
            "start_us": item.start_us,
            "end_us": item.end_us,
            "text": item.text,
            "confidence": item.confidence,
            "producer": self.producer,
            "producer_version": self.producer_version,
        } for item in observations]
        rows.extend({
            "modality": "speech_word", "start_us": item.start_us, "end_us": item.end_us,
            "text": item.text, "confidence": item.confidence,
            "producer": self.producer,
            "producer_version": self.producer_version,
        } for item in words)
        return understanding.add_observations(asset_id, rows)
