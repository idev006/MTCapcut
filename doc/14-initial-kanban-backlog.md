# Initial Kanban Backlog

วันที่สร้าง: 2 พฤศจิกายน 2026  
สถานะ: Options — ต้องผ่าน Replenishment และ Pull Criteria ก่อนเข้า Ready  
Execution SSOT: เอกสารนี้; `08-foundation-implementation-plan.md` เป็น technical reference ไม่ใช่คิวงาน

## Studio pipeline cards — 4 พฤศจิกายน 2026

รายละเอียด diagnosis, DoD และความเสี่ยงอยู่ใน [แผนหกเฟส V22](./37-v22-diagnosis-design-and-delivery-plan.md) ผู้ใช้ยืนยันว่า **ยังไม่ทำปลั๊กอิน**

| ID | Priority / board state | งานและ acceptance |
|---|---|---|
| STU-101 | P0 / Validate | แยก explicit on-screen copy ออกจาก production instructions; regression test ผ่าน |
| STU-102 | P0 / Validate | ตรวจภาพนิ่งซ้ำและช่วงวิดีโอซ้ำหลัง revision ทุกครั้ง; report ผูก candidate |
| STU-103 | P0 / Validate | payload ceiling ตรวจคำขอจริง, artifact พร้อมก่อน ledger ready, manifest ไม่ค้างเมื่อสร้าง draft ล้ม |
| STU-104 | P1 / Validate | accepted specialist handoff ถึง Lead Editor; evidence visual ต้องเป็น vision/OCR |
| STU-105 | P1 / Ready | usage/cost ledger ต่อ stage, scoped snapshot, idempotent checkpoint/retry |
| STU-106 | P1 / Ready | source visual coverage QC และ fact review ที่แยก unknown/observed |
| STU-107 | P2 / Options | chapter/sequence bounded planning และ localized render ของ 20+ นาที |
| STU-108 | P2 / Options | blind human review หลาย brief และ finishing A/B benchmark |

สถานะ Validate หมายถึง implementation/focused tests ผ่าน แต่ยังไม่ปิด card จน acceptance ตามงานจริงครบ

## Take-review cards — 6 พฤศจิกายน 2026

อ้างอิง [AutoVideoMaker research transfer](./38-autovideomaker-transfer-study.md); PR #1 เป็นจุดเริ่มการศึกษาและโค้ด review-only โดยพัฒนาต่อใน `main`

| ID | Priority / board state | งานและ acceptance |
|---|---|---|
| TAK-101 | P1 / Validate | faster-whisper เก็บ word timestamps/probability เป็น observations ของ asset version ปัจจุบัน; pure take rules คืน timecode/evidence IDs; 135 tests ผ่าน |
| TAK-102 | P1 / Ready | เพิ่ม review/approval + receipt ก่อน apply cut; ปฏิเสธการตัดเมื่อ evidence เปลี่ยน version |
| TAK-103 | P1 / Ready | ตรวจ word gap เทียบ acoustic silence, ambience/music และ multi-speaker; ทดสอบ false positives |
| TAK-104 | P2 / Options | ชุดคลิปพูดไทยมี label; วัด false-removal seconds, recall, processing time และ cost |

## Development snapshot — 2 พฤศจิกายน 2026

foundation slice เดินถึง validation แล้ว: `ENG-002` doctor ผ่านบนเครื่องจริง; `ENG-005/006` มี bundle ingest, immutable AssetVersion, current/history queries และ artifact provenance; `ENG-007` มี persisted revision/receipt และ localized change planning; `CMP-001` subset create/open/export ผ่าน CapCut 9.7.0.4153 ด้วย fixture สังเคราะห์ รายละเอียดอยู่ใน [Development Status](./17-development-status.md) และ [Compatibility Report](./21-capcut-compatibility-report.md) Acceptance เต็มของ config, rights, correction workflow, automatic edit application และ compatibility matrix ยังไม่ครบ จึงไม่เหมารวม milestone ว่า Done

