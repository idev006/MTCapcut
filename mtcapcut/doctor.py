"""Read-only environment diagnostics for MTCapcut."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import platform
import subprocess
import sys

from .config import Config


def _binary_version(executable: Path) -> dict[str, object]:
    if not executable.is_file():
        return {"ok": False, "path": str(executable), "error": "not found"}
    try:
        completed = subprocess.run(
            [str(executable), "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return {"ok": False, "path": str(executable), "error": str(error)}
    first_line = (completed.stdout or completed.stderr).splitlines()[0]
    return {"ok": True, "path": str(executable), "version": first_line}


def _capcut_versions(apps_root: Path) -> list[dict[str, str]]:
    if not apps_root.is_dir():
        return []
    installations = []
    for executable in apps_root.glob("*/CapCut.exe"):
        installations.append({"version": executable.parent.name, "path": str(executable.resolve())})
    return sorted(installations, key=lambda row: row["version"])


def diagnose(config: Config) -> dict[str, object]:
    """Return deterministic, read-only environment evidence."""
    try:
        pycapcut_version = version("pycapcut")
    except PackageNotFoundError:
        pycapcut_version = None
    checks = {
        "python": {
            "ok": sys.version_info >= (3, 11),
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "ffmpeg": _binary_version(config.ffmpeg),
        "ffprobe": _binary_version(config.ffprobe),
        "pycapcut": {
            "ok": pycapcut_version == "0.0.4",
            "version": pycapcut_version,
            "required": "0.0.4",
        },
        "capcut": {
            "ok": bool(installations := _capcut_versions(config.capcut_apps_root)),
            "apps_root": str(config.capcut_apps_root),
            "installations": installations,
        },
        "workspace": {
            "ok": config.workspace.parent.is_dir(),
            "path": str(config.workspace),
            "exists": config.workspace.is_dir(),
        },
    }
    return {"ok": all(bool(item["ok"]) for item in checks.values()), "checks": checks}
