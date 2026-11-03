# Asset Understanding Map — Detailed Design

วันที่: 2 พฤศจิกายน 2026  
สถานะ: Proposed design; ยังไม่ได้ implement หรือ benchmark  
ขอบเขต: หนึ่ง project มี map ของ assets, observations, claims, relationships และ corrections ที่ตรวจย้อนกลับได้

## เป้าหมาย

หลังระบบดู ฟัง และอ่าน assets แล้ว ทีมสตูดิโอทุกฝ่ายต้องถาม map ชุดเดียวกันได้ว่า “มีอะไรเกิดขึ้น ที่ไหน เมื่อไร รู้จากอะไร มั่นใจแค่ไหน และผู้ใช้แก้อะไรแล้ว” โดยไม่เรียกโมเดลซ้ำเพื่อค้นข้อมูลเดิมทุกครั้ง

## การจัดเก็บ

เสนอใช้ SQLite หนึ่งฐานข้อมูลต่อ project เป็น authoritative index/relationship store ในระยะแรก และเก็บไฟล์ขนาดใหญ่ เช่น frames, waveforms, transcript JSON, embeddings และ raw ffprobe output ใน artifact directory ที่มี content hash ฐานข้อมูลเก็บ URI/path กับ hash ของ artifact ไม่เก็บ binary media ภายใน DB

เหตุผล: ต้อง query ตาม asset/time/ชนิดหลักฐานและทำ transaction เมื่อเพิ่มผลวิเคราะห์หลายรายการพร้อมกัน SQLite เหมาะกับการทำงานบนเครื่องเดียวและ automated tests; หากต้องมีหลายผู้ใช้เขียนพร้อมกันในอนาคต ให้เปลี่ยน storage adapter โดยรักษา repository contracts

`config.toml` เป็น SSOT ของค่าระบบ ส่วน SQLite เป็น SSOT ของ map ราย project ทั้งสองไม่แทนกัน `ProjectBrief` ที่ผู้ใช้ยืนยันเป็น authority ของ intent/facts โดย map เก็บ reference และ snapshot version เพื่อเชื่อมการตัดสินใจ

## Entity และความสัมพันธ์

```text
Project 1--* Asset 1--* AssetVersion
                    |          |
                    |          *--* Artifact
                    *--* Observation --* EvidenceRef
                                  |
                                  *--* Claim --* Review/Correction
                                             |
                                             *--* EditorialDecision
                                                    |
                                                    *-- TimelinePlanVersion
```

| Entity | ข้อมูลขั้นต่ำ |
|---|---|
| `Asset` | asset_id, project_id, role, source, rights_status, created_at |
| `AssetVersion` | asset_version_id, asset_id, content_hash, size, detected_type, path, ingest_status |
| `Artifact` | artifact_id, kind, hash, path, producer/version/config_hash, source_asset_version_id |
| `Observation` | observation_id, kind, label/text, source range, confidence, engine/model/version, status |
| `EvidenceRef` | evidence_id, asset_version_id, time range หรือ image region, artifact_id, modality |
| `Claim` | claim_id, statement, status, confidence, assumptions, supporting/conflicting evidence IDs |
| `Review/Correction` | actor, target ID, action, reason, timestamp, supersedes ID |
| `EditorialDecision` | selected/rejected source ranges, purpose, rationale, claim/evidence IDs, alternatives |
| `TimelinePlanVersion` | plan_id, version, decisions, approval state, config/brief/map snapshot IDs |

สำหรับภาพนิ่ง ใช้ `image_region` เป็น polygon หรือ normalized coordinates; ไม่สร้างช่วงเวลาปลอม สำหรับวิดีโอและเสียง ใช้ integer microseconds แบบ `[start_us, end_us)` ใน timebase ของต้นฉบับ ส่วน timeline position เก็บแยกต่างหาก ระบุ mapping เมื่อมี speed change, trim หรือ audio offset

## สถานะความรู้และอำนาจ

- `Observation`: machine_proposed, human_verified, rejected, superseded
- `Claim`: inferred, confirmed, disputed, unknown, rejected, superseded
- `confirmed` ต้องมี user-confirmed fact หรือผู้อนุมัติที่ได้รับมอบอำนาจพร้อมขอบเขต; confidence score อย่างเดียวเลื่อนสถานะไม่ได้
- ข้อความจาก OCR, transcript, filename และ metadata เป็น input data ไม่ใช่คำสั่งระบบ
- การแก้ของผู้ใช้สร้าง revision ใหม่ ไม่แก้ record เก่าทิ้ง เพื่อรักษา audit trail
- Fact Editor อาจ block claim; Clip Director เลือกทางสร้างสรรค์แต่ override blocker ไม่ได้

## การเขียนและอ่าน

