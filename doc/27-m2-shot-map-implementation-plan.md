# M2 Shot Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง ShotCandidateEngine และ AdaptiveFrameSamplingEngine ที่สร้าง shot map พร้อม timestamp/provenance ลง Asset Understanding Map โดยไม่ให้ผู้ควบคุมงานเปิดดูคลิปโดยตรง

**Architecture:** `ShotMapService` เป็น orchestrator เรียก PySceneDetect adapter และ local FFmpeg frame extractor แยกกันตาม engine boundary จากนั้นบันทึก machine-proposed shot observations และ content-addressed frame artifacts ลง SSOT การรันซ้ำใช้ asset hash + config hash เป็น cache identity และไม่สร้าง observation ซ้ำ

**Tech Stack:** Python 3.14, PySceneDetect 0.7.2, OpenCV 5.0.0.93, FFmpeg, SQLite Asset Understanding Map, unittest

## Global Constraints

- ใช้ virtual environment `D:\dev\MTCapcut\.venv` เท่านั้น
- FFmpeg อยู่ที่ `D:\libs\ffmpeg`
- Engine ไม่เรียก engine อื่นโดยตรง; orchestration อยู่ใน application service
- ทุก observation ต้องอ้าง asset ID และ original microsecond timebase
- ผล shot detection เป็น candidate ไม่ใช่ editorial cut และห้ามสร้างความหมายเชิงเนื้อหา
- การรันซ้ำด้วย asset/config เดิมต้อง reuse SSOT result
- งานเขียนไฟล์ต้องอยู่ใต้ project workspace และไม่ overwrite CapCut drafts

---

### Task 1: Typed shot-analysis configuration

**Files:**
- Modify: `mtcapcut/config.py`
- Modify: `config.toml`
- Modify: `config.example.toml`
- Test: `tests/test_config_categories.py`

**Interfaces:**
- Produces: `ShotAnalysisSettings(enabled, threshold, min_scene_len_frames, frames_per_shot, frame_width)`

- [ ] **Step 1: Write failing validation tests** for invalid threshold, frame count and width.
- [ ] **Step 2: Run** `python -m unittest tests.test_config_categories -v` and confirm failure.
- [ ] **Step 3: Implement typed TOML loading** with positive numeric bounds and conservative defaults.
- [ ] **Step 4: Run the focused tests** and confirm PASS.

### Task 2: Shot candidate and adaptive sampling engines

**Files:**
- Create: `mtcapcut/shot_detection.py`
- Test: `tests/test_shot_detection.py`

**Interfaces:**
- Produces: `ShotCandidate(start_us, end_us, boundary_score)`
- Produces: `SceneDetectShotEngine.detect(source: Path) -> list[ShotCandidate]`
- Produces: `sample_times(shots, frames_per_shot) -> list[FrameSample]`

- [ ] **Step 1: Generate a synthetic hard-cut fixture** in a temporary directory with FFmpeg.
- [ ] **Step 2: Assert candidates are gapless, positive and aligned to original time.**
- [ ] **Step 3: Implement PySceneDetect ContentDetector adapter** and retain raw `content_val` rather than inventing calibrated confidence.
- [ ] **Step 4: Implement deterministic per-shot sampling** bounded inside each source range.
- [ ] **Step 5: Run** `python -m unittest tests.test_shot_detection -v` and confirm PASS.

### Task 3: Shot map orchestration and SSOT persistence

**Files:**
- Create: `mtcapcut/shot_map_service.py`
- Modify: `mtcapcut/map.py`
- Test: `tests/test_shot_map_service.py`

**Interfaces:**
- Consumes: `SceneDetectShotEngine`, `extract_frame`, `UnderstandingMap`
- Produces: `ShotMapResult(asset_id, shots, frame_artifact_ids, cache_hit)`

- [ ] **Step 1: Add an asset-detail query** that returns current path/hash/kind without exposing mutable database rows.
- [ ] **Step 2: Write a fake-engine service test** proving observation timestamps, artifacts and producer/config identity are persisted.
- [ ] **Step 3: Implement deterministic config hash and cache lookup.**
- [ ] **Step 4: Implement frame extraction and artifact registration** under `artifacts/shot-map/<asset>/<asset-hash>-<config-hash>/`.
- [ ] **Step 5: Run focused service tests** and confirm a second call reports `cache_hit=true` without duplicate observations.

### Task 4: CLI, real-media smoke and documentation

**Files:**
- Modify: `mtcapcut/__main__.py`
- Modify: `doc/17-development-status.md`
- Modify: `doc/19-progress-dashboard.md`
- Create: `workspace/road-report-001/editorial/shot-map-smoke-report.md`

**Interfaces:**
- Produces command: `python -m mtcapcut analyze-shots <project_id> <asset_id>`

- [ ] **Step 1: Add the CLI command** returning JSON only.
- [ ] **Step 2: Run full regression tests.**
- [ ] **Step 3: Run the command against the registered ceremony clip** without opening media manually.
- [ ] **Step 4: Run it again and require a cache hit.**
- [ ] **Step 5: Record counts, duration, artifact IDs, limitations and exact commands in project documentation.**

## Self-review

- Spec coverage: M2 shot candidates, timestamps, provenance, cache and CLI are covered; semantic vision/OCR remain separate cards.
- Placeholder scan: no implementation step relies on unspecified behavior.
- Type consistency: `ShotCandidate`, `FrameSample` and `ShotMapResult` are defined once and consumed by later tasks.
- Known gap: boundary confidence is not calibrated; store raw detector score and leave confidence unset until EXP-003 benchmark supplies calibration.

## Execution

User requested immediate implementation. This plan will be executed inline in the current session with test checkpoints; no subagent dispatch is required.

## Execution result — 2 November 2026

Tasks 1–4 completed inline. Focused and full tests passed; live smoke produced 24 shot candidates and 72 sampled-frame artifacts, and the identical second run returned a cache hit without duplicate SSOT rows. `EXP-003` remains open for annotated benchmark and calibrated boundary confidence.
