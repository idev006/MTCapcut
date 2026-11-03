"""Validated, categorized TOML configuration with redacted AI secrets."""

from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from urllib.parse import urlparse


@dataclass(frozen=True)
class RuntimeSettings:
    max_workers: int = 2


@dataclass(frozen=True)
class UIBridgeSettings:
    poll_interval_ms: int = 100


@dataclass(frozen=True)
class StorageSettings:
    journal_mode: str = "delete"


@dataclass(frozen=True)
class SecuritySettings:
    allow_remote_ai: bool = False
    allow_insecure_remote_http: bool = False


@dataclass(frozen=True)
class ObservabilitySettings:
    log_level: str = "INFO"


@dataclass(frozen=True)
class LocalEarSettings:
    enabled: bool = False
    model_size: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str | None = "th"
    vad_filter: bool = True
    min_confidence: float = 0.25
    cache_dir: Path | None = None


@dataclass(frozen=True)
class ShotAnalysisSettings:
    enabled: bool = False
    threshold: float = 27.0
    min_scene_len_frames: int = 15
    frames_per_shot: int = 3
    frame_width: int = 640


@dataclass(frozen=True)
class DataPolicySettings:
    require_asset_approval: bool = True
    allowed_external_classifications: tuple[str, ...] = ("public_source", "internal_test")
    max_evidence_bytes: int = 10_000_000
    evidence_retention_days: int = 7


@dataclass(frozen=True)
class AIProviderSettings:
    name: str
    kind: str
    base_url: str
    model: str
    api_key_env: str | None = None
    api_key: str | None = field(default=None, repr=False, compare=False)
    timeout_seconds: int = 120
    enabled: bool = False
    app_url: str | None = None
    app_name: str | None = None


@dataclass(frozen=True)
class AISettings:
    default_provider: str | None = None
    vision_model: str | None = None
    audio_model: str | None = None
    studio_model: str | None = None
    providers: dict[str, AIProviderSettings] = field(default_factory=dict)


@dataclass(frozen=True)
class Config:
    workspace: Path
    ffprobe: Path
    capcut_apps_root: Path
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
    ui_bridge: UIBridgeSettings = field(default_factory=UIBridgeSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    observability: ObservabilitySettings = field(default_factory=ObservabilitySettings)
    ai: AISettings = field(default_factory=AISettings)
    local_ear: LocalEarSettings = field(default_factory=LocalEarSettings)
    shot_analysis: ShotAnalysisSettings = field(default_factory=ShotAnalysisSettings)
    data_policy: DataPolicySettings = field(default_factory=DataPolicySettings)

    @property
    def ffmpeg(self) -> Path:
        return self.ffprobe.with_name("ffmpeg.exe")


def _integer(section: dict, key: str, default: int, minimum: int, maximum: int) -> int:
    value = section.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")
    return value


def _boolean(section: dict, key: str, default: bool) -> bool:
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _provider(name: str, raw: dict, security: SecuritySettings) -> AIProviderSettings:
    kind = raw.get("kind")
    if kind not in {"openrouter", "local_openai"}:
        raise ValueError(f"AI provider {name}: unsupported kind")
    base_url = str(raw.get("base_url", "")).rstrip("/")
    model = str(raw.get("model", "")).strip()
    if not base_url or not model:
        raise ValueError(f"AI provider {name}: base_url and model are required")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"AI provider {name}: invalid base_url")
    loopback = parsed.hostname.lower() in {"127.0.0.1", "localhost", "::1"}
    if kind == "openrouter" and parsed.scheme != "https":
        raise ValueError("OpenRouter requires HTTPS")
    if kind == "openrouter" and parsed.hostname.lower() != "openrouter.ai":
        raise ValueError("OpenRouter kind requires the official openrouter.ai endpoint")
    if kind == "local_openai" and not loopback and not security.allow_remote_ai:
        raise ValueError(f"AI provider {name}: remote AI endpoint is disabled")
    if parsed.scheme == "http" and not loopback and not security.allow_insecure_remote_http:
        raise ValueError(f"AI provider {name}: insecure remote HTTP is disabled")
    api_key_env = raw.get("api_key_env")
    if api_key_env is not None and not isinstance(api_key_env, str):
        raise ValueError(f"AI provider {name}: api_key_env must be a string")
    api_key_env = api_key_env.strip() if api_key_env else None
    api_key = raw.get("api_key")
    if api_key is not None and not isinstance(api_key, str):
        raise ValueError(f"AI provider {name}: api_key must be a string")
    api_key = api_key.strip() if api_key else None
    if kind == "openrouter" and not api_key_env and not api_key:
        raise ValueError(f"AI provider {name}: api_key or api_key_env is required")
    return AIProviderSettings(
        name=name, kind=kind, base_url=base_url, model=model,
        api_key_env=api_key_env, api_key=api_key,
        timeout_seconds=_integer(raw, "timeout_seconds", 120, 1, 3600),
        enabled=_boolean(raw, "enabled", False),
        app_url=str(raw["app_url"]) if raw.get("app_url") else None,
        app_name=str(raw["app_name"]) if raw.get("app_name") else None,
    )


