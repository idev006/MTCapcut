# V22 pipeline diagnosis, design, and delivery plan

วันที่: 4 พฤศจิกายน 2026

ขอบเขต: engine, OpenRouter council, asset evidence, long-form edit, pyCapCut/CapCut 9.8

สถานะ: แก้ P0 บางส่วนแล้ว; ยังไม่ผ่านเกณฑ์คุณภาพสร้างสรรค์ระดับ world-class

ปลั๊กอิน: ยังไม่ทำ ตามคำตอบของผู้ใช้

เอกสารนี้แยก **ข้อเท็จจริงที่ตรวจแล้ว** ออกจาก **สมมติฐานที่ต้องพิสูจน์** การตัดสินใจเชิงสร้างสรรค์ของคลิปทดสอบต้องมาจาก engines/OpenRouter ตามขอบเขต authorship ใน [doc/30](./30-studio-autonomy-boundary.md); การแก้โค้ดด้านล่างเป็นกติกา/การส่งต่องาน/QA ไม่ใช่การเลือกช็อตแทน AI

## เฟส 1 — วินิจฉัยจากหลักฐาน

### จุดแข็งที่ตรวจแล้ว

| ประเด็น | หลักฐาน |
|---|---|
| Asset Understanding Map และ provenance | `mtcapcut/map.py` เก็บ asset, observation, studio run และ candidate; `mtcapcut/studio_snapshot.py` สร้าง snapshot ที่มี hash |
| มีผู้เชี่ยวชาญหลายบทบาทและการกำกับ | `mtcapcut/studio_roles.py` เรียกคำแนะนำแต่ละบทบาท, Clip Director สังเคราะห์, Lead Editor สร้าง timeline |
| Fail closed สำหรับ brief และ media source | `mtcapcut/studio_orchestrator.py` เรียก timeline/brief compliance validator ก่อน ready |
| ผลงานเปิดและ export ได้จริง | run `4deaab5f-05f4-4580-81ff-46bb4b63381e`; `workspace/road-report-001/exports/road-report-001-studio-v22.mp4`: 180.001 s, H.264/AAC 1920×1080 30 fps, 220,367,458 bytes; รายละเอียดใน [doc/36](./36-three-minute-autonomous-retest.md) |

### จุดอ่อน บั๊ก และหนี้ทางเทคนิค

