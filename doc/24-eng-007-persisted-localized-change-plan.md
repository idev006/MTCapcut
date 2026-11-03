# ENG-007 Persisted Localized Change Request Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `mt-build` and `mt-test` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** บันทึกโมเดลตัดต่อคลิปยาวและคำขอแก้เฉพาะช่วงแบบ immutable/recoverable แล้วโหลดกลับมาเลือกขอบเขตเดิมด้วย stable IDs ได้

**Architecture:** เพิ่ม `EditorialStore` เป็น persistence boundary บน project SQLite SSOT โดยเก็บ canonical JSON พร้อม SHA-256, parent integrity, asset-version dependencies และ append-only receipts จากนั้นเพิ่ม `LocalizedChangeService` ซึ่งโหลด revision, คำนวณ edit scope และบันทึก receipt โดยไม่แก้ timeline หรือ CapCut draft อัตโนมัติ

**Tech Stack:** Python 3.14, standard-library `sqlite3`, dataclasses, SHA-256, `unittest`

## Global Constraints

- ใช้ virtual environment `D:\dev\MTCapcut\.venv`
- SQLite ใช้ single-writer และ rollback journal; ไม่เปิด WAL ใน slice นี้
- Revision/receipt ที่บันทึกแล้วห้าม update/delete ผ่าน public API
- ทุก payload มี canonical hash และ fail closed เมื่อ hash ไม่ตรง
- UI, AI provider, render และ CapCut adapter อยู่นอกขอบเขต
- Alembic เป็น migration tool และ SQLAlchemy เป็น ORM; การเพิ่มทั้งสองต้องผ่าน ADR และ Python 3.14 compatibility probe แยกต่างหาก

---

### Task 1: Immutable editorial persistence

**Files:**
- Create: `mtcapcut/editorial_store.py`
- Modify: `mtcapcut/editorial.py`
- Test: `tests/test_editorial_store.py`

**Interfaces:**
- Produces: `EditorialStore.save_revision`, `load_revision`, `append_receipt`, `list_receipts`, `revision_hash`, `dependent_revision_ids`, `integrity_check`, `backup_to`
- Guarantees: same ID/same payload is idempotent; same ID/different payload raises a conflict; missing parent or revision rolls back

- [x] **Step 1: Write failing persistence tests**

```python
with EditorialStore(database) as store:
    digest = store.save_revision(revision)
with EditorialStore(database) as reopened:
    assert reopened.load_revision(revision.revision_id) == revision
    assert reopened.revision_hash(revision.revision_id) == digest
```

- [x] **Step 2: Run the focused test and verify failure**

```powershell
& 'D:\dev\MTCapcut\.venv\Scripts\python.exe' -m unittest tests.test_editorial_store -v
```

- [x] **Step 3: Implement canonical serialization, migration v1 and append-only APIs**

Use tables `schema_migrations`, `editorial_revisions`, `editorial_revision_assets`, and `editorial_receipts`. Validate the domain object before `BEGIN IMMEDIATE`, enforce parent foreign keys, and verify stored hashes on every read.

- [x] **Step 4: Run focused tests until all persistence gates pass**

- [x] **Step 5: Record exact results in development status and dashboard**

### Task 2: Localized change-planning service

**Files:**
- Create: `mtcapcut/change_service.py`
- Test: `tests/test_change_service.py`

**Interfaces:**
- Consumes: `EditorialStore`, `select_edit_scope`
- Produces: `LocalizedChangeService.plan_change(...) -> ChangePlan`

- [x] **Step 1: Write a failing restart-safe 12–13 minute test**

```python
plan = service.plan_change(
    revision_id="rev-18", request_id="change-001",
    start_us=720_000_000, end_us=780_000_000,
    context_us=10_000_000, actor="editor", reason="tighten section",
)
assert plan.scope.editable_segment_ids == ("seg-041", "seg-042", "seg-043", "seg-044")
```

- [x] **Step 2: Verify the focused test fails before implementation**

```powershell
& 'D:\dev\MTCapcut\.venv\Scripts\python.exe' -m unittest tests.test_change_service -v
```

- [x] **Step 3: Implement change planning and append an exact receipt**

Receipt details must include requested/context ranges, actor, reason, editable/context segment IDs, affected element IDs, revision hash and deterministic scope hash. Do not mutate or create an editorial revision.

- [x] **Step 4: Verify invalid range/missing revision/conflicting request ID leave no partial receipt**

- [x] **Step 5: Run the full regression suite**

```powershell
& 'D:\dev\MTCapcut\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

### Task 3: Documentation and Kanban evidence

**Files:**
- Modify: `doc/README.md`
- Modify: `doc/06-test-and-validation-strategy.md`
- Modify: `doc/14-initial-kanban-backlog.md`
- Modify: `doc/17-development-status.md`
- Modify: `doc/18-development-roadmap.md`
- Modify: `doc/19-progress-dashboard.md`
- Modify: `doc/22-long-form-editorial-model.md`

- [x] **Step 1: Update ENG-007 status only from observed test evidence**
- [x] **Step 2: Record limitations: no automatic edit/render, no multi-process writer, no Alembic adoption yet**
- [x] **Step 3: Check every relative Markdown link resolves**
- [x] **Step 4: Report quality gates as PASS/FAIL/BLOCKED/NOT RUN with evidence**

## Review record

Independent code review พบและแก้ก่อนปิด validation: retry ที่ไม่มี timestamp เคยไม่ idempotent, ช่วงนอก timeline เคยสร้าง no-op receipt, integrity check เคยตรวจเพียง SQLite pages และ receipt provenance เคยบังคับไม่ครบ ทั้งสี่กรณีมี regression tests แล้ว ส่วน multi-process concurrency, AssetVersion foreign key ข้าม component และ Alembic adoption ยังคงเป็น ADR/งานถัดไป

## Self-review

- Spec coverage: persistence, immutability, parent integrity, exact receipt, recovery, 12–13 minute scope, transaction rollback and documentation are covered.
- Deliberately excluded: AI semantic quality, automatic timeline mutation, partial render, UI, multi-process writes and ORM migration.
- Type consistency: `EditorialRevision`, `Receipt`, `EditScope`, `ChangePlan` and store/service method names above are the SSOT for this slice.

