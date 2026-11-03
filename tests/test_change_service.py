from pathlib import Path
import tempfile
import unittest

from mtcapcut.change_service import LocalizedChangeService
from mtcapcut.editorial_store import EditorialStore, ReceiptConflict
from tests.test_editorial_store import persisted_revision


class LocalizedChangeServiceTests(unittest.TestCase):
    def test_plan_change_persists_exact_scope_without_creating_revision(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "project.sqlite3"
            with EditorialStore(database) as store:
                store.save_revision(persisted_revision())
                plan = LocalizedChangeService(store).plan_change(
                    revision_id="rev-18", request_id="change-001",
                    start_us=720_000_000, end_us=780_000_000, context_us=10_000_000,
                    actor="editor", reason="ปรับช่วงนาที 12–13", config_hash="cfg-1",
                    created_at="2026-11-02T00:00:00+00:00",
                )
                self.assertEqual(plan.scope.editable_segment_ids,
                                 ("seg-041", "seg-042", "seg-043", "seg-044"))
                self.assertEqual(plan.scope.context_segment_ids,
                                 ("seg-041", "seg-042", "seg-043", "seg-044", "seg-045"))
                self.assertEqual(store.revision_count(), 1)
            with EditorialStore(database) as reopened:
                receipt = reopened.list_receipts("rev-18")[0]
                details = dict(receipt.details)
                self.assertEqual(receipt.receipt_id, "change-001")
                self.assertEqual(details["actor"], "editor")
                self.assertEqual(details["reason"], "ปรับช่วงนาที 12–13")
                self.assertEqual(details["requested_range_us"], "720000000:780000000")
                self.assertEqual(details["editable_segment_ids"], "seg-041,seg-042,seg-043,seg-044")
                self.assertEqual(details["affected_element_ids"], "video-42,music-bed,caption-1")

    def test_invalid_request_and_conflict_do_not_append_partial_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            with EditorialStore(Path(folder) / "project.sqlite3") as store:
                store.save_revision(persisted_revision())
                service = LocalizedChangeService(store)
                with self.assertRaises(ValueError):
                    service.plan_change("rev-18", "bad", 10, 5, 0, "editor", "bad", "cfg")
                self.assertEqual(store.list_receipts("rev-18"), ())
                service.plan_change("rev-18", "same", 720_000_000, 780_000_000, 0,
                                    "editor", "first", "cfg", "2026-11-02T00:00:00+00:00")
                with self.assertRaises(ReceiptConflict):
                    service.plan_change("rev-18", "same", 720_000_000, 780_000_000, 0,
                                        "editor", "changed", "cfg", "2026-11-02T00:00:00+00:00")
                self.assertEqual(len(store.list_receipts("rev-18")), 1)

    def test_retry_without_timestamp_is_idempotent_and_outside_range_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with EditorialStore(Path(folder) / "project.sqlite3") as store:
                store.save_revision(persisted_revision())
                service = LocalizedChangeService(store)
                arguments = ("rev-18", "retry", 720_000_000, 780_000_000, 0,
                             "editor", "same request", "cfg")
                first = service.plan_change(*arguments)
                second = service.plan_change(*arguments)
                self.assertEqual(first.scope_hash, second.scope_hash)
                with self.assertRaises(ValueError):
                    service.plan_change("rev-18", "outside", 900_000_000, 910_000_000, 0,
                                        "editor", "outside", "cfg")
                self.assertEqual(len(store.list_receipts("rev-18")), 1)


if __name__ == "__main__":
    unittest.main()
