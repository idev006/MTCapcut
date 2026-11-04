# Development Status

วันที่: 3 พฤศจิกายน 2026  
สถานะ: Foundation และ CapCut compatibility slice ทำงานได้; ยังไม่ใช่ world-class production release

## ใช้งานได้แล้ว

- `config.toml` เป็น central configuration สำหรับ workspace, FFmpeg/ffprobe และ CapCut installation root
- `python -m mtcapcut doctor` ตรวจ Python, FFmpeg, ffprobe, pyCapCut และ CapCut แบบ read-only พร้อม JSON/exit code แม้ binary ที่ระบุใน config หาย
- `ingest` และ `ingest-bundle` รับ text, audio, picture และ clip; ตรวจ role, hash, technical metadata และลงทะเบียนแบบ transaction
- Asset Understanding Map เก็บ logical asset, immutable versions, observations, claims, reviews และ artifacts; เมื่อไฟล์เปลี่ยน version ผลวิเคราะห์เดิมยังตรวจย้อนหลังได้แต่ไม่ปรากฏใน current view
- `perception.py` แยกเฟรมและเสียงตาม timestamp เป็น evidence artifacts โดยยังไม่กล่าวอ้างความหมายเกินหลักฐาน
- `ShotMapService` ใช้ PySceneDetect สร้าง shot candidates, เลือก sampled frames แบบ deterministic, บันทึก observations/artifacts แบบ transaction และ reuse ผลตาม asset/config hash
- Timeline Plan เป็นโมเดลกลางที่ไม่ผูก UI/pyCapCut และตรวจ time range, source, track overlap และ main visual continuity
- Long-form editorial model แยก Chapter/Scene/EditSegment, ElementPlacement, Revision, Recipe และ Receipt; เลือกขอบเขตแก้ไขจาก timecode เป็น stable IDs พร้อมตรวจ elements ที่คร่อมช่วง
- `EditorialStore` บันทึก revision และ receipt แบบ append-only ด้วย canonical SHA-256, parent integrity, asset-version dependency query, SQLite backup และ reopen/recovery
- `LocalizedChangeService` แปลงคำขอเช่น “แก้นาที 12–13” เป็น editable/context segments และ affected elements พร้อม exact receipt โดยยังไม่เปลี่ยน timeline อัตโนมัติ
- config schema v2 แบ่ง runtime, UI bridge, storage, security, observability และ AI provider profiles; config v1 ยังอ่านได้
- `EngineRunner` ส่งงานแบบ non-blocking พร้อม polling events, callback, progress, cooperative cancellation และ structured failure สำหรับ UI ในอนาคต
- AI provider baseline ใช้ contract เดียวกับ OpenRouter และ local OpenAI-compatible server โดย secret อ่านจาก environment
- Media Cognition Engine รับ frame/audio evidence จาก Eye/Ear engine, ส่งผ่าน AI provider, ตรวจ structured observations และเขียนผลแบบ `machine_proposed` ลง Asset Understanding Map; bounded live smoke ผ่านกับภาพนิ่ง เฟรมวิดีโอที่ timestamp 8 วินาที และเสียงช่วง 30–45 วินาที โดยยังไม่ถือว่าความหมายถูกต้องจนกว่าจะผ่าน ground-truth review
- External AI Data Policy Gate บังคับ central switch, per-asset classification/approval, payload ceiling และ append-only revoke history ก่อนอ่าน evidence เป็น base64/ก่อน transport; CLI `set-ai-policy` และ `show-ai-policy` รองรับ audit workflow
- Windows launch มี requirements direct/lock และ `start`/doctor/CLI/test batch wrappers; ยังไม่มี installer หรือ release ZIP
- pyCapCut adapter ตรึง `pycapcut==0.0.4`, เขียนเฉพาะ sandbox ที่มี marker, ไม่ overwrite draft และสร้าง video/picture/audio/text tracks
- `PreviewRenderEngine` render Timeline Plan เป็น private-review MP4 ด้วย FFmpeg โดยไม่ overwrite, ใช้เพลงหนึ่งแทร็ก, motion สำหรับภาพนิ่ง, title ภาษาไทย, watermark และ loudness normalization
- Autonomous Studio Council slice อ่าน immutable snapshot ที่ไม่มี raw paths, เรียกผู้เชี่ยวชาญ 6 ฝ่ายแยกกัน, เก็บ recommendation/objection append-only, ให้ Clip Director/Lead Editor สร้าง candidate และใช้ Evidence/Fact/Timeline gates ก่อน render
- Human approval ledger แยก `private_preview` จาก `publication`; autonomous candidate ที่ถูกแก้ไขนอก ledger หรือยังไม่อนุมัติ render ผ่าน studio command ไม่ได้
- fixture สังเคราะห์สร้างซ้ำได้ด้วย `scripts/create_compatibility_fixture.py`

