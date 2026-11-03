# MTCapcut Foundation Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with a fresh review gate after each task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้างฐานระบบ MTCapcut ที่โหลด configuration ได้ ตรวจ environment และ media ได้ มี domain contracts กลาง และพิสูจน์การสร้าง CapCut test draft อย่างปลอดภัย

**Architecture:** ใช้ ports-and-adapters โดย domain models ไม่อ้างอิง pyCapCut, FFmpeg หรือ UI; Workflow Orchestrator เรียก engines ผ่าน protocols และบันทึก artifacts/decisions ลง SSOT ที่กำหนดไว้ การรองรับ UI เกิดผ่าน application service เดียวกับ CLI/test harness

**Execution note:** [Kanban backlog](./14-initial-kanban-backlog.md) เป็นคิวงานและสถานะจริง แผนนี้เป็น technical reference; งาน Asset Intake และ cognition proof เพิ่มใน `ENG-005`/`EXP-004` และ [contract](./15-asset-intake-and-cognition-contract.md)

**Tech Stack:** Python 3.14, pytest, TOML/tomllib, FFmpeg/ffprobe, pyCapCut 0.0.4, CapCut Desktop 9.7.0.4153

## Global Constraints

- ใช้ Python ที่ `D:\dev\MTCapcut\.venv\Scripts\python.exe`
- ใช้ FFmpeg/ffprobe ใต้ `D:\libs\ffmpeg\bin`
- ใช้ pyCapCut `0.0.4`; ห้ามใช้ API 0.1.0 ปะปน
- test ห้ามเขียนทับ CapCut draft ที่มีอยู่
- UI ห้ามเรียก FFmpeg หรือ pyCapCut โดยตรง
- ค่าร่วมทั้งหมดต้องผ่าน typed central configuration
- secret ห้ามอยู่ใน committed TOML

---

### Task 1: Project skeleton and verified configuration

**Files:**
- Create: `pyproject.toml`
- Create: `config/default.toml`
- Create: `src/mtcapcut/config/models.py`
- Create: `src/mtcapcut/config/loader.py`
- Test: `tests/config/test_loader.py`

**Interfaces:**
- Produces: `load_config(default_path: Path, local_path: Path | None, env: Mapping[str, str]) -> AppConfig`
- Produces: immutable `AppConfig` with paths, FFmpeg and CapCut sections

- [ ] เขียน tests สำหรับ default loading, local override, environment override, missing executable และ invalid schema version
- [ ] รัน `D:\dev\MTCapcut\.venv\Scripts\python.exe -m pytest tests/config/test_loader.py -v` และยืนยันว่า fail เพราะ implementation ยังไม่มี
- [ ] สร้าง typed models และ loader โดย parse TOML ครั้งเดียว normalize paths และตรวจ executable
- [ ] รัน test เดิมจนผ่าน
- [ ] ตรวจว่าไม่มี secret หรือ absolute path กระจายนอก configuration

### Task 2: Environment discovery and report

**Files:**
- Create: `src/mtcapcut/environment/models.py`
- Create: `src/mtcapcut/environment/discovery.py`
- Create: `src/mtcapcut/cli/doctor.py`
- Test: `tests/environment/test_discovery.py`

**Interfaces:**
- Consumes: `AppConfig`
- Produces: `EnvironmentReport` containing Python, FFmpeg, ffprobe, pyCapCut and CapCut versions with evidence

- [ ] เขียน tests โดยใช้ fake process runner และ temporary CapCut `ProductInfo.xml`
- [ ] ยืนยันว่า tests fail ก่อน implementation
- [ ] implement discovery โดยไม่ hard-code version directory และไม่เลือกจากชื่อ folder เพียงอย่างเดียว
- [ ] เพิ่ม CLI `doctor` ที่คืน non-zero เมื่อ required dependency ไม่ผ่าน policy
- [ ] รัน unit tests และรัน doctor กับ environment จริง เก็บ output เป็น artifact

### Task 3: Domain contracts and invariants

**Files:**
- Create: `src/mtcapcut/domain/media.py`
- Create: `src/mtcapcut/domain/brief.py`
- Create: `src/mtcapcut/domain/recommendation.py`
- Create: `src/mtcapcut/domain/timeline.py`
- Test: `tests/domain/test_timeline.py`

**Interfaces:**
- Produces: `MediaAsset`, `EvidenceRef`, `ProjectBrief`, `StudioRecommendation`, `EditDecision`, `TimelinePlan`
- Invariant: time ranges non-negative, source range within asset duration, stable IDs and schema versions required

- [ ] เขียน tests สำหรับ valid model, negative time, out-of-range segment, missing evidence และ illegal overlap
- [ ] ยืนยันว่า tests fail ก่อน implementation
- [ ] implement immutable domain models โดยไม่ import pycapcut
- [ ] เพิ่ม `TimelineValidator.validate(plan, catalog) -> QualityReport`
- [ ] รัน domain tests จนผ่าน

### Task 4: ffprobe media inspection adapter

**Files:**
- Create: `src/mtcapcut/ports/process_runner.py`
- Create: `src/mtcapcut/adapters/ffmpeg/probe.py`
- Create: `src/mtcapcut/media/catalog.py`
- Test: `tests/adapters/test_ffprobe.py`
- Test asset: `tests/fixtures/media/README.md`

