# MTCapcut Development Roadmap

วันที่จัดทำ: 2 พฤศจิกายน 2026  
สถานะ: แผนพัฒนาแบบ Agile Kanban; ทบทวนทุก Delivery Review  
Execution SSOT ของ cards: [Kanban Backlog](./14-initial-kanban-backlog.md)  
สถานะที่ผู้ใช้ดู: [Progress Dashboard](./19-progress-dashboard.md)

## เป้าหมายผลิตภัณฑ์

ผู้ใช้ส่ง clips, audio/MP3, pictures และ text files พร้อมบรีฟ ระบบตรวจและทำความเข้าใจสื่อเป็นแผนที่หลักฐาน สตูดิโอเสมือนเสนอเรื่องและการตัดต่อพร้อมเหตุผล ผู้ใช้แก้และอนุมัติ แล้วระบบสร้าง CapCut draft ที่เปิดแก้และส่งออกได้

## หลักส่งมอบ

แต่ละ milestone ต้องมี demo, automated test ที่เหมาะสม, limitations และผลตรวจของมนุษย์เมื่อเกี่ยวข้อง งานบน board เดินตาม Definition of Workflow และ WIP limits ใน [Kanban Operating Model](./10-agile-kanban-operating-model.md) ลำดับ milestone เป็น dependency และเกณฑ์ตรวจรับ ไม่ใช่กำหนดวันส่งที่ยังไม่มีข้อมูล cycle time

| Milestone | สิ่งที่ผู้ใช้เห็น/ทำได้ | เกณฑ์ผ่านและหลักฐาน | สถานะ 2 พ.ย. 2026 |
|---|---|---|---|
| M0 — Foundation | รับไฟล์ทีละรายการและดูข้อมูลเทคนิค | config, doctor, file validation, hash, ffprobe, SQLite tests | technical slice ผ่าน; config v2/Windows delivery และ per-asset external-AI gate เพิ่มแล้ว, full regression 83 tests |
| M1 — Asset Map | ส่งชุดไฟล์ทั้งงาน ดูรายการ/บทบาท/สิทธิ/เวลา และแก้ข้อมูลได้ | bundle ingest, versioned map, queries, revisions, artifact manifest, safe re-run tests | บางส่วน; bundle/version/history/artifact และ editorial revision persistence ผ่าน, asset correction/rights ยังไม่ครบ |
| M2 — ตาและหู | เปิดแผนที่ช็อต เฟรม คำพูด เสียง และข้อความในภาพพร้อมเวลา | shot/frame/ASR/OCR/audio observations; benchmark ภาษาไทยและความผิดพลาด | implementation slice ผ่าน: shot candidates + sampled frames + local/cloud ear; OCR และ benchmark ยังไม่ครบ |
| M3 — สมองและทีมบรรณาธิการ | เห็น intent, story alternatives, shot selects และข้อทักท้วงพร้อมเหตุผล | claims อ้าง evidence, fact/ethics review, blind editorial rubric, human corrections | autonomous Studio Council candidate slice ผ่าน live smoke; render/approval/blind evaluation ยังไม่จบ |
| M4 — แผนตัดต่อ | ตรวจและแก้ Timeline Plan ก่อนสร้าง draft | deterministic validation, long-form hierarchy, source ranges, duration, tracks, captions, audio, approvals | hierarchy/edit-scope/plan mapping + persisted change request ผ่าน; apply-change/approvals/transitions ยังไม่ครบ |
| M5 — CapCut draft | เปิด draft ที่สร้างผ่าน pyCapCut ใน CapCut และแก้ต่อได้ | create/open/save/reopen/manual export; ตรวจภาพ เสียง ไทย และ timing | compatibility slice create/open/export ผ่าน; edit-save-reopen matrix ยังไม่ครบ |
| M6 — UI และงานประจำ | เลือก assets, ดู map, review plan, สร้าง draft และติดตามงานจาก UI | UI เรียก application service, E2E demo, error recovery, usability/time study | non-blocking job/event/cancel bridge ผ่าน unit tests; UI toolkit/E2E ยังไม่เริ่ม |

## ลำดับงานที่มีความหมายต่อผู้ใช้

### M0 → M1: ข้อมูลและหลักฐานเชื่อถือได้

ปิด ADR ด้านโครงสร้าง Python และ storage; ทำ typed TOML, doctor, domain contracts, bundle ingest, AssetVersion และ Artifact Manifest; แยกสิทธิและบทบาทข้อความ; ทำ query/review/revision โดยไม่มีการเขียนทับประวัติ

Demo: ส่งคลิป MP3 รูป และ `brief.txt` อย่างละไฟล์แล้วเห็นแผนที่ assets; เปลี่ยนไฟล์ต้นฉบับแล้วระบบสร้าง version ใหม่และแสดงผลวิเคราะห์ที่ต้องทำซ้ำ

