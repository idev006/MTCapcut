"""AI-backed eyes and ears that produce validated SSOT observations.

This engine consumes evidence artifacts extracted by ``perception.py``. It is
the only layer allowed to convert pixels or waveforms into semantic proposals;
callers consume its structured observations instead of opening media directly.
"""

from base64 import b64encode
from dataclasses import dataclass
import json
from pathlib import Path

from .ai_provider import ChatMessage, ChatRequest, OpenAICompatibleProvider
from .data_policy import DataPolicyGate, provider_is_external
from .map import UnderstandingMap
from .perception import EvidenceArtifact


@dataclass(frozen=True)
class CognitionObservation:
    modality: str
    text: str
    confidence: float
    start_us: int
    end_us: int


_ALLOWED_MODALITIES = {"vision", "ocr", "speech", "sound", "music"}
_MIME_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".wav": "audio/wav", ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
}


class MediaCognitionEngine:
    producer_version = "1"

    def __init__(self, provider: OpenAICompatibleProvider, *,
                 policy_gate: DataPolicyGate | None = None,
                 max_evidence_bytes: int = 10_000_000):
        if max_evidence_bytes < 1:
            raise ValueError("max_evidence_bytes must be positive")
        self.provider = provider
        self.policy_gate = policy_gate
        self.max_evidence_bytes = max_evidence_bytes

    def analyze(self, artifact: EvidenceArtifact, *, asset_id: str | None = None) -> list[CognitionObservation]:
        if artifact.kind not in {"frame", "audio"}:
            raise ValueError("unsupported evidence kind")
        size = artifact.path.stat().st_size
        if size < 1 or size > self.max_evidence_bytes:
            raise ValueError("evidence size is outside the configured limit")
        if provider_is_external(self.provider.settings):
            if self.policy_gate is None:
                raise PermissionError("external AI requires a configured data policy gate")
            if not asset_id:
                raise PermissionError("external AI requires an asset_id for policy authorization")
            self.policy_gate.authorize(self.provider.settings, asset_id, size)
        mime = _MIME_TYPES.get(artifact.path.suffix.lower())
        if mime is None:
            raise ValueError("unsupported evidence media type")
        encoded = b64encode(artifact.path.read_bytes()).decode("ascii")
        if artifact.kind == "frame":
            media = {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}
            task = (
                "Analyze the supplied frame itself. Report concrete visible people, objects, actions, "
                "setting and exact OCR text. Omit categories that are not observable."
            )
            start_us, end_us = artifact.source_start_us, artifact.source_start_us + 1
        else:
            if artifact.source_end_us <= artifact.source_start_us:
                raise ValueError("audio evidence requires a closed source time range")
            audio_format = "wav" if artifact.path.suffix.lower() == ".wav" else artifact.path.suffix[1:].lower()
            media = {"type": "input_audio", "input_audio": {"data": encoded, "format": audio_format}}
            task = (
                "Listen to the supplied audio itself. For speech, transcribe exact audible words in the "
                "original language. For sound and music, report concrete audible events, instruments, "
                "tempo, vocals and mood. Omit categories that are not audible."
            )
            start_us, end_us = artifact.source_start_us, artifact.source_end_us
        response = self.provider.complete(ChatRequest(messages=(
            ChatMessage("system", (
                "You are a media evidence analyzer. Return JSON only as "
                "{\"observations\":[{\"modality\":\"vision|ocr|speech|sound|music\","
                "\"text\":\"factual observation\",\"confidence\":0.0}]}. "
                "Do not identify a person unless the evidence itself proves identity. Never return "
                "schema descriptions, category labels, instructions or placeholder text. If the media "
                "cannot be analyzed, return {\"observations\":[]}."
            )),
            ChatMessage("user", [{"type": "text", "text": task}, media]),
        ), temperature=0.0))
        return self._validated(response.text, start_us, end_us)

    def analyze_and_store(self, understanding: UnderstandingMap, asset_id: str,
                          artifact: EvidenceArtifact) -> list[str]:
        observations = self.analyze(artifact, asset_id=asset_id)
        producer = f"media-cognition:{self.provider.settings.name}:{self.provider.settings.model}"
        return understanding.add_observations(asset_id, [{
            "modality": item.modality,
            "start_us": item.start_us,
            "end_us": item.end_us,
            "text": item.text,
            "confidence": item.confidence,
            "producer": producer,
            "producer_version": self.producer_version,
        } for item in observations])

    @staticmethod
    def _validated(text: str, start_us: int, end_us: int) -> list[CognitionObservation]:
        try:
            document = json.loads(text)
        except json.JSONDecodeError as error:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("media cognition response is not valid JSON") from error
            try:
                document = json.loads(text[start:end + 1])
            except json.JSONDecodeError as nested_error:
                raise ValueError("media cognition response is not valid JSON") from nested_error
        rows = document.get("observations") if isinstance(document, dict) else None
        if not isinstance(rows, list) or not rows:
            raise ValueError("media cognition response has no observations")
        output = []
        for row in rows:
            if not isinstance(row, dict) or row.get("modality") not in _ALLOWED_MODALITIES:
                raise ValueError("media cognition response has an invalid modality")
            value = row.get("confidence")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                raise ValueError("media cognition response has an invalid confidence")
            observation = str(row.get("text", "")).strip()
            if not observation or value == 0:
                continue
            output.append(CognitionObservation(row["modality"], observation, float(value), start_us, end_us))
        if not output:
            raise ValueError("media cognition response has no usable observations")
        return output
