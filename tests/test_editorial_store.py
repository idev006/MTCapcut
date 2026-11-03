from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import unittest

from mtcapcut.editorial import (
    Chapter, EditSegment, EditorialRevision, ElementPlacement, Receipt, Scene,
    select_edit_scope,
)
from mtcapcut.editorial_store import (
    EditorialIntegrityError, EditorialStore, ReceiptConflict, RevisionConflict,
)


def persisted_revision() -> EditorialRevision:
    segments = (
        EditSegment("seg-041", "scene-04", 710_000_000, 728_000_000, "bridge-in"),
        EditSegment("seg-042", "scene-04", 728_000_000, 754_000_000, "speaker claim"),
        EditSegment("seg-043", "scene-04", 754_000_000, 767_000_000, "supporting B-roll"),
        EditSegment("seg-044", "scene-04", 767_000_000, 785_000_000, "outcome"),
        EditSegment("seg-045", "scene-04", 785_000_000, 800_000_000, "bridge-out"),
    )
    return EditorialRevision(
        "rev-18", None,
        (Chapter("chapter-04", "ผลดำเนินงาน", ("scene-04",)),),
        (Scene("scene-04", "chapter-04", "อธิบายผล", tuple(x.segment_id for x in segments)),),
        segments,
        (
            ElementPlacement("video-42", "video", "main", 710_000_000, 800_000_000,
                             tuple(x.segment_id for x in segments), "av-video", Path("clip.mp4")),
            ElementPlacement("music-bed", "audio", "music", 710_000_000, 800_000_000,
                             tuple(x.segment_id for x in segments), "av-music", Path("music.mp3")),
            ElementPlacement("caption-1", "caption", "captions", 730_000_000, 760_000_000,
                             ("seg-042", "seg-043"), text="รายงานผลการดำเนินงาน"),
        ),
    )


class EditorialStoreTests(unittest.TestCase):
    def test_round_trip_reopen_preserves_localized_edit_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "project.sqlite3"
            original = persisted_revision()
            with EditorialStore(database) as store:
                digest = store.save_revision(original)
                self.assertEqual(store.revision_hash("rev-18"), digest)
            with EditorialStore(database) as reopened:
                loaded = reopened.load_revision("rev-18")
                self.assertEqual(loaded, original)
                scope = select_edit_scope(loaded, 720_000_000, 780_000_000, context_us=10_000_000)
                self.assertEqual(scope.editable_segment_ids, ("seg-041", "seg-042", "seg-043", "seg-044"))
                self.assertEqual(scope.context_segment_ids, ("seg-041", "seg-042", "seg-043", "seg-044", "seg-045"))
                self.assertEqual(set(scope.affected_element_ids), {"video-42", "music-bed", "caption-1"})
                self.assertEqual(reopened.dependent_revision_ids("av-video"), ("rev-18",))

    def test_revision_is_idempotent_but_conflicting_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            original = persisted_revision()
            with EditorialStore(Path(folder) / "project.sqlite3") as store:
                first = store.save_revision(original)
                self.assertEqual(store.save_revision(original), first)
                changed_scene = replace(original.scenes[0], purpose="เปลี่ยนความหมาย")
                conflict = replace(original, scenes=(changed_scene,))
                with self.assertRaises(RevisionConflict):
                    store.save_revision(conflict)
                self.assertEqual(store.load_revision("rev-18"), original)

    def test_missing_parent_and_invalid_revision_leave_no_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            original = persisted_revision()
            with EditorialStore(Path(folder) / "project.sqlite3") as store:
                with self.assertRaises(ValueError):
                    store.save_revision(replace(original, revision_id="child", parent_revision_id="missing"))
                invalid = replace(original, revision_id="invalid", segments=())
                with self.assertRaises(ValueError):
                    store.save_revision(invalid)
                self.assertEqual(store.revision_count(), 0)

    def test_receipt_is_append_only_idempotent_and_requires_revision(self):
        with tempfile.TemporaryDirectory() as folder:
            receipt = Receipt("receipt-1", "test", "rev-18", ("seg-042",), "engine", "1",
                              ("input",), ("output",), config_hash="cfg",
                              details=(("actor", "editor"),), created_at="2026-11-02T00:00:00+00:00")
            with EditorialStore(Path(folder) / "project.sqlite3") as store:
                with self.assertRaises(ValueError):
                    store.append_receipt(receipt)
                store.save_revision(persisted_revision())
                store.append_receipt(receipt)
                store.append_receipt(receipt)
                with self.assertRaises(ReceiptConflict):
                    store.append_receipt(replace(receipt, output_hashes=("different",)))
                self.assertEqual(store.list_receipts("rev-18"), (receipt,))

    def test_receipt_without_created_at_is_retry_safe_and_requires_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            receipt = Receipt("receipt-1", "test", "rev-18", ("seg-042",), "engine", "1",
                              ("input",), ("output",), config_hash="cfg")
            with EditorialStore(Path(folder) / "project.sqlite3") as store:
                store.save_revision(persisted_revision())
                store.append_receipt(receipt)
                store.append_receipt(receipt)
                self.assertEqual(len(store.list_receipts("rev-18")), 1)
                with self.assertRaises(ValueError):
                    store.append_receipt(replace(receipt, receipt_id="missing-config", config_hash=""))

    def test_tampering_fails_closed_and_backup_is_recoverable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            database = root / "project.sqlite3"
            backup = root / "backup.sqlite3"
            with EditorialStore(database) as store:
                store.save_revision(persisted_revision())
                store.backup_to(backup)
                self.assertEqual(store.integrity_check(), ("ok",))
            with EditorialStore(backup) as recovered:
                self.assertEqual(recovered.load_revision("rev-18"), persisted_revision())
            connection = sqlite3.connect(database)
            connection.execute("UPDATE editorial_revisions SET payload_json='{}' WHERE revision_id='rev-18'")
            connection.commit()
            connection.close()
            with EditorialStore(database) as tampered:
                with self.assertRaises(EditorialIntegrityError):
                    tampered.load_revision("rev-18")

    def test_integrity_check_detects_unhashed_index_column_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "project.sqlite3"
            receipt = Receipt("receipt-1", "test", "rev-18", ("seg-042",), "engine", "1",
                              ("input",), ("output",), config_hash="cfg",
                              created_at="2026-11-02T00:00:00+00:00")
            with EditorialStore(database) as store:
                store.save_revision(persisted_revision())
                store.append_receipt(receipt)
                store.connection.execute(
                    "UPDATE editorial_receipts SET created_at='2099-01-01T00:00:00+00:00' WHERE receipt_id='receipt-1'"
                )
                store.connection.commit()
                with self.assertRaises(EditorialIntegrityError):
                    store.integrity_check()

    def test_database_does_not_enable_wal(self):
        with tempfile.TemporaryDirectory() as folder:
            with EditorialStore(Path(folder) / "project.sqlite3") as store:
                self.assertNotEqual(store.journal_mode(), "wal")


if __name__ == "__main__":
    unittest.main()
