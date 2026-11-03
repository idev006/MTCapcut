"""Fail-closed authorization gate for sending evidence to AI providers."""

from dataclasses import dataclass
from urllib.parse import urlparse

from .config import AIProviderSettings, Config
from .map import UnderstandingMap


@dataclass(frozen=True)
class DataPolicyDecision:
    asset_id: str
    external: bool
    classification: str | None
    policy_id: str | None
    evidence_bytes: int


def provider_is_external(settings: AIProviderSettings) -> bool:
    hostname = (urlparse(settings.base_url).hostname or "").lower()
    return hostname not in {"127.0.0.1", "localhost", "::1"}


class DataPolicyGate:
    def __init__(self, config: Config, understanding: UnderstandingMap):
        self.config = config
        self.understanding = understanding

    def authorize(self, settings: AIProviderSettings, asset_id: str, evidence_bytes: int) -> DataPolicyDecision:
        if evidence_bytes < 1:
            raise ValueError("evidence payload must be nonempty")
        external = provider_is_external(settings)
        if not external:
            return DataPolicyDecision(asset_id, False, None, None, evidence_bytes)
        if not self.config.security.allow_remote_ai:
            raise PermissionError("remote AI is disabled by central security config")
        if evidence_bytes > self.config.data_policy.max_evidence_bytes:
            raise PermissionError("evidence payload exceeds the external AI size limit")
        policy = self.understanding.current_asset_ai_policy(asset_id)
        if policy is None:
            if self.config.data_policy.require_asset_approval:
                raise PermissionError("asset has no external AI approval policy")
            raise PermissionError("external AI requires an explicit asset classification")
        if not policy["external_ai_allowed"]:
            raise PermissionError("asset policy blocks external AI")
        if policy["classification"] not in self.config.data_policy.allowed_external_classifications:
            raise PermissionError("asset classification is not allowed for external AI")
        return DataPolicyDecision(asset_id, True, policy["classification"], policy["policy_id"], evidence_bytes)
