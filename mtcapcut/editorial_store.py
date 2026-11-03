"""Append-only SQLite persistence for editorial revisions and receipts."""

from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from .editorial import (
    Chapter, EditSegment, EditorialRevision, ElementPlacement, Receipt, Scene,
    validate_revision,
)


class RevisionConflict(RuntimeError):
    """A revision ID already exists with different immutable content."""


class ReceiptConflict(RuntimeError):
    """A receipt ID already exists with different immutable content."""


class EditorialIntegrityError(RuntimeError):
    """Stored content does not match its recorded digest."""


SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  component TEXT NOT NULL,
  version INTEGER NOT NULL,
  applied_at TEXT NOT NULL,
  PRIMARY KEY (component, version)
);
CREATE TABLE IF NOT EXISTS editorial_revisions (
  revision_id TEXT PRIMARY KEY,
  parent_revision_id TEXT REFERENCES editorial_revisions(revision_id),
  payload_json TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS editorial_revision_assets (
  revision_id TEXT NOT NULL REFERENCES editorial_revisions(revision_id),
  asset_version_id TEXT NOT NULL,
  element_id TEXT NOT NULL,
  PRIMARY KEY (revision_id, asset_version_id, element_id)
);
CREATE TABLE IF NOT EXISTS editorial_receipts (
  receipt_id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL REFERENCES editorial_revisions(revision_id),
  kind TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS editorial_assets_by_version
  ON editorial_revision_assets(asset_version_id, revision_id);
CREATE INDEX IF NOT EXISTS editorial_receipts_by_revision
  ON editorial_receipts(revision_id, created_at, receipt_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(document: dict) -> tuple[str, str]:
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return payload, sha256(payload.encode("utf-8")).hexdigest()


def _revision_document(revision: EditorialRevision) -> dict:
    return {
        "revision_id": revision.revision_id,
        "parent_revision_id": revision.parent_revision_id,
        "chapters": [
            {"chapter_id": x.chapter_id, "title": x.title, "scene_ids": list(x.scene_ids)}
            for x in revision.chapters
        ],
        "scenes": [
            {"scene_id": x.scene_id, "chapter_id": x.chapter_id, "purpose": x.purpose,
             "segment_ids": list(x.segment_ids)} for x in revision.scenes
        ],
        "segments": [
            {"segment_id": x.segment_id, "scene_id": x.scene_id, "start_us": x.start_us,
             "end_us": x.end_us, "intent": x.intent} for x in revision.segments
        ],
        "elements": [
            {"element_id": x.element_id, "kind": x.kind, "track": x.track,
             "start_us": x.start_us, "end_us": x.end_us,
             "segment_ids": list(x.segment_ids), "asset_version_id": x.asset_version_id,
             "source_path": str(x.source_path) if x.source_path is not None else None,
             "source_start_us": x.source_start_us, "text": x.text,
             "parameters": [list(item) for item in x.parameters]}
            for x in revision.elements
        ],
    }


def _revision_from_document(document: dict) -> EditorialRevision:
    return EditorialRevision(
        revision_id=document["revision_id"],
        parent_revision_id=document["parent_revision_id"],
        chapters=tuple(Chapter(x["chapter_id"], x["title"], tuple(x["scene_ids"]))
                       for x in document["chapters"]),
        scenes=tuple(Scene(x["scene_id"], x["chapter_id"], x["purpose"], tuple(x["segment_ids"]))
                     for x in document["scenes"]),
        segments=tuple(EditSegment(x["segment_id"], x["scene_id"], x["start_us"], x["end_us"], x["intent"])
                       for x in document["segments"]),
        elements=tuple(ElementPlacement(
            element_id=x["element_id"], kind=x["kind"], track=x["track"],
            start_us=x["start_us"], end_us=x["end_us"], segment_ids=tuple(x["segment_ids"]),
            asset_version_id=x["asset_version_id"],
            source_path=Path(x["source_path"]) if x["source_path"] is not None else None,
            source_start_us=x["source_start_us"], text=x["text"],
            parameters=tuple(tuple(item) for item in x["parameters"]),
        ) for x in document["elements"]),
    )


def _receipt_document(receipt: Receipt) -> dict:
    return {
        "receipt_id": receipt.receipt_id,
        "kind": receipt.kind,
        "revision_id": receipt.revision_id,
        "subject_ids": list(receipt.subject_ids),
        "producer": receipt.producer,
        "producer_version": receipt.producer_version,
        "input_hashes": list(receipt.input_hashes),
        "output_hashes": list(receipt.output_hashes),
        "config_hash": receipt.config_hash,
        "model_id": receipt.model_id,
        "model_version": receipt.model_version,
        "details": [list(item) for item in receipt.details],
        "created_at": receipt.created_at,
    }


def _receipt_from_document(document: dict) -> Receipt:
    return Receipt(
        receipt_id=document["receipt_id"], kind=document["kind"], revision_id=document["revision_id"],
        subject_ids=tuple(document["subject_ids"]), producer=document["producer"],
        producer_version=document["producer_version"], input_hashes=tuple(document["input_hashes"]),
        output_hashes=tuple(document["output_hashes"]), config_hash=document["config_hash"],
        model_id=document["model_id"], model_version=document["model_version"],
        details=tuple(tuple(item) for item in document["details"]), created_at=document["created_at"],
    )


class EditorialStore:
    """Single-writer store; public APIs never update or delete editorial records."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=DELETE")
        existing_version = self.connection.execute(
            "SELECT MAX(version) FROM schema_migrations WHERE component='editorial'"
        ).fetchone()[0] if self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone() else None
        if existing_version is not None and existing_version > 1:
            self.connection.close()
            raise RuntimeError(f"editorial schema version {existing_version} is newer than supported version 1")
        self.connection.executescript(SCHEMA_V1)
        self._verify_schema_v1()
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(component,version,applied_at) VALUES ('editorial',1,?)",
                (_now(),),
            )

    def _verify_schema_v1(self) -> None:
        required = {
            "editorial_revisions": {"revision_id", "parent_revision_id", "payload_json", "payload_hash", "created_at"},
            "editorial_revision_assets": {"revision_id", "asset_version_id", "element_id"},
            "editorial_receipts": {"receipt_id", "revision_id", "kind", "payload_json", "payload_hash", "created_at"},
        }
        for table, columns in required.items():
            actual = {row[1] for row in self.connection.execute(f"PRAGMA table_info({table})")}
            if not columns.issubset(actual):
                self.connection.close()
                raise RuntimeError(f"incompatible editorial schema table: {table}")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self) -> None:
        self.connection.close()

    def _begin(self) -> None:
        self.connection.execute("BEGIN IMMEDIATE")

    def save_revision(self, revision: EditorialRevision, *, created_at: str | None = None) -> str:
        errors = validate_revision(revision)
        if errors:
            raise ValueError("; ".join(errors))
        payload, digest = _canonical(_revision_document(revision))
        try:
            self._begin()
            existing = self.connection.execute(
                "SELECT payload_hash FROM editorial_revisions WHERE revision_id=?", (revision.revision_id,)
            ).fetchone()
            if existing is not None:
                if existing[0] != digest:
                    raise RevisionConflict(f"revision_id already has different content: {revision.revision_id}")
                self.connection.rollback()
                return digest
            if revision.parent_revision_id is not None and not self.connection.execute(
                "SELECT 1 FROM editorial_revisions WHERE revision_id=?", (revision.parent_revision_id,)
            ).fetchone():
                raise ValueError(f"parent revision does not exist: {revision.parent_revision_id}")
            self.connection.execute(
                "INSERT INTO editorial_revisions VALUES (?,?,?,?,?)",
                (revision.revision_id, revision.parent_revision_id, payload, digest, created_at or _now()),
            )
            for element in revision.elements:
                if element.asset_version_id is not None:
                    self.connection.execute(
                        "INSERT INTO editorial_revision_assets VALUES (?,?,?)",
                        (revision.revision_id, element.asset_version_id, element.element_id),
                    )
            self.connection.commit()
            return digest
        except Exception:
            self.connection.rollback()
            raise

    def load_revision(self, revision_id: str) -> EditorialRevision:
        row = self.connection.execute(
            "SELECT payload_json,payload_hash FROM editorial_revisions WHERE revision_id=?", (revision_id,)
        ).fetchone()
        if row is None:
            raise KeyError(revision_id)
        payload, recorded_hash = row
        actual_hash = sha256(payload.encode("utf-8")).hexdigest()
        if actual_hash != recorded_hash:
            raise EditorialIntegrityError(f"revision payload hash mismatch: {revision_id}")
        revision = _revision_from_document(json.loads(payload))
        if revision.revision_id != revision_id:
            raise EditorialIntegrityError(f"revision identity mismatch: {revision_id}")
        errors = validate_revision(revision)
        if errors:
            raise EditorialIntegrityError("; ".join(errors))
        return revision

    def revision_hash(self, revision_id: str) -> str:
        row = self.connection.execute(
            "SELECT payload_hash FROM editorial_revisions WHERE revision_id=?", (revision_id,)
        ).fetchone()
        if row is None:
            raise KeyError(revision_id)
        return row[0]

    def revision_count(self) -> int:
        return self.connection.execute("SELECT COUNT(*) FROM editorial_revisions").fetchone()[0]

    def dependent_revision_ids(self, asset_version_id: str) -> tuple[str, ...]:
        rows = self.connection.execute(
            "SELECT DISTINCT revision_id FROM editorial_revision_assets WHERE asset_version_id=? ORDER BY revision_id",
            (asset_version_id,),
        ).fetchall()
        return tuple(row[0] for row in rows)

    def append_receipt(self, receipt: Receipt) -> None:
        if (not receipt.receipt_id or not receipt.kind or not receipt.producer or
                not receipt.producer_version or not receipt.config_hash or
                not receipt.subject_ids or not receipt.input_hashes or not receipt.output_hashes):
            raise ValueError("receipt identity, provenance, subjects and hashes are required")
        if (receipt.model_id is None) != (receipt.model_version is None):
            raise ValueError("model_id and model_version must be provided together")
        if len({key for key, _ in receipt.details}) != len(receipt.details):
            raise ValueError("receipt detail keys must be unique")
        try:
            self._begin()
            if not self.connection.execute(
                "SELECT 1 FROM editorial_revisions WHERE revision_id=?", (receipt.revision_id,)
            ).fetchone():
                raise ValueError(f"revision does not exist: {receipt.revision_id}")
            existing = self.connection.execute(
                "SELECT payload_json,payload_hash FROM editorial_receipts WHERE receipt_id=?", (receipt.receipt_id,)
            ).fetchone()
            if existing is not None:
                existing_payload, existing_hash = existing
                if sha256(existing_payload.encode("utf-8")).hexdigest() != existing_hash:
                    raise EditorialIntegrityError(f"receipt payload hash mismatch: {receipt.receipt_id}")
                existing_receipt = _receipt_from_document(json.loads(existing_payload))
                comparable_existing = existing_receipt if receipt.created_at else replace(existing_receipt, created_at="")
                if comparable_existing != receipt:
                    raise ReceiptConflict(f"receipt_id already has different content: {receipt.receipt_id}")
                self.connection.rollback()
                return
            stored = receipt if receipt.created_at else replace(receipt, created_at=_now())
            payload, digest = _canonical(_receipt_document(stored))
            self.connection.execute(
                "INSERT INTO editorial_receipts VALUES (?,?,?,?,?,?)",
                (stored.receipt_id, stored.revision_id, stored.kind, payload, digest, stored.created_at),
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def list_receipts(self, revision_id: str) -> tuple[Receipt, ...]:
        rows = self.connection.execute(
            "SELECT receipt_id,revision_id,kind,payload_json,payload_hash,created_at FROM editorial_receipts "
            "WHERE revision_id=? ORDER BY created_at,receipt_id", (revision_id,),
        ).fetchall()
        receipts = []
        for receipt_id, stored_revision_id, kind, payload, recorded_hash, created_at in rows:
            if sha256(payload.encode("utf-8")).hexdigest() != recorded_hash:
                raise EditorialIntegrityError(f"receipt payload hash mismatch: {receipt_id}")
            receipt = _receipt_from_document(json.loads(payload))
            if (receipt.receipt_id != receipt_id or receipt.revision_id != stored_revision_id or
                    receipt.kind != kind or receipt.created_at != created_at):
                raise EditorialIntegrityError(f"receipt index metadata mismatch: {receipt_id}")
            receipts.append(receipt)
        return tuple(receipts)

    def integrity_check(self) -> tuple[str, ...]:
        result = tuple(row[0] for row in self.connection.execute("PRAGMA integrity_check").fetchall())
        if result != ("ok",):
            raise EditorialIntegrityError("; ".join(result))
        foreign_key_failures = self.connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_failures:
            raise EditorialIntegrityError(f"foreign key check failed: {foreign_key_failures}")
        for revision_id, parent_id in self.connection.execute(
            "SELECT revision_id,parent_revision_id FROM editorial_revisions"
        ).fetchall():
            revision = self.load_revision(revision_id)
            if revision.parent_revision_id != parent_id:
                raise EditorialIntegrityError(f"revision parent metadata mismatch: {revision_id}")
            expected = sorted(
                (element.asset_version_id, element.element_id) for element in revision.elements
                if element.asset_version_id is not None
            )
            actual = self.connection.execute(
                "SELECT asset_version_id,element_id FROM editorial_revision_assets "
                "WHERE revision_id=? ORDER BY asset_version_id,element_id", (revision_id,),
            ).fetchall()
            if expected != actual:
                raise EditorialIntegrityError(f"revision dependency metadata mismatch: {revision_id}")
            self.list_receipts(revision_id)
        return result

    def journal_mode(self) -> str:
        return self.connection.execute("PRAGMA journal_mode").fetchone()[0].lower()

    def backup_to(self, destination: Path) -> None:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        target = sqlite3.connect(destination)
        try:
            self.connection.backup(target)
        finally:
            target.close()