def load_config(path: Path, *, validate_paths: bool = True) -> Config:
    with path.open("rb") as stream:
        raw = tomllib.load(stream)
    if raw.get("schema_version") not in {1, 2}:
        raise ValueError("Unsupported config schema_version")
    config_root = path.resolve().parent

    def configured_path(value: str) -> Path:
        candidate = Path(value)
        return (candidate if candidate.is_absolute() else config_root / candidate).resolve()

    workspace = configured_path(raw["paths"]["workspace"])
    ffprobe = configured_path(raw["ffmpeg"]["ffprobe"])
    apps_root = configured_path(raw["capcut"]["apps_root"])
    if validate_paths and not ffprobe.is_file():
        raise FileNotFoundError(f"ffprobe executable not found: {ffprobe}")

    runtime_raw = raw.get("runtime", {})
    runtime = RuntimeSettings(_integer(runtime_raw, "max_workers", 2, 1, 32))
    ui_bridge = UIBridgeSettings(
        _integer(raw.get("ui_bridge", {}), "poll_interval_ms", 100, 10, 5000)
    )
    storage = StorageSettings(str(raw.get("storage", {}).get("journal_mode", "delete")).lower())
    if storage.journal_mode not in {"delete", "truncate", "persist"}:
        raise ValueError("storage.journal_mode must remain a rollback-journal mode")
    security_raw = raw.get("security", {})
    security = SecuritySettings(
        _boolean(security_raw, "allow_remote_ai", False),
        _boolean(security_raw, "allow_insecure_remote_http", False),
    )
    log_level = str(raw.get("observability", {}).get("log_level", "INFO")).upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("observability.log_level is invalid")
    observability = ObservabilitySettings(log_level)

    local_ear_raw = raw.get("local_ear", {})
    local_ear_device = str(local_ear_raw.get("device", "cpu")).lower()
    if local_ear_device not in {"cpu", "cuda", "auto"}:
        raise ValueError("local_ear.device must be cpu, cuda or auto")
    local_ear_language = local_ear_raw.get("language", "th")
    if local_ear_language is not None and not isinstance(local_ear_language, str):
        raise ValueError("local_ear.language must be a string or omitted")
    cache_value = local_ear_raw.get("cache_dir")
    min_confidence = local_ear_raw.get("min_confidence", 0.25)
    if (not isinstance(min_confidence, (int, float)) or isinstance(min_confidence, bool)
            or not 0 <= min_confidence <= 1):
        raise ValueError("local_ear.min_confidence must be from 0 to 1")
    local_ear = LocalEarSettings(
        enabled=_boolean(local_ear_raw, "enabled", False),
        model_size=str(local_ear_raw.get("model_size", "small")).strip(),
        device=local_ear_device,
        compute_type=str(local_ear_raw.get("compute_type", "int8")).strip(),
        language=local_ear_language.strip() if local_ear_language else None,
        vad_filter=_boolean(local_ear_raw, "vad_filter", True),
        min_confidence=float(min_confidence),
        cache_dir=configured_path(cache_value) if cache_value else None,
    )
    if not local_ear.model_size or not local_ear.compute_type:
        raise ValueError("local_ear model_size and compute_type are required")

    shot_raw = raw.get("shot_analysis", {})
    threshold = shot_raw.get("threshold", 27.0)
    if (not isinstance(threshold, (int, float)) or isinstance(threshold, bool)
            or not 0 < threshold <= 255):
        raise ValueError("shot_analysis.threshold must be greater than 0 and at most 255")
    shot_analysis = ShotAnalysisSettings(
        enabled=_boolean(shot_raw, "enabled", False),
        threshold=float(threshold),
        min_scene_len_frames=_integer(shot_raw, "min_scene_len_frames", 15, 1, 10000),
        frames_per_shot=_integer(shot_raw, "frames_per_shot", 3, 1, 10),
        frame_width=_integer(shot_raw, "frame_width", 640, 64, 4096),
    )

    data_policy_raw = raw.get("data_policy", {})
    allowed_classifications = data_policy_raw.get(
        "allowed_external_classifications", ["public_source", "internal_test"]
    )
    if (not isinstance(allowed_classifications, list) or not allowed_classifications
            or any(not isinstance(item, str) or not item.strip() for item in allowed_classifications)):
        raise ValueError("data_policy.allowed_external_classifications must be a nonempty string array")
    allowed_tuple = tuple(dict.fromkeys(item.strip() for item in allowed_classifications))
    known_classifications = {"public_source", "internal_test", "confidential", "restricted"}
    if not set(allowed_tuple) <= known_classifications:
        raise ValueError("data_policy contains an unknown classification")
    data_policy = DataPolicySettings(
        require_asset_approval=_boolean(data_policy_raw, "require_asset_approval", True),
        allowed_external_classifications=allowed_tuple,
        max_evidence_bytes=_integer(data_policy_raw, "max_evidence_bytes", 10_000_000, 1, 100_000_000),
        evidence_retention_days=_integer(data_policy_raw, "evidence_retention_days", 7, 1, 3650),
    )

    ai_raw = raw.get("ai", {})
    providers = {name: _provider(name, value, security)
                 for name, value in ai_raw.get("providers", {}).items()}
    default_provider = ai_raw.get("default_provider") or None
    if default_provider is not None:
        if default_provider not in providers:
            raise ValueError("ai.default_provider does not exist")
        if not providers[default_provider].enabled:
            raise ValueError("ai.default_provider must be enabled")
    vision_model = str(ai_raw.get("vision_model", "")).strip() or None
    audio_model = str(ai_raw.get("audio_model", "")).strip() or None
    studio_model = str(ai_raw.get("studio_model", "")).strip() or None
    return Config(workspace, ffprobe, apps_root, runtime, ui_bridge, storage, security,
                  observability, AISettings(default_provider, vision_model, audio_model, studio_model, providers),
                  local_ear, shot_analysis, data_policy)
