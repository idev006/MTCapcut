# Test and Validation Strategy

## เป้าหมาย

พิสูจน์ทั้ง correctness ทางวิศวกรรมและคุณภาพเชิงสร้างสรรค์ โดยไม่ใช้คำว่า world-class เป็นเกณฑ์ที่ตรวจไม่ได้

## Test pyramid

### Unit tests

- config precedence และ validation
- timebase/range conversion
- domain model invariants
- timeline overlap/gap rules
- recommendation/evidence schema
- deterministic scoring functions
- asset role classification, content hash invalidation และ authority ของ text file
- pyCapCut mapping โดยใช้ fake writer

### Contract tests

- ทุก engine รับ/คืน schema version ที่รองรับ
- FFmpeg adapter คืน structured result/error
- AI provider adapter normalize confidence, usage และ provenance
- perception/reasoning contracts แยก `Observation`, `Claim` และ `EditDecision` พร้อม EvidenceRef
- pyCapCut adapter map track/segment โดยไม่รั่ว type ของไลบรารีออกสู่ domain

### Integration tests

- ffprobe กับ media fixtures จริง
- FFmpeg thumbnail, proxy, audio extraction และ loudness analysis
- Timeline Plan ไป draft folder ใน temporary test location
- artifact hashing, cache invalidation และ resume

### Compatibility tests

ต้องรันแยกและมีมนุษย์ตรวจในระยะแรก:

1. สร้าง draft ชื่อเฉพาะใน test folder
2. เปิดด้วย CapCut `9.7.0.4153`
3. ตรวจ video, image, audio, Thai text, transition และ keyframe
4. บันทึก ปิด และเปิดใหม่
5. export ด้วยมือ
6. ใช้ ffprobe ตรวจผลลัพธ์และเทียบ duration/streams
7. เก็บ screenshot, draft artifact, export และ report

### Editorial persistence and recovery tests

- ปิดและเปิด SQLite ใหม่แล้ว `EditorialRevision` ต้องเท่ากับต้นฉบับทุก field
- revision/receipt ID เดิมกับ payload เดิมต้อง idempotent; payload ต่างต้อง reject โดยไม่ overwrite
- parent revision ที่ไม่มีอยู่, revision ที่ผิด invariants และช่วงแก้ที่ไม่ถูกต้องต้อง rollback
- canonical payload hash ไม่ตรงต้อง fail closed
- backup ผ่าน SQLite backup API ต้องเปิดและเลือก edit scope เดิมได้
- dependency query ต้องตอบ revision ที่อ้าง `AssetVersion` ได้
- คำขอแก้ 12:00–13:00 ต้องเก็บ requested/context ranges, stable segment IDs, affected elements, actor และ reason ใน append-only receipt
- ค่าเริ่มต้นใช้ rollback journal และ single writer; WAL/multi-process เป็น compatibility gate แยก

### Creative evaluation

- blind A/B review เทียบ baseline ที่มนุษย์ตัด
- intent alignment
- story clarity
- factual accuracy
- emotional impact
- pacing
- audio-visual harmony
- brand consistency
- จำนวนและความรุนแรงของการแก้โดยมนุษย์
- เวลารวมตั้งแต่ ingest ถึง approved draft

## Golden fixtures

ชุด fixture ขั้นต่ำต้องมี:

- วิดีโอ landscape/portrait
- frame rate คงที่และแปรผัน
- คลิปมี/ไม่มีเสียง
- ภาษาไทยพร้อมชื่อเฉพาะและตัวเลข
- ภาพนิ่งหลายอัตราส่วน
- ไฟล์เสียหรือ stream ไม่ครบ
- ช็อตที่คล้ายกันแต่บริบทต่างกัน
- brief ที่ระบุสถานะ “กำลังดำเนินการ” เพื่อทดสอบ factual safeguard
- MP3 เสียงบรรยาย/เพลงและ text files หลายบทบาทที่มีข้อความขัดกัน

fixture ต้องเป็นสื่อที่มีสิทธิใช้งานและไม่เปิดเผยข้อมูลส่วนบุคคล

## Quality gates

| Gate | ผ่านเมื่อ |
|---|---|
| Environment | binaries และ versions ตรง policy |
| Media integrity | probe สำเร็จและ normalized schema valid |
| Asset intake | bundle มี role/hash/source/rights และ ambiguity ส่ง human review |
| Perception | observations ชี้กลับ asset/time และผ่าน benchmark ภาพ/เสียง/ภาษาไทย |
| Reasoning | claims แยก facts/inference/unknown และไม่มี unsupported critical claim |
| Evidence | factual claim ทุกข้อมี user source หรือ EvidenceRef |
| Editorial | Timeline Plan valid ไม่มี illegal overlap/range |
| Editorial persistence | revision/receipt immutable, hash valid, reopen/backup ได้ และ localized scope คงเดิม |
| Trust | ไม่มี unresolved critical fact/ethics finding |
| Draft | pyCapCut สร้าง artifact ครบโดยไม่แตะงานจริง |
| Compatibility | CapCut เปิด บันทึก เปิดใหม่ และ export ได้ |
| Technical QC | output ตรง delivery profile |
| Creative acceptance | ผู้ใช้อนุมัติและ metrics ถึงเกณฑ์ที่กำหนด |

## เกณฑ์ที่ยังต้องกำหนดจากข้อมูลจริง

- timing tolerance ระหว่าง Timeline Plan กับ export
- loudness profile ตามช่องทางส่งมอบ
- คะแนน blind review ขั้นต่ำ
- เป้าหมายลดเวลาตัดต่อ
- จำนวน critical factual errors ที่ยอมรับได้ — ข้อเสนอเริ่มต้นคือศูนย์

## Safety

- tests ห้ามเขียนทับ draft เดิม
- integration test ใช้ temporary directories
- fixture และ artifacts ต้องระบุ retention policy
- command logs ต้อง redact secret และข้อมูลส่วนบุคคล
- destructive cleanup ต้องตรวจ resolved path ว่าอยู่ใต้ test workspace เท่านั้น