| ID | หลักฐาน/ตำแหน่ง | ผลกระทบ |
|---|---|---|
| D1 | V22 มี title `ใช้ไฟล์ "โป้ง - หัวใจไม่เคยหยุดทำ1.mp3" เพียงเพลงเดียว`; `project_brief.py` เดิมยอมให้โมเดลยกข้อกำหนดการผลิตเป็น `required_messages`; `studio_roles.py` วางทุก required message เป็น title | ข้อความบนจอผิดเจตนาและลดความน่าเชื่อถือ |
| D2 | `studio_roles.py:create_long_timeline` เดิมรับ `recommendations` แต่ไม่ส่งให้ Lead Editor; premise/audience effect จาก synthesis ก็หาย | ใช้โทเคนเรียกผู้เชี่ยวชาญแต่ความคิดไม่ถึงโต๊ะตัดต่อ |
| D3 | `studio_orchestrator.py` เดิมเช็ก visual diversity ภายในรอบ sequence; `revise_timeline` รอบท้ายกลับเข้า validator พื้นฐานโดยไม่ตรวจซ้ำเรื่องภาพ/ช่วงแหล่งวิดีโอ | candidate ที่แก้เพื่อตรง brief อาจกลับไปซ้ำ asset/source |
| D4 | `studio_snapshot.py` เดิมหารขนาด JSON ทั้งก้อนด้วยจำนวน assets ก่อน `DataPolicyGate.authorize` | payload จริงอาจเกินเพดานที่ตั้งไว้ |
| D5 | `media_cognition.py` บันทึก vision frame เป็นช่วง 1 µs; `media_readiness.py` เดิมนับ semantic modality ทุกชนิดสำหรับ source range | frame ที่ตรงเพียงจุดเดียวหรือเสียงอย่างเดียวถูกอ่านว่าเพียงพอสำหรับภาพเคลื่อนไหวหลายวินาที; ยังพิสูจน์เนื้อหาทั้งช็อตไม่ได้ |
| D6 | `studio_orchestrator.py` เดิม mark run `candidate_ready` ก่อนเขียน JSON output | write failure ทำให้ ledger ชี้ไปยังไฟล์ที่ไม่มี |
| D7 | `studio_roles.py` จำกัด sequence สูงสุด 8 ไม่ว่าความยาวงาน; 20 นาทีจึงเฉลี่ย 150 s/sequence | prompt แบบ 4–8 ช็อต ช็อตละ 3–10 s ไม่สอดคล้องกับความยาวนี้ |
| D8 | `professional_finishing.py` ส่ง timing/rationale ให้ AI แต่ไม่ส่งคำอธิบายภาพหรือ arc เฉพาะ sequence; V22 ใช้ `Soft_Grain` 30 จาก 32 ภาพ | **สมมติฐาน:** finishing จึงสม่ำเสมอเกินไป; ต้องทดสอบ A/B ก่อนสรุปสาเหตุ |
| D9 | `__main__.py` เดิมเขียน finishing manifest ก่อน `create_draft`; หาก draft ล้ม manifest เดิมขวาง retry | recovery ที่ operator ต้องลบ/เปลี่ยนชื่อเอง; รอบนี้ stage manifest จน draft สำเร็จ |
| D10 | snapshot ประมาณ 137 KB ถูกส่งซ้ำให้ 6 specialist; `ai_provider.py` รับ usage แล้ว แต่ไม่มี per-stage cost/checkpoint | ค่าใช้จ่ายและ retry ยังมองไม่ชัด; ยังไม่มีหลักฐานว่ารูปแบบ TOON ช่วยจริง |
| D11 | V22 มีภาพนิ่ง 24 ช็อตและวิดีโอ 8 ช็อต (วิดีโอราว 52 s จาก 180 s) | ข้อสังเกตเชิงรูปแบบ ไม่ใช่คำตัดสินคุณภาพ; ต้อง blind review กับบรีฟ |

## เฟส 2 — สาเหตุและลำดับ

รากร่วมคือ **สัญญาระหว่างบรีฟ → council → editor → QA ไม่ครบ**: ข้อจำกัดจากผู้ใช้ไม่ได้แยกจาก copy ที่จะเผยแพร่, handoff ถูกตัดทอน, และ invariant บางข้ออยู่เฉพาะการสร้าง sequence จึงไม่คุ้มครอง candidate สุดท้าย อีกกลุ่มคือ **ขอบเขต evidence และ transaction ไม่ชัด**: 1 sampled frame ไม่ใช่การยืนยันทั้งช่วงเวลา, และสถานะ ready ต้องสัมพันธ์กับ artifact ที่เขียนสำเร็จ

| Priority | งาน | Impact | Effort | เหตุผล |
|---|---|---|---|---|
| P0 | แยก user-locked on-screen copy, final diversity gate, write-before-ready, payload ceiling | สูง | ต่ำ–กลาง | ทำให้ผลลัพธ์ผิดเจตนา/ความปลอดภัยข้อมูล/สถานะผิด |
| P1 | modality-aware evidence, handoff ผู้เชี่ยวชาญ, source-coverage QC | สูง | กลาง | ลด false confidence และทำให้ council มีผลจริง |
| P1 | เก็บ usage/cost ต่อ stage และ checkpoint retry | กลาง–สูง | กลาง | คุมงบ OpenRouter และการ recover |
| P2 | chapter/sequence planner สำหรับ 20+ นาที, local revision/cache | สูงสำหรับ long-form | สูง | เป้าหมายเดิมยังไม่พร้อมผลิตจริง |
| P2 | finishing context A/B และ blind benchmark | สูงต่อความว้าว | กลาง–สูง | ต้องมีคะแนนจากคนและตัวอย่างหลายงาน |