### M1 → M2: เห็นและได้ยิน

เริ่มด้วย ffmpeg frame/audio extraction และ shot candidates; benchmark ASR/OCR ภาษาไทยก่อนเลือก model; align observations บน original timebase; บันทึก confidence, artifact, model version และ failure

Demo: คลิกช็อตแล้วเห็นเฟรม คำพูดและข้อความในภาพของช่วงนั้น พร้อมลิงก์กลับต้นฉบับ; เหตุการณ์ที่หาไม่พบถูกระบุว่า unknown

### M2 → M3: เข้าใจและใช้วิจารณญาณ

สร้าง Intent/Story/Footage/Lead Editor/Fact/Critic contracts และ AI provider adapter; สร้าง claims จาก observations พร้อมข้อขัดแย้งและทางเลือก; ทดสอบกับ brief ที่ภาพชวนให้เข้าใจผิด; เก็บ human corrections เป็น revisions

Demo: ระบบเสนอ 2 แนวเรื่อง เลือกช็อตพร้อมเหตุผล และหยุดข้อความ “แล้วเสร็จ” เมื่อผู้ใช้ยืนยันว่างานยังดำเนินการ

### M3 → M4: วางไทม์ไลน์

แปลง editorial decisions เป็น Timeline Plan กลาง มี track, timing, transitions, captions, sound และ approval state; validator ตรวจ source range, overlap, factual blockers และ delivery profile

Demo: ผู้ใช้ย้าย/ตัดช็อตหรือแก้ข้อความ แล้วเห็นผลต่อความยาวและ finding ก่อนสร้าง draft

### M4 → M5: พิสูจน์การเชื่อม CapCut

ตรึง pyCapCut 0.0.4 ใน adapter, ใช้ test draft ชื่อใหม่, ตรวจกับ CapCut 9.7.0.4153 ทีละ feature และเก็บผลเปิด/บันทึก/เปิดใหม่/export; feature ที่ไม่ผ่านต้องมี fallback ที่ระบุชัด

Demo: เปิด draft ที่มีวิดีโอ ภาพ MP3 และข้อความไทยแยกชั้นใน CapCut แล้ว export ด้วยมือ

### M5 → M6: หน้าจอใช้งานประจำ

สร้าง UI หลัง application services เสถียร โดย UI ไม่แตะ ffmpeg/pyCapCut/SQLite โดยตรง; มี preview, evidence map, review queue, decision history และ job status; ประเมินเวลาและจำนวนแก้ไขกับงานจริง

Demo: ผู้ใช้ทำหนึ่งรายงานตั้งแต่เลือกไฟล์จนได้ approved CapCut draft จาก UI

## เส้นงานขวางทุก milestone

- Security/privacy: classification, prompt injection จากสื่อ, path safety, provider policy, retention
- Rights: เพลง ภาพ ฟอนต์ บุคคล pyCapCut/FFmpeg/CapCut terms ก่อน distribution
- Observability/cost: job/trace ID, latency, retry, token/GPU/API cost, budget
- Quality: fixtures ที่มีสิทธิ, regression tests, professional review และ fact error tracking
- Documentation: ADR, source register, compatibility matrix และ status dashboard

## เกณฑ์เลื่อน milestone

1. Cards ที่จำเป็นผ่าน Done policy พร้อม evidence links
2. Demo ทำซ้ำจากคำสั่งหรือ UI ที่ระบุได้
3. Critical findings เป็นศูนย์; high findings ปิดหรือมี waiver ตาม policy
4. ความเสี่ยงคงเหลือและข้อจำกัดแสดงบน dashboard
5. Product Owner ตรวจรับผลที่เห็นได้ ไม่ใช้เพียงจำนวน tests เป็นคำรับรองคุณภาพสร้างสรรค์

## งานที่ควร pull ถัดไป

1. `EXP-001`–`EXP-003` — เตรียมชุด benchmark ที่มีสิทธิสำหรับ Thai ASR/OCR/shot detection; ADR-002/DOC-002 enforcement slice ผ่านแล้ว
2. สร้าง semantic batch analysis จาก shot map ภายใต้ per-asset policy พร้อม bounded job budget
3. `ENG-006` — asset correction API และ normalized rights manifest; editorial revision persistence แยกส่งแล้วใน `ENG-007`
4. review/promotion ของ `ENG-007` แล้วออกแบบ approved change application โดยไม่ข้าม human approval gate
5. retention cleanup แบบ dry-run/receipt และตรวจ provider-side terms ก่อน production

Replenishment ต้องตรวจ owner, dependencies, acceptance และ capacity ก่อนย้ายเข้า Ready ข้อเสนอข้างต้นไม่ถือว่า card ถูก pull แล้ว