## หลักฐานทดสอบล่าสุด

- Automated tests: `103 tests, 0 failures`
- Windows batch: `doctor.bat` และ `run-tests.bat` ผ่าน; `start.bat` เป็นเมนูเรียก engines โดยไม่ติดตั้งหรือแก้ environment
- Editorial persistence/change planning: `11 tests, 0 failures` ครอบคลุม immutability, retry idempotency, rollback, metadata/payload tamper detection, backup/reopen, provenance requirements, no-op rejection และ scope นาที 12–13
- `doctor`: PASS บน Python 3.14.0, pyCapCut 0.0.4, FFmpeg/ffprobe build `2025-10-30`, CapCut 9.6 และ 9.7 ถูกค้นพบ
- CapCut 9.7.0.4153: พบและเปิด `MT_AI_COMPAT_20261102_01` ได้ เห็น timeline 3 วินาทีที่มีวิดีโอ, ภาพ, MP3 และข้อความไทย
- Manual local export: PASS; ได้ H.264 720×1280 + AAC, duration 3.018 วินาที, 1,902,659 bytes
- ปิด `Sync exported videos to space` และไม่กด Share; การทดสอบไม่ได้สั่ง Sync/Share (ไม่ได้ทำ network capture)
- Real-project technical proof `road-report-001`: ingest MP3 ภาษาไทย 2 ไฟล์, extract embedded artwork, สร้าง Timeline Plan 8:43.248 และ pyCapCut draft 3 tracks/6 segments สำเร็จ; rights ยัง `unknown` และยังไม่เปิด/export ใน CapCut
- Real-media profile rough cut v3: ลงทะเบียนภาพกิจกรรมทางการและคลิปพิธีพร้อม provenance, สร้าง silent proxy เพื่อตัดเสียงต้นฉบับ, สร้าง draft 32 วินาทีโดยใช้ `โป้ง - หัวใจไม่เคยหยุดทำ1.mp3` เพียงเพลงเดียว และคัดลอกไป CapCut ด้วยชื่อ `MT_ROAD_REPORT_001_POLICE6_PROFILE_V3`; ยังห้ามเผยแพร่จนกว่าจะผ่าน rights gates
- Direct previews v1/v2 พิสูจน์เฉพาะ renderer integration และ technical QA; ถูกเพิกถอนจาก creative/studio evaluation เพราะ editorial decisions มี Codex ช่วยออกแบบ จึงไม่ใช่หลักฐานว่า MTCapcut เข้าใจบรีฟหรือทำงานระดับ world-class
- Autonomous run `286f8675-9061-4b64-a60b-faec084b3386` เป็น legacy/noncompliant evidence: 45 วินาทีผิด brief 30–35 วินาทีและไม่มี candidate-bound compliance proof จึงถูกปิด render
- Typed ProjectBrief, deterministic Brief Compliance Validator และ engine-owned revision loop ทำงานแล้ว: test พิสูจน์ 45 วินาทีถูกส่งกลับให้ Lead Editor engine แก้เป็น 32 วินาที; ถ้ายังผิดครบ 3 รอบจบ `candidate_rejected` และไม่สร้าง output
- Semantic evidence binder ไม่นับ `shot` เป็นความเข้าใจเนื้อหาและบังคับ temporal overlap แล้ว; SSOT-only readiness ของ `road-report-001` ยัง BLOCKED เพราะ 11/14 media ไม่มี semantic observations/policy, silent proxy ครอบคลุมเพียง 1/24 shots และเพลงที่เลือกครอบคลุมประมาณ 8.97%
- Provider-facing objections เปลี่ยนเป็น typed findings แล้ว โดยมี category/severity/evidence/action/owner; deterministic policy แยก private/public blockers และปฏิเสธประโยคประเภท “No explicit objection” ไม่ให้กลายเป็น blocker ปลอม
- Autonomous run `42dca66f-0e51-43db-bb95-e33767e3f7c2` ผ่าน typed brief/compliance และ private-preview gate; render v7 สำเร็จเป็น H.264/AAC 1920×1080 ระยะเวลา 35.000 วินาที ส่วน publication เป็นการตัดสินใจและความรับผิดชอบของผู้นำไปเผยแพร่ โดยระบบเก็บ rights findings ไว้ประกอบการตัดสินใจ
- OpenRouter cognition เติม semantic observations ให้ silent proxy อีก 23 shots และภาพกิจกรรมทางการ 4 ภาพ ทำให้ intended visual set มี coverage 24/24 shots และ 5/5 photos; audio gap 10–20 วินาทีตอบ empty observations และถูก fail closed โดยไม่มีข้อมูลปลอมเข้า SSOT
- Professional Finishing Engine ใช้ OpenRouter เลือก transition/filter/motion/text animation แบบ typed allowlist พร้อม rationale และ pyCapCut materialize เป็น draft `MT_ROAD_REPORT_001_AUTONOMOUS_PRO_V2`; CapCut 9.7 เปิด timeline 35 วินาทีได้และมี transition material 1, effects 3, animation 1 แต่ filter/text-animation บาง resource แสดง `Couldn't download filter` / `Animation loss` จึงต้องเพิ่ม local-safe compatibility profile
- งานรอบ 3 นาที: ภาพ event_photo 57 ภาพถูก ingest และวิเคราะห์ผ่าน OpenRouter Vision ลง SSOT แล้ว; brief ใหม่กำหนด 170–190 วินาที แต่ Studio Council V9–V15 ยังไม่ผ่าน brief compliance (V15 ได้เพียง 72 วินาทีและขาดข้อความหลัก) จึงยังไม่มี draft รอบ 3 นาที ขนาด snapshot JSON 137,204 bytes เป็นสัญญาณว่าต้องแบ่ง context/sequence ตาม doc/34

