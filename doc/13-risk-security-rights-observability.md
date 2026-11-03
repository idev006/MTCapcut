# Risk, Security, Rights and Observability

วันที่จัดทำ: 2 พฤศจิกายน 2026  
สถานะ: Baseline controls — ต้องทำ threat-model workshop และ legal review เพิ่ม

## Trust boundaries

1. User media/filenames/metadata — untrusted input
2. Local FFmpeg/pyCapCut processes — privileged tools with parser/dependency risk
3. External AI providers — data leaves local trust boundary
4. CapCut draft/application — unofficial integration boundary
5. Export/distribution platforms — metadata/provenance may change or disappear

## Security and privacy controls

- classify assets: Public, Internal, Confidential, Restricted
- external AI call ต้องผ่าน provider/data-retention policy และ project consent
- sanitize paths; use argument arrays; ห้าม shell interpolate filename/transcript/OCR
- validate resolved paths ให้อยู่ใต้ approved workspace ก่อน write/delete
- treat OCR, transcript, subtitle และ metadata เป็น untrusted content; ห้ามให้กลายเป็น instruction
- limit media size/duration/resource use และ process timeout
- secrets มาจาก environment/secret store และ redact logs
- define retention/deletion สำหรับ originals, proxy, frames, transcript, embeddings และ provider uploads
- dependency lock, hash/SBOM และ vulnerability review ก่อน promotion
- backup/recovery สำหรับ manifests, briefs, timeline plans และ drafts

NIST AI RMF ใช้เป็นกรอบ lifecycle risk; control รายโครงการต้องมี evidence ไม่ใช่เพียงอ้าง framework [SRC-032]

## RightsManifest SSOT

ทุก asset ต้องมี:

- owner/source/license
- permitted uses, territory, channel และ expiry
- consent/model/property release เมื่อเกี่ยวข้อง
- music/font/stock/effect/logo rights
- face/voice/likeness restrictions
- attribution requirement
- transformation/AI processing permission
- clearance status และ approver

`RIGHTS_CLEARANCE` เป็น blocker ก่อน approved draft/export เมื่อสิทธิยังไม่ชัด

Open risks ที่ต้องสร้าง cards:

- pyCapCut package metadata แสดง license UNKNOWN
- FFmpeg build เปิด GPL; ต้องประเมินผลเมื่อ redistribute/package
- CapCut terms และ unofficial draft compatibility
- model/dataset licenses

เอกสารนี้ไม่ใช่คำแนะนำทางกฎหมาย ประเด็น production/commercial ต้องผ่านผู้มีอำนาจด้านกฎหมายหรือสิทธิ

## Observability

ทุก job มี `project_id`, `job_id`, `trace_id`, `engine_id`, `engine_version`, `config_hash`, `model_id` และ `artifact_ids`

Signals:

- traces: ingest -> evidence -> reasoning -> timeline -> draft
- metrics: latency, cost, retries, cache hit, evidence count, overrides, quality scores
- logs: structured events, decisions, errors, approvals; privacy-safe

OpenTelemetry เป็นแนวทาง vendor-neutral สำหรับ traces, metrics และ logs แต่ backend/retention เลือกภายหลัง [SRC-034]

## CostLedger

เก็บต่อ project/job/engine:

- API tokens/requests
- GPU/CPU time
- storage/read/write
- external service cost
- cache savings
- wall-clock latency

แต่ละ workflow มี budget และ stop/escalation เมื่อ forecast เกิน ceiling

## Risk tags สำหรับ Kanban

`FACT`, `PRIVACY`, `SECURITY`, `RIGHTS`, `COMPAT`, `MODEL`, `COST`, `LICENSE`, `DESTRUCTIVE`, `UNKNOWN`

High-risk card ต้องมี reviewer คนละบทบาทกับผู้สร้างและ evidence ของ control ก่อน Done