## เฟส 3 — ทางเลือก

| ทางเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| A. แก้ prompt ของ OpenRouter อย่างเดียว | เริ่มเร็ว, โค้ดน้อย | โมเดลยังอาจผิด; การ repair ข้ามกติกาได้; QA อธิบายซ้ำไม่ได้ |
| B. Typed contracts + deterministic final gates + ให้ OpenRouter repair งานสร้างสรรค์ (**แนะนำ**) | ตรวจซ้ำอัตโนมัติ, provenance ชัด, รักษา AI authorship | ต้องออกแบบ contract และ benchmark เพิ่ม; บางงานถูก reject เมื่อข้อมูลไม่พอ |
| C. ส่ง raw media ให้ multimodal model วางแผนและตัดต่อรอบเดียว | บริบทภาพ/เสียงครบในหนึ่งโมเดล | ค่าใช้จ่าย/latency/สิทธิ์ข้อมูลสูง, traceability และแก้นาที 12–13 ยาก |

เลือก B และใช้ metadata/observations จาก SSOT เป็น input หลักตามความคิดของผู้ใช้ การบีบ serialization แบบ TOON ให้ตัดสินจากการวัด token/ความถูกต้องจริง; ลด payload ด้วย scoped retrieval และ cache ก่อน

## เฟส 4 — สถาปัตยกรรมและ interfaces

```text
Asset files → Eye/Ear/ffprobe → Asset Understanding Map (SSOT)
                                  ↓ scoped snapshot + policy gate
Typed ProjectBrief → specialist recommendations → Clip Director synthesis
                                                  ↓ explicit editorial handoff
                                     Lead Editor sequence candidates
                                                  ↓
                     timeline + modality/evidence + diversity + brief gates
                                                  ↓
                     durable candidate JSON → ready ledger → finishing plan
                                                  ↓
                                    pyCapCut draft → CapCut export/review
```

ขอบเขตไฟล์และสัญญา: `project_brief.py` เก็บข้อกำหนดแบบ typed โดย `required_messages` ต้องเป็นข้อความบนจอที่ผู้ใช้สั่งชัด; `studio_roles.py` รับ accepted recommendations/premise/audience effect ผ่าน handoff; `studio_quality.py` คืน `EditorialQCReport` แบบ JSON จาก candidate สุดท้าย; `media_readiness.py` คัด evidence ตาม modality/source time; `studio_orchestrator.py` เป็น transaction boundary; `studio_snapshot.py` บังคับ data policy ก่อนส่ง provider. UI ใช้ `EngineRunner` events/callbacks ตาม `engine_runtime.py` โดยไม่แตะรายละเอียด pyCapCut โดยตรง

สำหรับ 20+ นาที: แยก chapter (narrative intent) → sequence (bounded AI context) → stable segment IDs/receipts. `LocalizedChangeService` หา dependency ของช่วง 12–13 นาที; re-plan เฉพาะ sequence ที่ได้รับผลและบริบทข้างเคียง; render/cache เฉพาะชิ้นที่ hash เปลี่ยน แล้วประกอบไฟล์ใหม่และ QC จุดต่อ การรับประกันว่า *ไม่ render ทั้งหมด* ยังต้องทำ cache/render splice จริงและทดสอบ codec boundary

## เฟส 5 — Kanban, Definition of Done, ความเสี่ยง