รายละเอียด: [CapCut Compatibility Report](./21-capcut-compatibility-report.md)
และ [Long-form Editorial Model](./22-long-form-editorial-model.md)

## ยังไม่เสร็จ

- OCR, semantic batch scene/event understanding, Thai ASR benchmark และ audio-event benchmark
- professional blind evaluation ของ autonomous output และ typed objection severity/resolution workflow
- normalized rights manifest, approval authority, retention cleanup automation, provider-terms verification และ license decision สำหรับ distribution
- application services ส่วนอื่น, การ apply change ที่ผ่านอนุมัติ, orchestrator, job queue, UI และ CI
- ADR เต็มสำหรับ SQLAlchemy ORM/Alembic, multi-process writer และ migration จาก schema เดิม; slice ปัจจุบันใช้ migration boundary v1 + single-writer rollback journal
- local-model capability probe, streaming, provider retry/rate-limit/cost policy และ persistent job/event queue
- UI toolkit และการ marshal callbacks/events กลับ UI main thread
- การทดสอบกับ assets งานจริงที่มีสิทธิและคำตอบอ้างอิง

ดังนั้นระบบมี “ตาและหูเชิงกล” สำหรับ probe/extract และมี SSOT map รองรับหลักฐานแล้ว แต่ยังไม่ “เห็น ได้ยิน เข้าใจ” เทียบเท่าทีมงานระดับโลก การพิสูจน์ดังกล่าวต้องใช้ชุดงานจริง, annotations และ blind human review

## คำสั่งตรวจสอบ

```powershell
& 'D:\dev\MTCapcut\.venv\Scripts\python.exe' -m mtcapcut doctor
& 'D:\dev\MTCapcut\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```
