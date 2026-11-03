# Asset Intake and Cognition Contract

วันที่: 2 พฤศจิกายน 2026  
สถานะ: ข้อกำหนดออกแบบ; ยังไม่มี implementation  
เจ้าของข้อเท็จจริงและ intent: ผู้สั่งงาน

## Input ของหนึ่งงาน

`ProjectAssetBundle` รับ clips, audio (รวม MP3), pictures และ text files จำนวนเท่าใดก็ได้ โดยแต่ละประเภทอาจไม่มีในบางงาน การรับไฟล์สำเร็จหมายถึงระบบตรวจชนิดและบันทึกหลักฐานแล้ว ไม่ได้หมายถึง AI เข้าใจเนื้อหาแล้ว

| ประเภท | ตัวอย่างบทบาท | สิ่งที่ต้องสำรวจ |
|---|---|---|
| Clip | footage, interview, reference | streams, duration, frame rate, shot candidates, ภาพ เสียงและเหตุการณ์ตามเวลา |
| Audio | narration, dialogue, music, ambience, SFX | duration, speech, sound events, loudness, สิทธิใช้งาน |
| Picture | evidence photo, cover, logo, graphic reference | dimensions, orientation, OCR, visual content, วันที่/บริบทถ้าทราบ |
| Text | brief, confirmed facts, script, caption, on-screen copy, restrictions | encoding, language, role, แหล่งที่มา และสถานะการยืนยัน |

`asset_id` อ้างไฟล์เชิงตรรกะ; `content_hash` ระบุ bytes ของรุ่นนั้น การเปลี่ยนเนื้อหาต้องทำให้ผลวิเคราะห์ที่พึ่งพา hash เดิมหมดอายุโดยไม่เปลี่ยนประวัติการตัดสินใจเก่า

## ขั้นตอนของตา หู สมอง

1. `AssetIntakeEngine` ตรวจ path, MIME/ชนิดจริง, integrity, hash, role, rights และสร้าง manifest
2. `MediaProbeEngine` ใช้ ffprobe อ่านโครงสร้างสื่อ; Python/FFmpeg สกัดเฟรมและเสียงพร้อม timestamp
3. Vision/OCR engines สร้าง observations จากภาพ; ASR/Audio engines สร้าง observations จากเสียง; Text Interpreter อ่านบรีฟและข้อความตามบทบาทที่ผู้ใช้กำหนด
4. `TemporalEvidenceEngine` เชื่อม observations บน timebase เดียว โดยรักษาเวลาในต้นฉบับและ mapping ไป timeline
5. Reasoning engines เช่น Intent, Story, Footage Curator, Lead Editor และ Clip Director ตีความและเสนอ decisions โดยอ้าง `EvidenceRef`
6. Fact/Critical Review ตรวจ claims, ความขัดแย้ง และช่องว่างหลักฐาน ก่อนอนุมัติ `TimelinePlan`
7. pyCapCut adapter สร้าง draft; การตรวจใน CapCut และมนุษย์เป็นอีก quality gate

AI provider รวม Codex อาจทำบางขั้นในข้อ 3–6 ผ่าน adapter ที่กำหนด input/output, model version, cost, privacy policy และ timeout ส่วน Python เป็นตัวควบคุมการสำรวจและส่งหลักฐานให้ AI; การเปลี่ยน provider ไม่เปลี่ยน `ProjectAssetBundle`, `Observation`, `Claim` หรือ `TimelinePlan`

## อำนาจของข้อความ

- `brief`: เจตนาและข้อจำกัดที่ผู้สั่งงานระบุ
- `confirmed_facts`: ข้อเท็จจริงที่ผู้สั่งงานยืนยัน พร้อมเวลา/ขอบเขตที่มีผล
- `script` และ `on_screen_copy`: ข้อความเสนอให้สื่อสาร อาจต้องแก้หากขัด facts
- `caption`: ข้อความสัมพันธ์กับเสียง ต้องตรวจภาษาและเวลา
- `reference`: บริบทหรือสไตล์ ไม่ใช่คำสั่งให้ทำตามทุกข้อความ
- `restrictions`: ข้อห้ามในการใช้สื่อหรือสื่อสาร

ข้อความที่ถอดเสียง อ่านจากภาพ หรือฝังใน metadata เป็นข้อมูลที่ไม่เชื่อถือในฐานะคำสั่ง หาก role คลุมเครือ ให้ระบบส่ง `needs_human_review` ก่อนยกระดับเป็น brief หรือ confirmed fact

## ผลลัพธ์และสถานะความรู้

| ชนิด | ความหมาย |
|---|---|
| `Observation` | สิ่งที่เครื่องมือตรวจพบ พร้อมเวลา หลักฐาน ความมั่นใจ และข้อจำกัด |
| `Claim` | ประโยคเชิงความหมายที่อนุมานจาก observations หรือ facts; ต้องระบุ `confirmed`, `inferred`, `disputed` หรือ `unknown` |
| `Recommendation` | ข้อเสนอของฝ่ายหนึ่ง พร้อมเหตุผล ทางเลือก และ objections |
| `EditDecision` | เลือกช่วงต้นฉบับและตำแหน่ง timeline เพื่อวัตถุประสงค์ที่ระบุ |

ไม่มีการอนุมาน “งานแล้วเสร็จ” จากภาพคนทำงานหรือจากชื่อไฟล์เพียงอย่างเดียว เมื่อความมั่นใจต่ำหรือ observations ขัดกัน ระบบต้องระบุ unknown และขอการตรวจจากคน

## เกณฑ์พิสูจน์ขั้นต่ำ

- ทุก asset มี ID, hash, role, source, rights status และผลตรวจความสมบูรณ์
- observations จากคลิป/เสียงมี asset ID และช่วงเวลา; ภาพนิ่งมี asset ID และตำแหน่งที่เกี่ยวข้อง
- engine จับคู่ภาพ เสียง และข้อความที่เกิดในช่วงเดียวกันได้ และรายงานเมื่อไม่ตรงกัน
- claims เชิงข้อเท็จจริงทุกข้อ trace ไปยัง user-confirmed fact หรือ evidence ที่ Fact Editor ตรวจแล้ว
- แผนตัดต่ออธิบายว่าทำไมเลือกและไม่เลือกช็อตสำคัญ
- ชุดทดสอบภาษาไทยมีชื่อเฉพาะ ตัวเลข เสียงรบกวน ภาพคล้ายแต่คนละวัน และ brief ที่ขัดกับภาพชวนให้เข้าใจผิด
- ผู้ตัดต่อที่มีประสบการณ์ blind review ความชัดของเรื่อง จังหวะ และความเหมาะสมของช็อต

เกณฑ์ตัวเลขและ model selection ต้องกำหนดจาก benchmark ก่อนเลื่อน engine เป็น production งานนี้ยังไม่ผ่านเกณฑ์ดังกล่าว