| Card / สถานะ | Definition of Done | ความเสี่ยง |
|---|---|---|
| STU-101 P0 — Implemented, validate | explicit copy ไม่กลายเป็น production instruction; test regression | บรีฟใช้รูปแบบคำสั่งที่ยังไม่รู้จัก ต้องเพิ่ม parser/typed clarification |
| STU-102 P0 — Implemented, validate | candidate สุดท้าย reject ภาพซ้ำ/source overlap หลังทุก revision | กฎ diversity อาจเข้มเกินสำหรับ assets น้อย; ให้ reject อย่างโปร่งใส |
| STU-103 P0 — Implemented, validate | output write failure ไม่สร้าง ready ledger; full payload เกิน ceiling ถูก reject; draft failure ไม่ทิ้ง finishing manifest | crash ระหว่าง file/DB ยังอาจมี orphan file; reconcile/recovery card ถัดไป |
| STU-104 P1 — Implemented slice | handoff accepted recommendations ถึง Lead Editor; ภาพต้องมี vision/OCR | vision frame หนึ่งจุดยังไม่รับรองทั้งช็อต |
| STU-105 P1 — Ready | per-stage token/cost ledger, scoped snapshots, idempotent checkpoints; rerun ไม่เรียก stage ผ่านแล้ว | ราคา/provider usage เปลี่ยนได้; benchmark ต้องบันทึกจริง |
| STU-106 P1 — Ready | coverage QA ระบุสัดส่วนช็อตที่ sampled/ตรวจ, แยก unknown จาก understood; fact review | model hallucination และ OCR/ASR ภาษาไทย |
| STU-107 P2 — Options | 20-min plan มี sequence ขนาดจำกัด, edit 12–13 นาทีแล้ว render เฉพาะ affected chunks, seamless output | GOP/transition/audio seam |
| STU-108 P2 — Options | blind human review หลาย brief, preset/finishing A/B, measurable quality gains | subjective score และชุดตัวอย่างไม่พอ |

Pull ทีละ WIP ตาม [Kanban model](./10-agile-kanban-operating-model.md); อย่าย้าย card เป็น Done จาก unit tests เพียงอย่างเดียวเมื่อ DoD ต้องการ media/human review

## เฟส 6 — สิ่งที่พัฒนาและทดสอบรอบนี้

- แก้ `project_brief.py` ให้ข้อความบนจอที่สั่งชัดเป็น SSOT ของ `required_messages`; เพิ่ม regression test สำหรับคำสั่งชื่อเพลง
- ส่ง accepted specialist recommendations, premise, audience effect และ unresolved objections ถึง Lead Editor ในทุก long-form sequence
- เพิ่ม final `studio_quality.py` gate/report หลัง candidate ทุก revision; รายงาน still reuse, video interval reuse และ pair overlap
- ตรวจชนิด evidence สำหรับภาพ (`vision`/`ocr`) แยกจากเสียง (`speech`/`sound`/`music`); ยังไม่อ้างว่าหนึ่ง frame ครอบคลุมทั้งช็อต
- ตรวจขนาด full snapshot payload ต่อคำขอ และ stage output JSON แบบ fsync/rename ก่อน mark run ready
- stage finishing manifest จน pyCapCut สร้าง draft สำเร็จ; หากการอัปเดต failure ledger เองล้มยังคง exception ต้นเหตุ
- Focused tests ที่ครอบคลุมส่วนเปลี่ยนแปลงผ่าน; full suite `python -m unittest discover -s tests -p 'test_*.py' -q` ผ่าน 125 tests, 0 failures; `compileall -q mtcapcut` และ `git diff --check` ผ่าน

**ขีดจำกัด:** ยังไม่มี re-run/OpenRouter cut ใหม่หลังแก้; V22 เป็นผลก่อนแก้และยังมี title ผิดเจตนา จึงไม่ควรใช้เป็นหลักฐานว่า creative quality ผ่าน การทำ long-form 20 นาทีแบบ localized render, cost checkpoint, visual coverage benchmark และ blind review ยังไม่เสร็จ

### อ้างอิงภายนอก

- [OpenRouter support: usage accounting](https://openrouter.ai/support)
- [OpenRouter Responses API](https://openrouter.ai/docs/api/api-reference/responses/create-responses)
- [CapCut: Pro export prompt](https://www.capcut.com/help/capcut-pro-export-prompt)
- [BBC Editorial Guidelines, Accuracy](https://downloads.bbc.co.uk/guidelines/editorialguidelines/pdfs/bbc-editorial-guidelines-section-3-accuracy.pdf)
- [BBC guidance on pictures from social media](https://downloads.bbc.co.uk/guidelines/editorialguidelines/pdfs/social-media-pictures.pdf)