**Interfaces:**
- Consumes: media `Path`, `AppConfig.ffmpeg`
- Produces: normalized `MediaAsset` plus raw JSON artifact and content hash

- [ ] สร้าง licensed synthetic media fixture ด้วย FFmpeg command ที่บันทึกไว้ใน README
- [ ] เขียน tests สำหรับ video+audio, no-audio และ corrupt input
- [ ] implement process runner ที่เก็บ exit code/stdout/stderr แบบมี timeout
- [ ] normalize ffprobe JSON โดยรักษา raw artifact
- [ ] รัน integration tests กับ FFmpeg build ที่ติดตั้ง

### Task 5: Engine protocol and workflow orchestrator

**Files:**
- Create: `src/mtcapcut/engines/base.py`
- Create: `src/mtcapcut/workflow/orchestrator.py`
- Create: `src/mtcapcut/workflow/state.py`
- Test: `tests/workflow/test_orchestrator.py`

**Interfaces:**
- Produces: `Engine.execute(context: EngineContext) -> EngineResult`
- Produces: resumable `WorkflowOrchestrator.run(job: ProductionJob) -> JobResult`

- [ ] เขียน tests สำหรับ success, retryable failure, blocker, resume และ cache invalidation เมื่อ config/engine version เปลี่ยน
- [ ] ยืนยันว่า tests fail ก่อน implementation
- [ ] implement engine registry, job state และ structured failure
- [ ] บังคับไม่ให้ engine เรียก engine อื่นโดยตรงผ่าน public contract
- [ ] รัน workflow tests จนผ่าน

### Task 6: Provider-neutral Timeline Plan to pyCapCut adapter

**Files:**
- Create: `src/mtcapcut/ports/draft_writer.py`
- Create: `src/mtcapcut/adapters/pycapcut/writer.py`
- Create: `src/mtcapcut/adapters/pycapcut/mapping.py`
- Test: `tests/adapters/test_pycapcut_mapping.py`

**Interfaces:**
- Consumes: validated `TimelinePlan`, `MediaCatalog`, isolated output directory
- Produces: `DraftArtifact` with manifest, hashes and pyCapCut version

- [ ] เขียน mapping tests โดยใช้ fake draft writer สำหรับ video, image, audio และ Thai text
- [ ] เพิ่ม safety test ว่า existing/non-test directory ไม่ถูก overwrite
- [ ] implement mapping สำหรับ pyCapCut 0.0.4 เท่านั้นและตรวจ version ตอน runtime
- [ ] สร้าง draft fixture ใน temporary directory
- [ ] ตรวจ manifest ว่าผูก timeline decisions กับ output segments ได้

### Task 7: CapCut compatibility proof

**Files:**
- Create: `tests/compatibility/capcut_9_7_checklist.md`
- Create: `tests/compatibility/generate_fixture.py`
- Create: `doc/compatibility-capcut-9.7.0.4153.md`

**Interfaces:**
- Consumes: known Timeline Plan fixture
- Produces: evidence-backed PASS/FAIL report for CapCut `9.7.0.4153`

- [ ] สร้าง fixture draft ชื่อ unique โดยไม่ใช้โฟลเดอร์งานจริง
- [ ] เปิดใน CapCut และบันทึก screenshot ของ tracks, Thai text และ duration
- [ ] บันทึก ปิด และเปิดใหม่ แล้วตรวจองค์ประกอบซ้ำ
- [ ] export ด้วยมือและตรวจด้วย ffprobe
- [ ] บันทึก PASS/FAIL ราย feature; ห้ามสรุป compatibility จากการเปิดได้อย่างเดียว

### Task 8: Research spike for media intelligence

**Files:**
- Create: `research/benchmark_media_intelligence.py`
- Create: `tests/fixtures/research/manifest.json`
- Create: `doc/media-intelligence-benchmark.md`

**Interfaces:**
- Produces: benchmark report for shot boundaries, transcription and image-text retrieval
- Does not produce: production engine selection before evidence review

- [ ] สร้างชุดข้อมูลประเมินที่มี human annotations และสิทธิใช้งาน
- [ ] นิยาม metrics ได้แก่ boundary F1/tolerance, transcript error review, retrieval precision@k และ runtime
- [ ] ทดลอง candidate implementations ที่รองรับ environment หรือ environment แยกที่บันทึกชัดเจน
- [ ] วิเคราะห์ failure cases โดยเฉพาะภาษาไทย ชื่อเฉพาะ ภาพซ้ำ และ short-form cuts
- [ ] เขียน ADR เลือก implementation หรือสรุปว่ายังไม่มีตัวเลือกผ่านเกณฑ์

## Self-review

- ครอบคลุม environment, SSOT/config, domain contracts, engines, FFmpeg, pyCapCut, compatibility และ research spike
- ไม่มี implementation task ใดผูก domain กับ UI
- API pyCapCut ถูกจำกัดที่ adapter และ version 0.0.4
- งาน AI ยังเป็น benchmark ก่อนเลือก dependency เพื่อลดการตัดสินจากสมมติฐาน
- แผนยังไม่สร้าง UI เพราะ foundation และ compatibility ต้องผ่านก่อน

