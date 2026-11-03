"""Application service for reviewable, localized editorial change requests."""

from dataclasses import dataclass
from hashlib import sha256
import json

from .editorial import EditScope, Receipt, select_edit_scope
from .editorial_store import EditorialStore


@dataclass(frozen=True)
class ChangePlan:
    request_id: str
    revision_id: str
    scope: EditScope
    scope_hash: str


class LocalizedChangeService:
    def __init__(self, store: EditorialStore):
        self.store = store

    def plan_change(
        self,
        revision_id: str,
        request_id: str,
        start_us: int,
        end_us: int,
        context_us: int,
        actor: str,
        reason: str,
        config_hash: str,
        created_at: str = "",
    ) -> ChangePlan:
        if not request_id or not actor.strip() or not reason.strip() or not config_hash:
            raise ValueError("request_id, actor, reason and config_hash are required")
        revision = self.store.load_revision(revision_id)
        scope = select_edit_scope(revision, start_us, end_us, context_us=context_us)
        if not scope.editable_segment_ids:
            raise ValueError("requested range does not overlap an editable segment")
        details = (
            ("actor", actor),
            ("reason", reason),
            ("requested_range_us", f"{start_us}:{end_us}"),
            ("context_range_us", f"{scope.context_start_us}:{scope.context_end_us}"),
            ("editable_segment_ids", ",".join(scope.editable_segment_ids)),
            ("context_segment_ids", ",".join(scope.context_segment_ids)),
            ("affected_element_ids", ",".join(scope.affected_element_ids)),
        )
        scope_payload = json.dumps(details, ensure_ascii=False, separators=(",", ":"))
        scope_hash = sha256(scope_payload.encode("utf-8")).hexdigest()
        subjects = (revision_id,) + scope.editable_segment_ids + scope.affected_element_ids
        receipt = Receipt(
            receipt_id=request_id,
            kind="localized_change_request",
            revision_id=revision_id,
            subject_ids=subjects,
            producer="localized-change-service",
            producer_version="1",
            input_hashes=(self.store.revision_hash(revision_id),),
            output_hashes=(scope_hash,),
            config_hash=config_hash,
            details=details,
            created_at=created_at,
        )
        self.store.append_receipt(receipt)
        return ChangePlan(request_id, revision_id, scope, scope_hash)
