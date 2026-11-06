# World-class studio quality cycle — design and implementation

วันที่: 6 พฤศจิกายน 2026

## คำตัดสินปัจจุบัน

MTCapcut **ยังไม่ผ่านเกณฑ์ World-Class Grade** ตาม [นิยามโครงการ](./09-world-class-grade-definition.md) แม้ V22 export จาก CapCut ได้ เหตุผลคือการ export ยืนยันโครงสร้างและความเข้ากันได้ทางเทคนิค แต่ยังไม่มีหลักฐานว่าผู้ชมเข้าใจเรื่อง ตื่นเต้น หรือภาพทุกช่วงแสดงสิ่งที่ AI อ้าง

### หลักฐานจากโค้ดและงานจริง

| ประเด็น | หลักฐาน | ผลกระทบ |
|---|---|---|
| sequence งานยาว | `studio_roles.py` เดิมจำกัด 8 ช่วงเสมอ; 20 นาทีจึงได้เฉลี่ย 150 วินาทีต่อช่วง ทั้งที่ prompt ขอ 4–8 ช็อต ช็อตละ 3–10 วินาที | สัญญา editor ขัดกันเองและเสี่ยงให้โมเดลคืนแผนสั้น/ไม่ครบ |
| ความเข้าใจภาพ | `media_cognition.py` บันทึก frame vision เป็นช่วง 1 µs; V22 ใช้วิดีโอ 52,000,000 µs แต่ vision observations ที่ทับช่วงรวมเพียง 17 µs | หนึ่งเฟรมไม่พิสูจน์เหตุการณ์ตลอดช็อต; เป็น **sampled only** ไม่ใช่ภาพที่ตรวจครบ |
| finishing | `professional_finishing.py` เดิมส่ง timing/rationale แต่ไม่ส่ง visual observation ของแต่ละช็อต; V22 ได้ `Soft_Grain` 30/32 ช็อต | **สมมติฐาน** ว่าขาดบริบททำให้ดูซ้ำ ต้องพิสูจน์ด้วย A/B และคนดู |
| story/quality review | V22 มีภาพนิ่ง 128/180 วินาที, title คำสั่งเพลงผิดเจตนา (แก้ parser แล้ว) และยังไม่ผ่าน blind review | ยังไม่ยืนยัน story arc, pacing, visual originality, audience effect |

ผล 17 µs มาจาก `visual_evidence_report` บน candidate V22 กับ observations รุ่นปัจจุบันใน Understanding Map เป็น *ระยะเวลาของ sampled observations* ไม่ใช่คำกล่าวว่าเฟรมอื่นไม่มีภาพหรือคลิปผิดข้อเท็จจริง

## ทางเลือกและข้อสรุป

| วิธี | ข้อดี | ข้อเสีย |
|---|---|---|
| เพิ่ม prompt ให้ AI ตัดต่อ “สวยขึ้น” | ทำเร็ว | ไม่มีหลักฐานว่าช็อตที่เลือกถูกหรือเจตนาถึงผู้ชม |
| แยก bounded edit jobs + evidence coverage + ส่ง visual context ให้ finishing (**เลือก**) | สัญญาไม่ขัดกัน, ตรวจสอบได้, AI ยังตัดสินสร้างสรรค์เอง | ต้องลงทุนเพิ่มใน shot evidence, usage ledger และ benchmark |
| ส่ง raw media ทั้งหมดให้ multimodal model รอบเดียว | บริบทภาพ/เสียงมาก | ค่าใช้จ่ายสูง, provenance/การแก้เฉพาะนาทีอ่อน และจัดการ 20+ นาทีลำบาก |

## สถาปัตยกรรมรอบนี้

```text
Brief + SSOT observations
      → Clip Director synthesis + specialist handoff
      → bounded SequenceJob (stable ID, <=30 s, exact global time)
      → OpenRouter Lead Editor เลือกช็อต/เวลา/เหตุผล
      → structural/diversity/visual-evidence QC (แยก status)
      → candidate + editorial review requirement
      → OpenRouter finishing ได้ story context + observed notes ตามช็อต
      → pyCapCut draft → export → technical QC → blind creative review
```

`sequence_planner.py` เป็น deterministic scheduling **ไม่เลือกช็อต**; `studio_roles.py` ให้ OpenRouter เลือกภาพตาม beat; `studio_quality.py` รายงาน sample coverage โดยไม่แปลงเป็นคะแนนศิลปะ; `professional_finishing.py` รับเฉพาะคำบรรยายภาพที่อ้าง evidence ของ asset เดียวกันและข้อมูลเรื่องจาก Clip Director; `studio_orchestrator.py` เก็บ QC ใน candidate เพื่อให้ UI อ่านได้

## Kanban / Definition of Done

