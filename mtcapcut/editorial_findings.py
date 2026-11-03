"""Typed editorial findings and deterministic release-scope gates."""

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class FindingCategory(StrEnum):
    FACT = "fact"
    ETHICS = "ethics"
    RIGHTS = "rights"
    PRIVACY = "privacy"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ACCESSIBILITY = "accessibility"
    BRAND = "brand"
    EVIDENCE_GAP = "evidence_gap"
    BRIEF_COMPLIANCE = "brief_compliance"


class FindingSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOTE = "note"


class ReleaseScope(StrEnum):
    PRIVATE_PREVIEW = "private_preview"
    PUBLICATION = "publication"


@dataclass(frozen=True)
class EditorialFinding:
    finding_id: str
    source_role: str
    category: FindingCategory
    severity: FindingSeverity
    finding: str
    evidence: tuple[str, ...]
    required_action: str
    owner_role: str
    blocks_scopes: tuple[ReleaseScope, ...] = ()

    def __post_init__(self) -> None:
        if not all((self.finding_id.strip(), self.source_role.strip(), self.finding.strip())):
            raise ValueError("editorial finding identity and text are required")
        if self.severity in {FindingSeverity.CRITICAL, FindingSeverity.HIGH}:
            if not self.evidence or not self.required_action.strip():
                raise ValueError("high and critical findings require evidence and an action")
        if len(set(self.blocks_scopes)) != len(self.blocks_scopes):
            raise ValueError("finding block scopes must be unique")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReleaseGates:
    private_preview_eligible: bool
    publication_eligible: bool
    private_blocking_finding_ids: tuple[str, ...]
    publication_blocking_finding_ids: tuple[str, ...]
    warning_finding_ids: tuple[str, ...]
    rights_blocker_asset_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_release_gates(findings: tuple[EditorialFinding, ...],
                          rights_blockers: tuple[str, ...],
                          delivery_scope: str) -> ReleaseGates:
    private = tuple(item.finding_id for item in findings
                    if ReleaseScope.PRIVATE_PREVIEW in item.blocks_scopes)
    publication = tuple(item.finding_id for item in findings
                        if ReleaseScope.PUBLICATION in item.blocks_scopes)
    warning = tuple(item.finding_id for item in findings if not item.blocks_scopes)
    publication_allowed = delivery_scope == ReleaseScope.PUBLICATION
    return ReleaseGates(
        not private,
        publication_allowed and not private and not publication and not rights_blockers,
        private,
        tuple(dict.fromkeys((*private, *publication))),
        warning,
        tuple(rights_blockers),
    )
