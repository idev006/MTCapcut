"""Local media perception artifacts with source timestamps.

Frames and audio are evidence for later AI engines; this module makes no semantic claims.
"""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class EvidenceArtifact:
    kind: str
    source_start_us: int
    source_end_us: int
    path: Path
    content_hash: str


def hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[-1000:])


def extract_frame(
    ffmpeg: Path, source: Path, destination: Path, at_us: int, *, width: int = 640
) -> EvidenceArtifact:
    if at_us < 0 or width < 1:
        raise ValueError("Invalid frame position or width")
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-ss", f"{at_us / 1_000_000:.6f}",
          "-i", str(source), "-map", "0:v:0", "-frames:v", "1", "-vf", f"scale={width}:-2",
          "-f", "image2", str(destination)])
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError("No frame decoded at the requested timestamp")
    return EvidenceArtifact("frame", at_us, at_us, destination, hash_file(destination))


def extract_audio(
    ffmpeg: Path, source: Path, destination: Path, *, start_us: int = 0,
    end_us: int | None = None, sample_rate: int = 16000
) -> EvidenceArtifact:
    if start_us < 0 or (end_us is not None and end_us <= start_us) or sample_rate < 1:
        raise ValueError("Invalid audio range or sample rate")
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [str(ffmpeg), "-hide_banner", "-loglevel", "error", "-ss", f"{start_us / 1_000_000:.6f}",
               "-i", str(source), "-map", "0:a:0", "-vn", "-ar", str(sample_rate), "-ac", "1"]
    if end_us is not None:
        command.extend(["-t", f"{(end_us - start_us) / 1_000_000:.6f}"])
    command.extend(["-c:a", "pcm_s16le", str(destination)])
    _run(command)
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError("No audio decoded from the requested range")
    return EvidenceArtifact("audio", start_us, end_us or -1, destination, hash_file(destination))