M2 evidence slice เพิ่ม ShotCandidateEngine/AdaptiveFrameSamplingEngine แล้ว: live clip 118.4 วินาทีได้ 24 candidates และ 72 frame artifacts พร้อม transaction/cache; `EXP-003` ยังอยู่ระหว่างดำเนินการเพราะยังไม่มี annotated benchmark/F1 threshold จึงยังไม่ย้าย Done

`ADR-002`/`DOC-002` มี implementation evidence slice แล้ว: central remote switch, append-only per-asset classification/approval, payload ceiling และ fail-before-transport tests อยู่ใน [ADR-002](./28-adr-002-ai-data-provider-policy.md) และ [Threat Model](./29-threat-model-retention-schedule.md) งาน provider-side terms, automatic cleanup และ professional sign-off ยังไม่ Done

## Options candidates

| ID | Card | Owner/Approver | Depends on | Trace | Acceptance evidence |
|---|---|---|---|---|---|
| DOC-001 | StudioRoleCatalog SSOT และ stable role IDs | Architect / Product Owner | none | ARCH, DOC | roles/services/engines/adapters แยกชัดและ docs อ้าง catalog เดียว |
| ADR-001 | project skeleton/dependency strategy สำหรับ Python 3.14 | Tech Lead / Architect | none | LOC-001, RISK-MODEL | alternatives, compatibility probes, ADR approval |
| ENG-001 | Typed central TOML configuration | Config Steward / Tech Lead | ADR-001 | SRC-013, SRC-014, ARCH | precedence/validation tests ผ่าน ไม่มี secret |
| ENG-002 | Environment doctor | Platform Engineer / Tech Lead | ENG-001 | LOC-001..003, TEST | reproducible report กับเครื่องจริง |
| ENG-003 | Domain contracts: MediaAsset/EvidenceRef/TimelinePlan | Architect / Tech Lead | DOC-001, ADR-001 | SRC-003, SRC-028, ARCH | invariants และ tests ผ่าน |
| RQ-001 | ตรวจ license pyCapCut และ distribution implications | Rights Owner / Product Owner | none | LOC-001, RISK-LICENSE | authoritative evidence หรือ legal escalation |
| RQ-002 | หา CapCut Drafts path และ compatibility policy | Integration Engineer / Tech Lead | ENG-002 | LOC-003, RISK-COMPAT | safe discovery/proof plan |
| CMP-001 | pyCapCut 0.0.4 กับ CapCut 9.7.0.4153 | Integration Engineer / Technical QC | RQ-002, ENG-003 | SRC-001, LOC-003, TEST | open/save/reopen/export evidence per feature |
| EXP-001 | benchmark Thai ASR candidates | AI Engineer / Fact Editor | ADR-002, DOC-002 | SRC-008, TEST | dataset rights, CER/WER/entity/timestamp/cost report |
| EXP-002 | benchmark Thai OCR candidates | AI Engineer / Fact Editor | ADR-002, DOC-002 | SRC-030, TEST | OCR accuracy/polygon/runtime report |
| EXP-003 | shot boundary candidates | AI Engineer / Lead Editor | ENG-003 | SRC-005..007, TEST | F1/tolerance/failure report |
| ADR-002 | local vs external AI provider data policy | Security/AI Lead / Product Owner | DOC-002 | [ADR](./28-adr-002-ai-data-provider-policy.md), RISK-PRIVACY | enforcement slice ผ่าน; provider terms/cost approval ยังรอ |
| DOC-002 | threat model and retention schedule | Security Owner / Product Owner | none | [Threat Model](./29-threat-model-retention-schedule.md), RISK-SECURITY | trust boundaries/retention documented; cleanup automation/sign-off ยังรอ |
| ENG-004 | Job/Artifact/Decision ledger baseline | Platform Engineer / Tech Lead | ENG-001, ENG-003 | SRC-033, SRC-034, ARCH | schema/tests/correlation IDs/provenance graph |
| ENG-005 | ProjectAssetBundle และ AssetIntakeEngine สำหรับ clips/mp3/pictures/text | Media Engineer / Fact Editor | ENG-001, ENG-003 | SRC-003, ARCH, TEST | role/hash/rights/integrity report; ambiguous text role ส่ง human review |
| ADR-003 | ตัดสิน storage/schema/revision policy ของ Asset Understanding Map | Architect / Tech Lead | ENG-003, ENG-004 | ARCH, TEST | SQLite vs alternatives, SQLAlchemy ORM/Alembic migration compatibility, concurrent write test plan และ accepted ADR |
| ENG-006 | Asset Understanding Map repository และ queries | Platform Engineer / Fact Editor | ADR-003, ENG-005 | ARCH, TEST | transactional ingest, source/time queries, revisions, corrections และ invalidation tests |
| ENG-007 | Persisted Localized Change Request | Platform Engineer / Lead Editor | ENG-003, ENG-006 | [Plan](./24-eng-007-persisted-localized-change-plan.md), TEST | immutable revision/receipt, reopen/backup, dependency query และ 12–13 minute scope tests ผ่าน; automatic edit อยู่นอกขอบเขต |
| ENG-008 | Windows batch launch + non-blocking engine/UI bridge + AI provider baseline | Platform/AI Engineer / Tech Lead | ENG-001, ADR-002 | [Architecture](./25-deployment-ui-bridge-ai-provider-architecture.md), TEST | start/doctor/CLI/test batch files, grouped config, event/cancel contracts และ mocked OpenRouter/local provider tests ผ่าน |
| EXP-004 | พิสูจน์ตา หู สมองแบบ end-to-end กับสื่อที่มี annotation | AI Engineer / Lead Editor | ENG-006, EXP-001, EXP-002, EXP-003 | SRC-028..031, TEST | ทุก observation มี asset/time; claims มี evidence; Timeline Plan ไม่กล่าวสถานะเกิน facts |

