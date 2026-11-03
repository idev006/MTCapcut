"""Asset intake: source identity, role and technical metadata."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import subprocess
from uuid import uuid4

from .config import Config


MEDIA_SUFFIXES = {
    "clip": {".mp4", ".mov", ".mkv", ".avi", ".webm"},
    "audio": {".mp3", ".wav", ".m4a", ".flac", ".aac"},
    "picture": {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"},
    "text": {".txt", ".md", ".srt", ".vtt"},
}
TEXT_ROLES = {"brief", "confirmed_facts", "script", "caption", "on_screen_copy", "reference", "restrictions"}
AUDIO_ROLES = {"narration", "dialogue", "music", "ambience", "sfx", "reference"}


@dataclass(frozen=True)
class InputAsset:
    path: Path
    role: str
    source: str = "user"
    rights_status: str = "unknown"


def file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    for kind, suffixes in MEDIA_SUFFIXES.items():
        if suffix in suffixes:
            return kind
    raise ValueError(f"Unsupported asset extension: {suffix}")


def inspect_asset(item: InputAsset, config: Config) -> dict:
    path = item.path.resolve(strict=True)
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    kind = detect_kind(path)
    if kind == "text" and item.role not in TEXT_ROLES:
        raise ValueError(f"Text role must be one of {sorted(TEXT_ROLES)}")
    if kind == "audio" and item.role not in AUDIO_ROLES:
        raise ValueError(f"Audio role must be one of {sorted(AUDIO_ROLES)}")
    technical = {}
    if kind != "text":
        command = [str(config.ffprobe), "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60, check=False,
        )
        if result.returncode:
            raise ValueError(f"ffprobe rejected {path.name}: {result.stderr.strip()[:300]}")
        technical = json.loads(result.stdout)
        if not technical.get("streams"):
            raise ValueError(f"No media streams: {path.name}")
    else:
        path.read_text(encoding="utf-8-sig")
    return {
        "asset_id": str(uuid4()),
        "path": str(path),
        "kind": kind,
        "role": item.role,
        "source": item.source,
        "rights_status": item.rights_status,
        "content_hash": file_hash(path),
        "size_bytes": path.stat().st_size,
        "technical": technical,
    }


def inspect_bundle(items: list[InputAsset], config: Config) -> list[dict]:
    """Inspect all inputs before callers commit any of them to a project map."""
    if not items:
        raise ValueError("Asset bundle is empty")
    inspected = [inspect_asset(item, config) for item in items]
    identities = [(asset["path"], asset["role"]) for asset in inspected]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate path and role in asset bundle")
    return inspected
