"""Transactional project understanding map with immutable observations."""

from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from uuid import uuid4


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS assets (
  asset_id TEXT PRIMARY KEY, path TEXT NOT NULL, kind TEXT NOT NULL,
  role TEXT NOT NULL, source TEXT NOT NULL, rights_status TEXT NOT NULL,
  content_hash TEXT NOT NULL, size_bytes INTEGER NOT NULL,
  technical_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
  observation_id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES assets(asset_id),
  modality TEXT NOT NULL, start_us INTEGER, end_us INTEGER,
  text TEXT NOT NULL, confidence REAL, producer TEXT NOT NULL,
  producer_version TEXT NOT NULL, status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (start_us IS NULL OR start_us >= 0),
  CHECK (end_us IS NULL OR (start_us IS NOT NULL AND end_us > start_us)),
  CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1)
);
CREATE TABLE IF NOT EXISTS claims (
  claim_id TEXT PRIMARY KEY, statement TEXT NOT NULL, status TEXT NOT NULL,
  rationale TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claim_evidence (
  claim_id TEXT NOT NULL REFERENCES claims(claim_id),
  observation_id TEXT NOT NULL REFERENCES observations(observation_id),
  relation TEXT NOT NULL CHECK (relation IN ('supports','conflicts')),
  PRIMARY KEY (claim_id, observation_id, relation)
);
CREATE TABLE IF NOT EXISTS reviews (
  review_id TEXT PRIMARY KEY, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
  actor TEXT NOT NULL, decision TEXT NOT NULL, reason TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS asset_versions (
  version_id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES assets(asset_id),
  content_hash TEXT NOT NULL, path TEXT NOT NULL, size_bytes INTEGER NOT NULL,
  technical_json TEXT NOT NULL, created_at TEXT NOT NULL,
  UNIQUE(asset_id, content_hash)
);
CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id TEXT PRIMARY KEY, asset_version_id TEXT NOT NULL REFERENCES asset_versions(version_id),
  kind TEXT NOT NULL, path TEXT NOT NULL, content_hash TEXT NOT NULL,
  producer TEXT NOT NULL, producer_version TEXT NOT NULL, config_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS asset_versions_latest ON asset_versions(asset_id, created_at);
CREATE INDEX IF NOT EXISTS observations_asset_time ON observations(asset_id, start_us);
CREATE TABLE IF NOT EXISTS asset_ai_policies (
  policy_id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL REFERENCES assets(asset_id),
  classification TEXT NOT NULL CHECK (classification IN ('public_source','internal_test','confidential','restricted')),
  external_ai_allowed INTEGER NOT NULL CHECK (external_ai_allowed IN (0,1)),
  actor TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS asset_ai_policies_latest ON asset_ai_policies(asset_id, created_at);
CREATE TABLE IF NOT EXISTS studio_runs (
  run_id TEXT PRIMARY KEY, status TEXT NOT NULL,
  authorship TEXT NOT NULL CHECK (authorship IN ('autonomous_studio','developer_fixture')),
  input_hash TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL,
  prompt_version TEXT NOT NULL, input_json TEXT NOT NULL,
  synthesis_json TEXT, candidate_plan_json TEXT, error TEXT,
  created_at TEXT NOT NULL, completed_at TEXT
);
CREATE TABLE IF NOT EXISTS studio_recommendations (
  recommendation_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES studio_runs(run_id),
  role TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS studio_recommendations_run ON studio_recommendations(run_id, created_at);
CREATE TABLE IF NOT EXISTS studio_brief_interpretations (
  interpretation_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES studio_runs(run_id),
  payload_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS studio_brief_interpretations_run ON studio_brief_interpretations(run_id, created_at);
CREATE TABLE IF NOT EXISTS studio_approvals (
  approval_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES studio_runs(run_id),
  scope TEXT NOT NULL CHECK (scope IN ('private_preview','publication')),
  decision TEXT NOT NULL CHECK (decision IN ('approve','reject')),
  actor TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS studio_approvals_latest ON studio_approvals(run_id, scope, created_at);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UnderstandingMap:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        fields = {row[1] for row in self.connection.execute("PRAGMA table_info(observations)")}
        if "asset_version_id" not in fields:
            self.connection.execute("ALTER TABLE observations ADD COLUMN asset_version_id TEXT REFERENCES asset_versions(version_id)")
        # Existing maps predate version tracking. Preserve their identity and history.
        with self.connection:
            for asset_id, path, digest, size, technical, created in self.connection.execute(
                "SELECT asset_id,path,content_hash,size_bytes,technical_json,created_at FROM assets"
            ).fetchall():
                if not self.connection.execute("SELECT 1 FROM asset_versions WHERE asset_id=?", (asset_id,)).fetchone():
                    version_id = str(uuid4())
                    self.connection.execute("INSERT INTO asset_versions VALUES (?,?,?,?,?,?,?)",
                                            (version_id, asset_id, digest, path, size, technical, created))
                    self.connection.execute("UPDATE observations SET asset_version_id=? WHERE asset_id=? AND asset_version_id IS NULL",
                                            (version_id, asset_id))

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def add_asset(self, asset: dict) -> str:
        with self.connection:
            self.connection.execute(
                "INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?)",
                (asset["asset_id"], asset["path"], asset["kind"], asset["role"],
                 asset["source"], asset["rights_status"], asset["content_hash"],
                 asset["size_bytes"], json.dumps(asset["technical"], ensure_ascii=False), now()),
            )
            self.connection.execute("INSERT INTO asset_versions VALUES (?,?,?,?,?,?,?)",
                                    (str(uuid4()), asset["asset_id"], asset["content_hash"], asset["path"],
                                     asset["size_bytes"], json.dumps(asset["technical"], ensure_ascii=False), now()))
        return asset["asset_id"]

    def register_bundle(self, assets: list[dict]) -> list[dict]:
        """Commit pre-inspected assets together; same path/role retains logical identity."""
        results = []
        with self.connection:
            for asset in assets:
                row = self.connection.execute(
                    "SELECT asset_id,content_hash FROM assets WHERE path=? AND role=? ORDER BY created_at DESC LIMIT 1",
                    (asset["path"], asset["role"]),
                ).fetchone()
                asset_id = row[0] if row else asset["asset_id"]
                changed = row is None or row[1] != asset["content_hash"]
                if row is None:
                    self.connection.execute("INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (asset_id, asset["path"], asset["kind"], asset["role"], asset["source"],
                         asset["rights_status"], asset["content_hash"], asset["size_bytes"],
                         json.dumps(asset["technical"], ensure_ascii=False), now()))
                elif changed:
                    self.connection.execute(
                        "UPDATE assets SET kind=?,source=?,rights_status=?,content_hash=?,size_bytes=?,technical_json=? WHERE asset_id=?",
                        (asset["kind"], asset["source"], asset["rights_status"], asset["content_hash"],
                         asset["size_bytes"], json.dumps(asset["technical"], ensure_ascii=False), asset_id),
                    )
                version = self.connection.execute(
                    "SELECT version_id FROM asset_versions WHERE asset_id=? AND content_hash=?",
                    (asset_id, asset["content_hash"]),
                ).fetchone()
                if version is None:
                    version_id = str(uuid4())
                    self.connection.execute("INSERT INTO asset_versions VALUES (?,?,?,?,?,?,?)",
                        (version_id, asset_id, asset["content_hash"], asset["path"], asset["size_bytes"],
                         json.dumps(asset["technical"], ensure_ascii=False), now()))
                else:
                    version_id = version[0]
                results.append({"asset_id": asset_id, "asset_version_id": version_id,
                                "changed": changed, "content_hash": asset["content_hash"]})
        return results

    def current_version(self, asset_id: str) -> str:
        row = self.connection.execute(
            "SELECT v.version_id FROM asset_versions v JOIN assets a ON a.asset_id=v.asset_id "
            "WHERE a.asset_id=? AND v.content_hash=a.content_hash ORDER BY v.created_at DESC LIMIT 1", (asset_id,)
        ).fetchone()
        if row is None:
            raise KeyError(asset_id)
        return row[0]

    def list_assets(self) -> list[dict]:
        rows = self.connection.execute(
            "SELECT asset_id,path,kind,role,rights_status,content_hash FROM assets ORDER BY created_at,asset_id"
        ).fetchall()
        return [dict(zip(("asset_id", "path", "kind", "role", "rights_status", "content_hash"), row)) for row in rows]

    def get_asset(self, asset_id: str) -> dict:
        row = self.connection.execute(
            "SELECT asset_id,path,kind,role,source,rights_status,content_hash,size_bytes,technical_json "
            "FROM assets WHERE asset_id=?", (asset_id,)
        ).fetchone()
        if row is None:
            raise KeyError(asset_id)
        keys = ("asset_id", "path", "kind", "role", "source", "rights_status",
                "content_hash", "size_bytes", "technical")
        result = dict(zip(keys, row))
        result["technical"] = json.loads(result["technical"])
        return result

    def set_asset_ai_policy(self, asset_id: str, classification: str, external_ai_allowed: bool,
                            actor: str, reason: str) -> str:
        if classification not in {"public_source", "internal_test", "confidential", "restricted"}:
            raise ValueError("invalid asset data classification")
        if not actor.strip() or not reason.strip():
            raise ValueError("asset AI policy requires actor and reason")
        if not self.connection.execute("SELECT 1 FROM assets WHERE asset_id=?", (asset_id,)).fetchone():
            raise KeyError(asset_id)
        policy_id = str(uuid4())
        with self.connection:
            self.connection.execute("INSERT INTO asset_ai_policies VALUES (?,?,?,?,?,?,?)",
                (policy_id, asset_id, classification, int(external_ai_allowed),
                 actor.strip(), reason.strip(), now()))
        return policy_id

    def current_asset_ai_policy(self, asset_id: str) -> dict | None:
        row = self.connection.execute(
            "SELECT policy_id,classification,external_ai_allowed,actor,reason,created_at "
            "FROM asset_ai_policies WHERE asset_id=? ORDER BY created_at DESC,rowid DESC LIMIT 1",
            (asset_id,),
        ).fetchone()
        if row is None:
            return None
        keys = ("policy_id", "classification", "external_ai_allowed", "actor", "reason", "created_at")
        result = dict(zip(keys, row))
        result["external_ai_allowed"] = bool(result["external_ai_allowed"])
        return result

    def find_asset_by_hash(self, content_hash: str, role: str) -> str | None:
        row = self.connection.execute(
            "SELECT asset_id FROM assets WHERE content_hash=? AND role=? ORDER BY created_at DESC LIMIT 1",
            (content_hash, role),
        ).fetchone()
        return row[0] if row else None

    def start_studio_run(self, input_hash: str, provider: str, model: str,
                         prompt_version: str, input_document: dict,
                         *, authorship: str = "autonomous_studio") -> str:
        if authorship not in {"autonomous_studio", "developer_fixture"}:
            raise ValueError("invalid studio authorship")
        if not all(item.strip() for item in (input_hash, provider, model, prompt_version)):
            raise ValueError("studio run metadata is incomplete")
        run_id = str(uuid4())
        with self.connection:
            self.connection.execute(
                "INSERT INTO studio_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, "running", authorship, input_hash, provider, model, prompt_version,
                 json.dumps(input_document, ensure_ascii=False, sort_keys=True),
                 None, None, None, now(), None),
            )
        return run_id

    def append_studio_recommendation(self, run_id: str, recommendation: dict) -> str:
        recommendation_id = str(recommendation.get("recommendation_id", "")).strip()
        role = str(recommendation.get("role", "")).strip()
        if not recommendation_id or not role:
            raise ValueError("recommendation ID and role are required")
        row = self.connection.execute("SELECT status FROM studio_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or row[0] != "running":
            raise ValueError("studio run is not writable")
        with self.connection:
            self.connection.execute("INSERT INTO studio_recommendations VALUES (?,?,?,?,?)",
                (recommendation_id, run_id, role,
                 json.dumps(recommendation, ensure_ascii=False, sort_keys=True), now()))
        return recommendation_id

    def append_studio_brief(self, run_id: str, brief: dict) -> str:
        row = self.connection.execute("SELECT status FROM studio_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or row[0] != "running":
            raise ValueError("studio run is not writable")
        interpretation_id = str(uuid4())
        with self.connection:
            self.connection.execute("INSERT INTO studio_brief_interpretations VALUES (?,?,?,?)",
                (interpretation_id, run_id, json.dumps(brief, ensure_ascii=False, sort_keys=True), now()))
        return interpretation_id

    def complete_studio_run(self, run_id: str, synthesis: dict, candidate_plan: dict) -> None:
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE studio_runs SET status='candidate_ready',synthesis_json=?,candidate_plan_json=?,completed_at=? "
                "WHERE run_id=? AND status='running'",
                (json.dumps(synthesis, ensure_ascii=False, sort_keys=True),
                 json.dumps(candidate_plan, ensure_ascii=False, sort_keys=True), now(), run_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("studio run cannot be completed")

    def fail_studio_run(self, run_id: str, error: str) -> None:
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE studio_runs SET status='failed',error=?,completed_at=? WHERE run_id=? AND status='running'",
                (error[:2000], now(), run_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("studio run cannot be failed")

    def reject_studio_run(self, run_id: str, synthesis: dict, candidate_plan: dict, error: str) -> None:
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE studio_runs SET status='candidate_rejected',synthesis_json=?,candidate_plan_json=?,"
                "error=?,completed_at=? WHERE run_id=? AND status='running'",
                (json.dumps(synthesis, ensure_ascii=False, sort_keys=True),
                 json.dumps(candidate_plan, ensure_ascii=False, sort_keys=True), error[:2000], now(), run_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("studio run cannot be rejected")

    def get_studio_run(self, run_id: str) -> dict:
        row = self.connection.execute(
            "SELECT run_id,status,authorship,input_hash,provider,model,prompt_version,input_json,"
            "synthesis_json,candidate_plan_json,error,created_at,completed_at FROM studio_runs WHERE run_id=?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise KeyError(run_id)
        keys = ("run_id", "status", "authorship", "input_hash", "provider", "model", "prompt_version",
                "input", "synthesis", "candidate_plan", "error", "created_at", "completed_at")
        result = dict(zip(keys, row))
        for key in ("input", "synthesis", "candidate_plan"):
            result[key] = json.loads(result[key]) if result[key] else None
        recommendations = self.connection.execute(
            "SELECT payload_json FROM studio_recommendations WHERE run_id=? ORDER BY created_at,rowid", (run_id,)
        ).fetchall()
        result["recommendations"] = [json.loads(item[0]) for item in recommendations]
        briefs = self.connection.execute(
            "SELECT payload_json FROM studio_brief_interpretations WHERE run_id=? ORDER BY created_at,rowid",
            (run_id,),
        ).fetchall()
        result["brief_interpretations"] = [json.loads(item[0]) for item in briefs]
        return result

    def review_studio_run(self, run_id: str, scope: str, decision: str,
                          actor: str, reason: str) -> str:
        if scope not in {"private_preview", "publication"} or decision not in {"approve", "reject"}:
            raise ValueError("invalid studio approval scope or decision")
        if not actor.strip() or not reason.strip():
            raise ValueError("studio approval requires actor and reason")
        row = self.connection.execute("SELECT status FROM studio_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or row[0] != "candidate_ready":
            raise ValueError("only a candidate_ready studio run can be reviewed")
        approval_id = str(uuid4())
        with self.connection:
            self.connection.execute("INSERT INTO studio_approvals VALUES (?,?,?,?,?,?,?)",
                (approval_id, run_id, scope, decision, actor.strip(), reason.strip(), now()))
        return approval_id

    def current_studio_approval(self, run_id: str, scope: str) -> dict | None:
        row = self.connection.execute(
            "SELECT approval_id,decision,actor,reason,created_at FROM studio_approvals "
            "WHERE run_id=? AND scope=? ORDER BY created_at DESC,rowid DESC LIMIT 1", (run_id, scope)
        ).fetchone()
        if row is None:
            return None
        return dict(zip(("approval_id", "decision", "actor", "reason", "created_at"), row))

    def add_observations(self, asset_id: str, entries: list[dict]) -> list[str]:
        ids = []
        with self.connection:
            for entry in entries:
                start, end = entry.get("start_us"), entry.get("end_us")
                if start is not None and (start < 0 or end is None or end <= start):
                    raise ValueError("Invalid source time range")
                if start is None and end is not None:
                    raise ValueError("end_us requires start_us")
                observation_id = str(uuid4())
                version_id = self.current_version(asset_id)
                self.connection.execute(
                    "INSERT INTO observations (observation_id,asset_id,modality,start_us,end_us,text,confidence,producer,producer_version,status,created_at,asset_version_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (observation_id, asset_id, entry["modality"], start, end,
                     entry["text"], entry.get("confidence"), entry["producer"],
                     entry["producer_version"], "machine_proposed", now(), version_id),
                )
                ids.append(observation_id)
        return ids

    def add_claim(self, statement: str, evidence: list[tuple[str, str]], rationale: str) -> str:
        if not evidence:
            raise ValueError("Claim requires evidence")
        claim_id = str(uuid4())
        with self.connection:
            self.connection.execute("INSERT INTO claims VALUES (?,?,?,?,?)",
                                    (claim_id, statement, "inferred", rationale, now()))
            for observation_id, relation in evidence:
                self.connection.execute("INSERT INTO claim_evidence VALUES (?,?,?)",
                                        (claim_id, observation_id, relation))
        return claim_id

    def review(self, target_type: str, target_id: str, actor: str, decision: str, reason: str) -> str:
        if target_type not in {"observation", "claim"} or decision not in {"verify", "reject", "dispute"}:
            raise ValueError("Invalid review target or decision")
        table, key = ("observations", "observation_id") if target_type == "observation" else ("claims", "claim_id")
        if not self.connection.execute(f"SELECT 1 FROM {table} WHERE {key}=?", (target_id,)).fetchone():
            raise ValueError("Review target does not exist")
        review_id = str(uuid4())
        with self.connection:
            self.connection.execute("INSERT INTO reviews VALUES (?,?,?,?,?,?,?)",
                                    (review_id, target_type, target_id, actor, decision, reason, now()))
        return review_id

    def asset_timeline(self, asset_id: str) -> list[dict]:
        rows = self.connection.execute(
            "SELECT observation_id, modality, start_us, end_us, text, confidence, producer, status "
            "FROM observations WHERE asset_id=? ORDER BY start_us, observation_id", (asset_id,)
        ).fetchall()
        keys = ("observation_id", "modality", "start_us", "end_us", "text", "confidence", "producer", "status")
        return [dict(zip(keys, row)) for row in rows]

    def current_asset_timeline(self, asset_id: str) -> list[dict]:
        version_id = self.current_version(asset_id)
        return [item for item in self.asset_timeline(asset_id)
                if self.connection.execute("SELECT 1 FROM observations WHERE observation_id=? AND asset_version_id=?",
                                           (item["observation_id"], version_id)).fetchone()]

    def register_artifact(self, asset_id: str, kind: str, path: str, content_hash: str,
                          producer: str, producer_version: str, config_hash: str) -> str:
        artifact_id = str(uuid4())
        version_id = self.current_version(asset_id)
        with self.connection:
            self.connection.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?,?,?)",
                (artifact_id, version_id, kind, path, content_hash, producer, producer_version, config_hash, now()))
        return artifact_id

    def add_analysis_bundle(self, asset_id: str, observations: list[dict], artifacts: list[dict]) -> dict:
        """Persist one engine run atomically after external artifacts are complete."""
        observation_ids, artifact_ids = [], []
        version_id = self.current_version(asset_id)
        with self.connection:
            for entry in observations:
                start, end = entry.get("start_us"), entry.get("end_us")
                if start is not None and (start < 0 or end is None or end <= start):
                    raise ValueError("Invalid source time range")
                observation_id = str(uuid4())
                self.connection.execute(
                    "INSERT INTO observations (observation_id,asset_id,modality,start_us,end_us,text,confidence,producer,producer_version,status,created_at,asset_version_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (observation_id, asset_id, entry["modality"], start, end, entry["text"],
                     entry.get("confidence"), entry["producer"], entry["producer_version"],
                     "machine_proposed", now(), version_id),
                )
                observation_ids.append(observation_id)
            for entry in artifacts:
                artifact_id = str(uuid4())
                self.connection.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?,?,?)",
                    (artifact_id, version_id, entry["kind"], entry["path"], entry["content_hash"],
                     entry["producer"], entry["producer_version"], entry["config_hash"], now()))
                artifact_ids.append(artifact_id)
        return {"observation_ids": observation_ids, "artifact_ids": artifact_ids}

    def current_artifacts(self, asset_id: str, *, producer: str | None = None) -> list[dict]:
        version_id = self.current_version(asset_id)
        query = ("SELECT artifact_id,kind,path,content_hash,producer,producer_version,config_hash "
                 "FROM artifacts WHERE asset_version_id=?")
        parameters: list[str] = [version_id]
        if producer is not None:
            query += " AND producer=?"
            parameters.append(producer)
        query += " ORDER BY created_at,artifact_id"
        rows = self.connection.execute(query, parameters).fetchall()
        keys = ("artifact_id", "kind", "path", "content_hash", "producer", "producer_version", "config_hash")
        return [dict(zip(keys, row)) for row in rows]

    def explain_claim(self, claim_id: str) -> dict:
        claim = self.connection.execute("SELECT statement,status,rationale FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
        if claim is None:
            raise KeyError(claim_id)
        evidence = self.connection.execute(
            "SELECT e.relation,o.observation_id,o.asset_id,o.start_us,o.end_us,o.text,o.asset_version_id,"
            "a.content_hash,v.content_hash "
            "FROM claim_evidence e JOIN observations o ON o.observation_id=e.observation_id "
            "JOIN assets a ON a.asset_id=o.asset_id "
            "LEFT JOIN asset_versions v ON v.version_id=o.asset_version_id "
            "WHERE e.claim_id=?", (claim_id,)
        ).fetchall()
        return {"claim_id": claim_id, "statement": claim[0], "status": claim[1],
                "rationale": claim[2], "evidence": [{**dict(zip(
                    ("relation", "observation_id", "asset_id", "start_us", "end_us", "text", "asset_version_id"), row[:7])),
                    "source_is_current": row[7] == row[8]} for row in evidence]}