## Pull order proposal

1. `RQ-001`, `ADR-001`, `DOC-001`
2. `ENG-001`, `ENG-002`, `ENG-003`
3. `RQ-002`, `DOC-002`, `ADR-002`
4. `CMP-001`, `ENG-004`
5. `ENG-005`, `ADR-003`, `ENG-006`, `EXP-001`–`EXP-003` ตาม WIP/capacity แล้วจึง `EXP-004`
6. `ENG-007` evidence slice ผ่าน Validate และปิด independent review findings แล้ว; รอ Product Owner ตรวจรับก่อนย้าย Done
7. `ENG-008` baseline ผ่าน automated validation; live provider/UI integration รอ config, credentials/server และ UI card

เหตุผล: ปิด license/environment/domain risks ก่อนสร้าง integration และยังไม่เลือก AI models ก่อนมี benchmark

ทุก item ใช้ Class `Standard` ใน Options; เปลี่ยนเป็น Fixed Date/Expedite ได้เฉพาะ Replenishment เมื่อมีหลักฐานครบตาม policy

## Mapping จากแผนเดิม

| Implementation plan | Kanban card |
|---|---|
| Task 1 | ADR-001, ENG-001 |
| Task 2 | ENG-002 |
| Task 3 | ENG-003 |
| Task 4 | เพิ่ม ENG card หลัง ENG-003 ผ่าน Replenishment |
| Task 5 | เพิ่ม ENG card หลัง domain contracts ผ่าน |
| Task 6 | เพิ่ม ENG card โดยขึ้นกับ CMP-001 scope |
| Task 7 | CMP-001 |
| Task 8 | EXP-001, EXP-002, EXP-003 |

## Blocked/unknown

- ไม่มี historical flow data จึงใช้ provisional SLE
- ยังไม่มี media fixtures ที่ยืนยันสิทธิ
- มี test draft ชื่อเฉพาะและ sandbox fixture แล้ว; ยังต้องกำหนด lifecycle/cleanup policy ก่อนทำงานซ้ำใน production
- ยังไม่มีผู้มีอำนาจด้าน legal/rights ระบุชื่อ
- ยังไม่ได้เลือก telemetry backend หรือ AI provider

## Replenishment checklist

ก่อนย้าย card เข้า Ready ต้องเพิ่ม owner, approver, dependencies, evidence links, acceptance thresholds และ size ที่ review ได้หนึ่งรอบตาม [Agile Kanban Operating Model](./10-agile-kanban-operating-model.md)

