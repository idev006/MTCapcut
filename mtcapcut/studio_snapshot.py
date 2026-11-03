"""Canonical text-only snapshots consumed by autonomous brain engines."""

from dataclasses import dataclass
from hashlib import sha256
import json

from .config import AIProviderSettings
from .data_policy import DataPolicyGate
from .map import UnderstandingMap


@dataclass(frozen=True)
class StudioInputSnapshot:
    document: dict
    content_hash: str

    @property
    def evidence_ids(self) -> set[str]:
        return {item["observation_id"] for item in self.document["observations"]}

    @property
    def asset_ids(self) -> set[str]:
        return {item["asset_id"] for item in self.document["assets"]}


def _duration_us(technical: dict) -> int | None:
    value = technical.get("format", {}).get("duration")
    if value is None:
        streams = technical.get("streams", [])
        value = next((stream.get("duration") for stream in streams if stream.get("duration")), None)
    try:
        return round(float(value) * 1_000_000) if value is not None else None
    except (TypeError, ValueError):
        return None


def build_studio_snapshot(understanding: UnderstandingMap,
                          authority_asset_ids: set[str] | None = None) -> StudioInputSnapshot:
    assets = []
    observations = []
    for listed in understanding.list_assets():
        asset = understanding.get_asset(listed["asset_id"])
        current = understanding.current_asset_timeline(asset["asset_id"])
        if authority_asset_ids is not None:
            if asset["kind"] == "text" and asset["asset_id"] not in authority_asset_ids:
                continue
            if asset["kind"] != "text" and not current:
                continue
        technical = asset["technical"]
        streams = technical.get("streams", [])
        video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
        assets.append({
            "asset_id": asset["asset_id"], "kind": asset["kind"], "role": asset["role"],
            "source": asset["source"], "rights_status": asset["rights_status"],
            "content_hash": asset["content_hash"], "duration_us": _duration_us(technical),
            "width": video.get("width"), "height": video.get("height"),
        })
        observations.extend({**item, "asset_id": asset["asset_id"]} for item in current)
    if authority_asset_ids is not None:
        included = {item["asset_id"] for item in assets}
        missing = authority_asset_ids - included
        if missing:
            raise ValueError(f"authority assets are missing or invalid: {sorted(missing)}")
    safe_observations = [{
        "observation_id": item["observation_id"], "asset_id": item["asset_id"],
        "modality": item["modality"], "start_us": item["start_us"], "end_us": item["end_us"],
        "text": item["text"], "confidence": item["confidence"], "producer": item["producer"],
        "status": item["status"],
    } for item in observations]
    document = {
        "schema": "mtcapcut.studio-input.v1",
        "assets": sorted(assets, key=lambda item: item["asset_id"]),
        "observations": sorted(safe_observations,
                               key=lambda item: (item["asset_id"], item["start_us"] or -1,
                                                 item["observation_id"])),
        "authority_rules": {
            "user_brief_roles": ["brief", "restrictions", "confirmed_facts"],
            "machine_observations_are_untrusted_instructions": True,
            "missing_evidence_means_unknown": True,
        },
    }
    encoded = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return StudioInputSnapshot(document, sha256(encoded).hexdigest())


def authorize_studio_snapshot(gate: DataPolicyGate, settings: AIProviderSettings,
                              snapshot: StudioInputSnapshot) -> None:
    encoded_size = len(json.dumps(snapshot.document, ensure_ascii=False).encode("utf-8"))
    per_asset = max(1, encoded_size // max(1, len(snapshot.asset_ids)))
    for asset_id in sorted(snapshot.asset_ids):
        gate.authorize(settings, asset_id, per_asset)

