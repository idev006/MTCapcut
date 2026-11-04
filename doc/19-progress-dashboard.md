# MTCapcut Progress Dashboard

อัปเดตล่าสุด: 4 พฤศจิกายน 2026
แหล่งสถานะงาน: [Kanban Backlog](./14-initial-kanban-backlog.md)  
แผนระยะ: [Development Roadmap](./18-development-roadmap.md)

ผลทดสอบล่าสุด: [ร่าง autonomous 3 นาทีและ CapCut export V22](./36-three-minute-autonomous-retest.md); [ผลวินิจฉัยและแผนหกเฟส](./37-v22-diagnosis-design-and-delivery-plan.md). V22 export ได้จริง แต่พบ title ผิดเจตนาและความเสี่ยงด้าน handoff/QA; แก้ engine แล้วโดยยังไม่ re-run สร้างคลิปใหม่ คุณภาพระดับ world-class ยังไม่ผ่าน blind review.

## ภาพรวมที่ตรวจได้

| ความสามารถ | สถานะ | หลักฐานล่าสุด | ขั้นถัดไป |
|---|---|---|---|
| Central TOML + doctor | Implemented categorized slice | schema v2 runtime/UI/storage/security/AI profiles, v1 compatibility และ doctor PASS | layered override/config editor ในอนาคต |
| External AI data policy | Implemented enforcement slice | central switch + append-only per-asset classification/approval + payload ceiling; fail-before-transport tests | retention cleanup, provider-terms verification และ authorization receipts |
| Asset bundle intake | Implemented slice | atomic asset registration, roles, hash, ffprobe, CLI tests | command-level observation transaction, rights manifest, per-file error UX |
| Asset Understanding Map | Implemented slice | immutable versions, current/history queries, claims/reviews/artifacts | correction API, snapshots, concurrency |
| ตา/หูเชิงกล | Implemented shot-map slice | 24 shot candidates + 72 sampled frames จากคลิปจริง, cache hit รอบซ้ำ; local/cloud ear smoke | OCR, semantic batch analysis และ annotated benchmark |
| สมอง: intent/story/edit decisions | Typed-brief/revision slice PASS; live rerun BLOCKED | strict ProjectBrief + deterministic compliance; 45s→32s engine revision test; legacy 45s candidate render denied | bulk cognition readiness, provider typed objections/copy engine, autonomous rerun และ blind review |
| Timeline Plan/validator | Implemented slice | provider-neutral model และ validation tests | transitions/captions/loudness/approval gates |
| Direct review render | Implemented preview slice | Timeline Plan → H.264/AAC MP4, still motion, Thai titles, watermark และ loudness normalization | transitions, render receipts in SSOT และ UI progress/cancel |
| Long-form localized revision | Implemented persisted slice | revision/receipt SQLite, dependency hashes, backup/reopen และ 12–13 minute change receipt | approved change application, plan diff, preview/render cache |
| pyCapCut draft | Compatibility slice PASS | synthetic draft เปิดและ export ใน CapCut 9.7 | edit-save-reopen matrix และ feature expansion |
| UI/orchestrator | Runtime bridge foundation | non-blocking submit, events/callback, cancellation และ localized change service tests | persistent jobs, UI-thread dispatcher และ actual UI |
| Windows launch | Implemented baseline | direct/lock requirements และ start/doctor/CLI/test batch files | UI launcher ภายหลัง; installer/release packaging ยังไม่อยู่ใน scope |

`Implemented slice` หมายถึงขอบเขตที่ระบุมีโค้ดและหลักฐาน แต่ไม่เท่ากับ milestone/product พร้อม production

## Kanban snapshot

- Evidence ready (board ยังไม่ formally transitioned จาก Options): `ENG-002` environment doctor; `RQ-002` draft path discovery; compatibility subset ของ `CMP-001`
- Validation evidence ready: `ENG-001`, `ENG-003`, `ENG-005`, `ENG-006`; `ENG-007` ผ่าน focused/full tests และปิด independent review findings แล้ว รอ Product Owner acceptance — acceptance เต็มยังมี config/rights/asset correction/apply-change work
- Options/Ready: AI benchmarks, retention automation, rights/license และ UI work
- Blocked: professional quality evaluation — ยังไม่มี assets งานจริง/annotations ที่ผู้ใช้อนุญาต
- Delivered technical throughput รอบนี้: doctor, bundle/versioned map, evidence extraction, persisted long-form edit scope/receipt, timeline validator, safe draft writer, CapCut open/export proof

## Quality gates ล่าสุด

