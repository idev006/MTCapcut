# Long-form Editorial Model

วันที่: 2 พฤศจิกายน 2026  
ประเภท: Explanation + domain reference  
สถานะ: domain + persistence/change-planning slice implemented; apply-change/render cache ยังเป็นงานถัดไป

## คำตอบเชิงออกแบบ

Scene ต้องประกอบด้วย Segments แต่ไม่ควรออกแบบให้ทุก Receipt และ Element เป็นลูกที่ฝังอยู่ใน Segment เพราะเพลง, caption, transition และหลักฐานอาจคร่อมหลาย Segment ระบบจึงแยกสามมิติ:

```text
Editorial hierarchy
Project → EditorialRevision → Chapter → Scene → EditSegment

Timeline composition
EditSegment ↔ ElementPlacement → AssetVersion

Evidence and audit
Receipt → Scene / EditSegment / Element / Observation / Decision
```

## นิยาม

- `Chapter`: หน่วยเรื่องขนาดใหญ่และลำดับของ Scenes
- `Scene`: หน่วยความหมาย มี purpose, intent, continuity และ review state; ช่วงเวลาคำนวณจาก Segments
- `EditSegment`: ช่วงตัดต่อที่เปลี่ยนหรืออนุมัติแยกได้ มี stable ID และ timeline range
- `ElementPlacement`: สิ่งที่วางจริง เช่น video, picture, dialogue, music, text, caption, graphic, transition หรือ effect; อาจเชื่อมหลาย Segments
- `EditorialRevision`: snapshot แบบ immutable ที่อ้าง parent revision
- `EditRecipe`: สูตรใช้ซ้ำ เช่น interview-cleanup หรือ report-lower-third
- `Receipt`: หลักฐาน append-only ว่า recipe/engine/model/config/input ใดสร้างหรืออนุมัติ output ใด

Recipe และ Receipt ไม่ใช่สิ่งเดียวกัน: Recipe บอกว่าจะทำอย่างไร ส่วน Receipt บอกว่ารอบนี้ทำอะไรจริงและได้ผลใด

## ตัวอย่างแก้ช่วง 12–13 นาที

```text
Scene scene-04: ผลดำเนินงาน 11:50–13:20
├── seg-041 11:50–12:08 bridge-in
├── seg-042 12:08–12:34 speaker claim
├── seg-043 12:34–12:47 supporting B-roll
├── seg-044 12:47–13:05 outcome
└── seg-045 13:05–13:20 bridge-out

Elements
├── main video คร่อม seg-041..045
├── music bed คร่อม seg-041..045
└── Thai caption คร่อม seg-042..043
```

คำสั่งแก้ 12:00–13:00 ให้ผล:

- editable: `seg-041`–`seg-044`
- context เมื่อขยาย 10 วินาที: รวม `seg-045`
- affected elements: main video, music bed และ caption
- ส่วนอื่นใช้ Asset Intelligence, stable IDs และ revision เดิมซ้ำได้

นี่หมายถึงไม่ต้องวิเคราะห์ assets หรือสร้าง editorial decisions ใหม่ทั้งงาน แต่ final export จาก CapCut อาจยัง render เต็มจนกว่า Incremental Render Engine จะผ่าน compatibility/QC

## Invariants

1. ID ถาวร; timecode ไม่ใช่ identity
2. Scene time derive จาก Segments ไม่บันทึกค่าซ้ำเป็นเจ้าของหลายจุด
3. Segment อยู่ใน Scene เดียวและ Scene อยู่ใน Chapter เดียวต่อ revision
4. Element คร่อมหลาย Segment ได้ แต่ต้อง overlap และมี coverage links
5. Media element ต้อง pin `AssetVersion` และ source range
6. ข้อความเชิงข้อเท็จจริงต้องอ้าง approved Claim หรือ user-confirmed fact
7. Receipt เป็น append-only และผูก exact revision/model/config/input/output hashes
8. เปลี่ยน asset hash แล้ว invalidate เฉพาะ dependencies ที่เกี่ยวข้อง
9. pyCapCut IDs เป็น adapter detail และต้องไม่เป็น domain identity
10. draft รุ่นใหม่ห้าม overwrite draft เดิม

## สิ่งที่ implement แล้ว

- frozen domain models ใน `mtcapcut/editorial.py`
- hierarchy/orphan/time/coverage validation
- Scene range ที่ derive จาก Segments
- timecode-to-stable-ID edit scope พร้อม context window
- cross-boundary element impact
- mapping ElementPlacement ไป provider-neutral TimelinePlan โดยรักษา element/edit-segment IDs
- SQLite persistence สำหรับ immutable revision, append-only receipt, canonical hash และ parent integrity
- asset-version dependency query, backup/reopen และ fail-closed tamper detection
- application service ที่บันทึกคำขอแก้เฉพาะช่วงพร้อม actor/reason/scope โดยไม่ mutate timeline

## งานถัดไป

- persistence ของ `EditRecipe` และ migration ADR สำหรับ SQLAlchemy/Alembic/concurrency
- plan diff และ stale dependency propagation
- preview/render cache key จาก element versions + parameters + engine/config + delivery profile
- application service สำหรับนำ change request ที่อนุมัติแล้วไปสร้าง revision ใหม่
- partial FFmpeg render/concat พร้อม codec, GOP, audio continuity และ boundary QC
- adapter receipt ที่ map domain IDs ไป pyCapCut IDs โดยไม่รั่วเข้า domain
