"""Human approval boundary for autonomous studio candidate rendering."""

import json
from pathlib import Path

from .map import UnderstandingMap


def authorize_private_preview(understanding: UnderstandingMap, candidate_path: Path) -> dict:
    document = json.loads(candidate_path.resolve(strict=True).read_text(encoding="utf-8-sig"))
    if document.get("authorship") != "autonomous_studio" or not document.get("studio_run_id"):
        raise PermissionError("private preview requires an autonomous_studio candidate")
    run = understanding.get_studio_run(document["studio_run_id"])
    if run["status"] != "candidate_ready" or run["candidate_plan"] != document:
        raise PermissionError("candidate file does not match the append-only studio ledger")
    if (document.get("brief_compliance") or {}).get("status") != "pass":
        raise PermissionError("private preview requires a candidate-bound passing brief compliance report")
    gates = document.get("gates") or {}
    if gates.get("private_preview_eligible") is True:
        return document
    approval = understanding.current_studio_approval(document["studio_run_id"], "private_preview")
    if approval is None or approval["decision"] != "approve":
        raise PermissionError("private preview blockers require explicit human approval")
    return document