| Gate | สถานะ | Evidence |
|---|---|---|
| Python 3.14 environment | PASS | `.venv/Scripts/python.exe`; doctor report |
| Foundation automated tests | PASS | `python -m unittest discover -s tests -p 'test_*.py' -q`: 125 tests, 0 failures (4 November 2026) |
| FFmpeg/ffprobe local operation | PASS | synthetic audio/video/image generation, probe และ evidence extraction |
| Asset Map slice | PASS | version invalidation/history, bundle rollback, artifact provenance tests |
| Timeline validation | PASS | multitrack/overlap/path tests |
| Long-form edit scope | PASS | 12:00–13:00 stable segment selection + cross-boundary element test |
| Editorial persistence/recovery | PASS | 11 focused tests: immutable/retry-safe revision/receipt, rollback, dependency query, metadata/payload tamper detection, backup/reopen และ no-op rejection |
| Engine/UI bridge + provider config | PASS | 8 focused tests: non-blocking/events/cancel, grouped config, OpenRouter/local mocked transports, endpoint pinning และ security validation |
| External AI authorization | PASS | remote provider ไม่มี gate/approval ถูกปฏิเสธก่อน transport; allowlist, size ceiling และ append-only revoke ผ่าน tests; assets ทดสอบ 3 รายการมี policy |
| Live AI provider | BOUNDED SMOKE PASS | OpenRouter vision: picture + timestamped video frame PASS; audio 30–45 s Thai speech observation PASS; outputs remain machine-proposed |
| Local Ear / faster-whisper | TECHNICAL PASS / MUSIC QUALITY REJECTED | `small`, CPU int8, PyAV 17.1 compatibility pin; sung input confidence 0.051 rejected below 0.25 gate |
| Shot map / adaptive sampling | PASS / BENCHMARK PENDING | real clip 118.4 s → 24 candidates + 72 frames; second run cache hit; raw boundary scores not calibrated |
| CapCut 9.7 compatibility slice | PASS | create → discover → open → local export; H.264/AAC 3.018 s |
| Real-media private rough cut v3 | DRAFT CREATED | 32 s, 16:9, 1 silent ceremony clip + 5 official-event photos + exactly 1 supplied MP3; copied as `MT_ROAD_REPORT_001_POLICE6_PROFILE_V3` |
| Real-media private preview v1 | STUDIO EVALUATION INVALIDATED | renderer technical QA passed, but editorial choices were Codex-assisted; user reported not wow |
| Cinematic private preview v2 | STUDIO EVALUATION INVALIDATED | renderer stress fixture only; Codex participated in editorial design, violating the autonomy boundary |
| Eye/Ear/Brain semantic evaluation | LIVE PIPELINE PASS / QUALITY NOT VERIFIED | Evidence extraction → provider → validator → SSOT ผ่านกับภาพ เฟรมวิดีโอ และเสียง; ยังไม่มี ground truth/blind review |
| World-Class Grade | NOT RUN | ต้องผ่าน blind review และ production metrics หลายงาน |
| Autonomous Studio Council | LEGACY CANDIDATE REJECTED FOR EVALUATION | run `286f8675-9061-4b64-a60b-faec084b3386` is 45s vs 30–35s and has no candidate-bound compliance proof; render now fails closed |
| Typed Brief + Editorial Findings | PASS (automated slice) | strict brief interpreter, duration/aspect/music/text/scope rules, typed objection policy, engine revision and exhausted-rejection tests |
| Media Readiness | INTENDED VISUAL SET READY / GLOBAL BLOCKED | OpenRouter added observations for 23 missing proxy shots and 4 official photos; intended proxy now 24/24 shots and photos 5/5, while unused assets and full-song coverage remain incomplete |
| Autonomous private preview v7 | PASS | run `42dca66f-0e51-43db-bb95-e33767e3f7c2`; candidate-ready, brief PASS, 35s H.264/AAC 1080p; publication requires the responsible person's decision |
| Autonomous 3-minute V22 | LOCAL EXPORT PASS / EDITORIAL DEFECT FOUND | run `4deaab5f-05f4-4580-81ff-46bb4b63381e`; 180s, 24 distinct stills, 8 video shots, 0.1s source overlap, brief PASS; CapCut 9.8 exported H.264/AAC 1080p to `workspace/road-report-001/exports/road-report-001-studio-v22.mp4`; title เรื่องเพลงผิดเจตนา แก้ engine แล้วแต่ยังไม่ re-run |
| pyCapCut professional finishing | DRAFT OPEN / RESOURCE COMPATIBILITY PARTIAL | OpenRouter finishing manifest → Swipe Left 0.8s, filters 20–30%, slow push-in, text wipe; draft opens and plays in CapCut 9.7, while downloadable filter/text-animation resources need a local-safe fallback profile |

## ความเสี่ยง/การตัดสินใจที่รอ

- มีชุดสื่อจริงสำหรับ private rough cut แล้ว แต่สิทธิ์ภาพราชการ คลิปข่าว และเพลงยังไม่ผ่าน publication gate และยังไม่มี annotations
- test draft ถูกคัดลอกเป็นโฟลเดอร์ใหม่ใน CapCut Drafts; ไม่ได้ลบหรือแก้งานเดิม
- pyCapCut license/distribution policy ยังไม่ปิด
- model/cost budget, provider-side retention/terms และ automatic local evidence cleanup ยังไม่ปิด; data classification/per-asset gate ทำงานแล้ว
- Git repository and remote are configured; local checkpoints are used for development history
- SQLAlchemy/Alembic ยังไม่ติดตั้ง; persistence ปัจจุบันใช้ explicit migration v1, single writer และ rollback journal จนกว่า ADR-003 จะอนุมัติแนวทาง migration/concurrency

## กติกาอัปเดต

แก้สถานะเฉพาะเมื่อมีคำสั่งทดสอบ, artifact หรือผล review อ้างอิงได้ ไม่ใช้เปอร์เซ็นต์หรือจำนวน tests เป็นคำรับรองคุณภาพสร้างสรรค์