| Card | สถานะ | เกณฑ์เสร็จ |
|---|---|---|
| WCS-101 bounded sequences | Validate | 20 นาทีแยกเป็นอย่างน้อย 40 jobs, แต่ละงาน <=30 s, ID/เวลาแน่นอน; 3 นาที 8 beats คง 8 jobs |
| WCS-102 visual evidence report | Validate | แยก point sample จาก interval coverage; V22 รายงาน sampled-only 8 ช็อต ไม่มีการอ้างว่าเห็นเต็ม 52 s |
| WCS-103 finishing context | Validate | OpenRouter ได้ visual evidence ที่อ้างกับช็อตและ premise/audience effect; ไม่รั่ว observation ของ asset อื่น |
| WCS-104 durable checkpoints/cost | Ready | หลัง failure resume sequence ที่ผ่านแล้วโดยไม่เรียก AI ซ้ำ; usage/cost ต่อ stage อยู่ใน SSOT |
| WCS-105 visual/event audit | Ready | เพิ่มการตรวจภาพหลายตำแหน่งต่อช็อต, identity/event claims ต้องมีหลักฐานและ human escalation |
| WCS-106 creative benchmark | Options | ชุดงานมีคำเฉลยและ blind panel หลาย genre; วัด intent, story, pacing, visual/sound craft, fact integrity และรายงาน disagreement |
| WCS-107 finishing experiment | Options | A/B กับบริบทภาพที่เพิ่ม วัดการเลือก treatment และ blind preference โดยไม่บังคับ filter diversity แบบผิวเผิน |

## Quality gates ที่ต้องแยก

- **Structural QC:** schema, duration, source bounds, asset IDs, diversity, music/text locks
- **Evidence QC:** current asset/version, visual observation ที่ทับช่วง, report sampled-only/unknown, fact-context findings
- **Technical QC:** export, codec, black/silence, audio profile, font/resource compatibility
- **Creative QC:** คนดูที่ไม่เห็นชื่อวิธีตัดประเมินเรื่อง จังหวะ อารมณ์ และความหมาย; คะแนนต้องเป็นเกณฑ์ของโครงการที่ประกาศก่อนทดลอง
- **Release decision:** ผู้รับผิดชอบเผยแพร่ตัดสินจากข้อมูลข้างต้น; ระบบไม่ใช้คำว่า world-class จากการผ่าน tests หรือ export เพียงอย่างเดียว

## ผลพัฒนาและข้อจำกัด

รอบนี้เพิ่ม bounded sequence jobs, visual evidence report และ finishing handoff จาก SSOT/Clip Director พร้อม tests. Evidence binder แนบ observation ที่ทับ source range จริง และ finishing ตัด visual note ที่อยู่นอกช่วงวิดีโอทิ้ง. OpenRouter V23 ผ่าน brief/structural gates, pyCapCut สร้าง draft และ CapCut 9.8 export ได้จริง แต่ `editorial_review_required=true`. ยังไม่มี checkpoint, visual understanding เต็มช็อต, A/B finishing หรือ blind creative score

### V23 live retest (private review)

- run `1ebee223-2db7-4d98-9395-e1e9322a080d`; candidate `workspace/road-report-001/editorial/autonomous-candidate-v23-3min.json`
- 180 วินาที, ภาพ 37 ช็อต: 31 ภาพนิ่งและ 6 วิดีโอ (วิดีโอรวม 38 วินาที); ไม่ใช้ภาพนิ่ง/ช่วงวิดีโอซ้ำ, required copy 3 ข้อถูกต้อง, brief compliance `pass`
- sampled video observation span รวม 17 µs จาก source video ที่เลือก 38,000,000 µs; ทั้ง 6 วิดีโอเป็น `sampled_only`; จึงต้องตรวจภาพจริงก่อนรับรองข้ออ้างของช็อต
- OpenRouter finishing: `Soft_Grain` 19, `BW_2` 3, ไม่ใส่ filter 15; `Mix` 6, `Overlay` 1, ไม่ใส่ transition 30. เป็นความหลากหลายเชิงกล ไม่ใช่คะแนนความสวย
- finishing รอบแรกถูก validator ปฏิเสธเพราะ model ส่ง filter intensity ต่ำกว่าข้อกำหนด; เพิ่มข้อความ repair ที่ระบุ segment/field แล้วรันใหม่สำเร็จ โดยไม่มี manifest/draft ค้างจากรอบล้ม
- pyCapCut draft `workspace/road-report-001/drafts/MT_ROAD_REPORT_001_AUTONOMOUS_PRO_3MIN_V23`; CapCut 9.8 เปิด timeline 03:00 และ export ไป `workspace/road-report-001/exports/road-report-001-studio-v23.mp4` โดยไม่ใช้ปุ่ม Share/sync
- FFprobe: H.264/AAC, 1920×1080, 30 fps, 180.000998 s, 220,476,906 bytes; FFmpeg blackdetect/silencedetect ไม่รายงานช่วงเกิน 1 s; automated suite 143 tests ผ่านหลัง source-range evidence fix

ข้อสรุป: **technical export PASS, creative/world-class NOT YET VERIFIED**; V23 ยังพึ่งภาพนิ่งมากและไม่มี blind audience review

### แหล่งปฐมภูมิ

- [Netflix delivery processing and manual QC states](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215652537-What-is-the-difference-between-Delivered-and-Processed-on-Backlot)
- [BBC Editorial Guidelines: Accuracy](https://downloads.bbc.co.uk/guidelines/editorialguidelines/pdfs/bbc-editorial-guidelines-section-3-accuracy.pdf)
- [Adobe Premiere media intelligence limitations](https://helpx.adobe.com/premiere/desktop/organize-media/file-organization/search-for-media-using-ai-powered-media-intelligence.html)
- [EBU R128 and loudness context](https://tech.ebu.ch/publications/r128)
- [W3C captions for prerecorded media](https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded)
- [OpenRouter usage fields](https://openrouter.ai/docs/api/api-reference/responses/create-responses)