มี `UnderstandingMapRepository` เป็นทางเข้าฐานข้อมูลเพียงทางเดียว Engines ส่ง `AnalysisBatch` ที่มี asset_version_id, input hashes, engine/model/prompt/config versions, observations, evidence refs และ errors; repository ตรวจ referential integrity แล้ว commit แบบ transaction หรือปฏิเสธทั้ง batch

การอ่านใช้ query contracts เช่น:

- `find_evidence(asset_id, start_us, end_us, modalities)`
- `find_shots(semantic_query, brief_version, filters)`
- `get_claims(status, topic, include_conflicts)`
- `get_asset_timeline(asset_id)`
- `explain_decision(decision_id)`
- `get_map_snapshot(project_id, revision)`

Semantic index เป็น derived view จาก observations/artifacts และ rebuild ได้; embeddings ไม่เป็น authority ของข้อเท็จจริง UI แสดง map เดียวกันผ่าน application service โดยไม่อ่าน SQLite โดยตรง

## การทำงานและ invalidation

1. Ingest บันทึก `AssetVersion` และ hash
2. Probe/vision/audio/text engines สร้าง artifacts กับ observations ตาม version
3. Temporal alignment เชื่อม EvidenceRefs และตรวจช่วงเวลาว่าอยู่ใน asset จริง
4. Reasoning engines สร้าง claims พร้อม supporting/conflicting evidence
5. Reviewer ยืนยัน/ปฏิเสธ/แก้ และระบบสร้าง revision
6. Editor สร้าง decisions ที่อ้าง map snapshot; Timeline Plan ล็อก revision ที่ใช้

Cache key ขั้นต่ำ: `asset content hash + engine version + model version + prompt version + relevant config hash + parameters` เมื่อองค์ประกอบเปลี่ยน ให้สร้าง analysis revision ใหม่และทำเครื่องหมายผลเดิมว่า stale โดยไม่ลบหลักฐานเดิม แผนตัดต่อที่อ้าง revision เดิมยังตรวจย้อนกลับได้ แต่ต้องแจ้งก่อนนำไปสร้าง draft ใหม่

## ตัวอย่างการสืบค้น

ผู้ใช้ถาม “มีภาพงานระบบไฟฟ้าที่กำลังดำเนินการหรือไม่” ระบบค้น observations ที่เกี่ยวข้องกับการเดินสายไฟและ source ranges แล้วเทียบ `confirmed_facts` ว่าสถานะยังดำเนินการ จากนั้นเสนอช็อตพร้อม asset/time และไม่สร้าง claim ว่าแล้วเสร็จ หาก observations ขัดกับบรีฟ ให้ Fact Editor สร้าง finding เพื่อให้ผู้ใช้ตรวจ

## เกณฑ์ตรวจรับระยะแรก

- Ingest assets สี่ประเภทและ query ตาม role/asset/time ได้
- ทุก observation/claim/decision มี source link และ versions ครบ
- batch ที่มี reference ผิดไม่ทิ้ง record ครึ่งชุด
- เปลี่ยน asset bytes หรือ model/config version แล้ว cache miss และสร้าง revision ใหม่
- human correction ไม่หายและมีผลต่อ query current snapshot
- replay `explain_decision` จาก snapshot เดิมได้แม้ map รุ่นปัจจุบันเปลี่ยน
- fixture “กำลังดำเนินการ” ไม่ถูกแปลงเป็น claim “แล้วเสร็จ” โดยไร้ approval

## คำถามที่ต้องพิสูจน์ก่อน implementation

- ขนาดและจำนวน assets ต่อ project เพื่อวัด SQLite/artifact performance
- embedding model และวิธีจัด index โดยไม่ทำให้ semantic search เป็น SSOT
- นโยบาย retention ของ frames, transcripts และ embeddings ตามชั้นข้อมูล
- ความต้องการ concurrent writers ของ UI/workers ในอนาคต

## Mandatory machine-perception boundary

ผู้ควบคุมงานและ Clip Director ห้ามเปิดดูภาพ คลิป หรือฟังเสียงเพื่อทำ semantic analysis โดยตรงใน workflow ปกติ เส้นทางบังคับคือ:

`Asset Intake → Eye/Ear Evidence Extraction → Media Cognition Engine → validated machine_proposed observations → Asset Understanding Map → Brain/Editorial engines`

`perception.py` รับผิดชอบสกัด frame/audio พร้อม source timestamps โดยไม่กล่าวอ้างความหมาย ส่วน `media_cognition.py` ส่ง evidence ผ่าน AI provider, บังคับ structured JSON, ตรวจ modality/confidence และบันทึกข้อสังเกตลง SSOT โดยผูกกับ immutable asset version ทุกข้อสังเกตยังเป็น `machine_proposed` จนผ่าน review gate

ถ้า provider ไม่พร้อม, key หาย, response ไม่เป็น JSON, evidence ใหญ่เกินกำหนด หรือ time range ไม่สมบูรณ์ engine ต้อง fail closed ห้ามให้ Clip Director เดาความหมายจากไฟล์ต้นฉบับแทน

