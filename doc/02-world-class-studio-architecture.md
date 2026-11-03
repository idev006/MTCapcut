# World-Class Studio Architecture

> บทบาทในเอกสารนี้เป็นแบบจำลองของ MTCapcut ไม่ใช่การอ้างว่าทุกสตูดิโอใช้ชื่อตำแหน่งเดียวกัน หลัก workflow ที่ตรวจเทียบจากแหล่งวิชาชีพอยู่ใน [Professional Post-Production Workflow Research](./23-professional-post-production-workflow-research.md)

> ขอบเขต UI/deployment: UI เป็นเปลือกที่เรียก application services/engines ผ่าน typed requests, job handles และ events เท่านั้น งานหนักห้ามรันบน UI thread รายละเอียดอยู่ใน [Deployment, UI Bridge and AI Provider Architecture](./25-deployment-ui-bridge-ai-provider-architecture.md)

## แนวคิดหลัก

ระบบต้องจำลองการทำงานของสตูดิโอ ไม่ใช่โมเดลเดียวสั่งเครื่องมือทั้งหมด บทบาทแต่ละฝ่ายมีขอบเขตความเชี่ยวชาญ สามารถเสนอทางเลือก ทักท้วง และให้หลักฐานได้ ก่อน Clip Director สังเคราะห์ภาพรวม

คำว่า “world-class” เป็นเป้าหมายคุณภาพ ไม่ใช่คำรับรองล่วงหน้า คุณภาพต้องพิสูจน์ด้วย blind review, factual accuracy, edit-time reduction และผลทดสอบกับงานจริงหลายประเภท

## Creative leadership

- **Executive Producer** — รักษาเป้าหมาย ขอบเขต เวลา และนิยามความสำเร็จ
- **Clip Director** — รักษาความหมาย อารมณ์ จังหวะ และความเป็นเอกภาพทั้งเรื่อง
- **Creative Director** — กำหนด visual language และความสดใหม่
- **Audience & Insight Strategist** — วิเคราะห์ผู้ชม intent และผลลัพธ์ที่ต้องการ
- **Story Architect** — สังเคราะห์ข้อมูลเป็น premise, narrative arc และ beats

## Editorial department

- **Lead Editor** — สังเคราะห์ editorial decisions เป็น candidate timeline
- **Footage Curator** — ค้นหาและจัดอันดับช็อตโดยใช้ความหมายและคุณภาพ
- **Narrative Editor** — ตรวจตรรกะ ความชัด และความต่อเนื่องของเรื่อง
- **Rhythm & Pacing Editor** — ตรวจระยะช็อต ความหนาแน่น และจังหวะ
- **Continuity Editor** — ตรวจเวลา สถานที่ ทิศทาง บุคคล และเหตุการณ์
- **Hook Editor** — ดูแล opening, reveal และ retention points

## Picture, sound and graphics

- **Visual Quality Supervisor** — ตรวจ focus, exposure, shake, resolution และ artifacts
- **Color Director** — กำหนด mood และ color continuity
- **Sound Director** — กำหนด dialogue, ambience, silence, SFX และ loudness intent
- **Music Supervisor** — ดูอารมณ์ จังหวะ สิทธิการใช้ และความสัมพันธ์กับเนื้อหา
- **Motion & Graphic Director** — ดู hierarchy, typography, safe area และ motion
- **Subtitle Editor** — ตรวจภาษา timing ความอ่านง่าย และ line breaking

## Trust and review

- **Fact & Context Editor** — ตรวจข้อเท็จจริงและป้องกันการสื่อผิดบริบท
- **Brand Guardian** — รักษาภาพลักษณ์ ภาษา สี และกฎแบรนด์
- **Ethics & Sensitivity Reviewer** — ตรวจความเป็นส่วนตัว ศักดิ์ศรี และความละเอียดอ่อน
- **Audience Simulator** — ประเมินจากมุมมองผู้ชมเป้าหมายหลายกลุ่ม
- **Critical Reviewer** — วิจารณ์โดยไม่ยึดติดกับผู้สร้างร่าง
- **Technical QC** — ตรวจ media integrity, timing, loudness และ project validity

## ขอบเขตซอฟต์แวร์

```text
UI / CLI / API
       |
Application Service
       |
Workflow Orchestrator -------- Job State Store
       |
Studio Council / Clip Director
       |
Domain engines
  - intent and insight
  - media intelligence
  - story and creative direction
  - footage judgment
  - editorial decision
  - sound, graphics and subtitles
  - fact, ethics and critique
       |
Timeline Plan (provider-neutral SSOT)
       |
Infrastructure adapters
  - FFmpeg / ffprobe
  - AI providers
  - pyCapCut
       |
Artifacts / CapCut Draft / Reports
```

## กติกาการประสานงาน

1. Engine ไม่เรียก engine อื่นโดยตรง
2. Orchestrator ส่ง immutable input contract และรับ result contract
3. ทุกข้อเสนอเชิงวิจารณญาณต้องมี `recommendation`, `confidence`, `evidence`, `risks`, `alternatives`
4. ความเห็นขัดแย้งไม่ถูกลบทิ้ง แต่บันทึกใน Decision Ledger
5. Clip Director สังเคราะห์ความเห็น แต่เปลี่ยน user-confirmed facts ไม่ได้
6. Fact, ethics และ technical blockers ต้องแก้หรือได้รับการยกเว้นจากมนุษย์อย่างชัดแจ้ง
7. การตัดสินใจที่ส่งผลต่อ timeline ต้องอ้าง asset ID และ time range เสมอ

## Contracts สำคัญ

- `ProjectBrief`: intent, audience, message, facts, prohibitions, delivery constraints
- `ProjectAssetBundle`: รายการ assets, role, hash, source, rights และ ingest status ของงานหนึ่ง
- `MediaAsset`: stable ID, content hash, paths, streams, duration และ provenance
- `Observation` และ `Claim`: แยกสิ่งที่ตา/หูตรวจพบจากความหมายที่สมองอนุมาน พร้อม evidence และ fact status
- `EvidenceRef`: asset ID, start/end time, frame/time reference และ extractor version
- `CreativeBrief`: premise, tone, audience effect, style constraints
- `StudioRecommendation`: recommendation, evidence, confidence, risks, alternatives
- `EditDecision`: source range, timeline range, role, rationale และ dependencies
- `TimelinePlan`: tracks, segments, transitions, captions, audio และ approval state
- `QualityReport`: findings, severity, owner, evidence และ disposition
- `DecisionLedger`: proposals, objections, final decision, actor/version และ timestamp

## Clip Director ไม่ใช่ single point of intelligence

Clip Director เป็น domain service ระดับสูงที่รักษาภาพรวม แต่ต้องรับข้อเสนอจากหัวหน้าฝ่ายต่าง ๆ การอนุมัติ creative direction ไม่ลบล้าง factual หรือ technical blocker และ workflow สามารถเลือกทีมย่อยตามระดับความเสี่ยงได้:

- Quick edit: producer, director, lead editor, fact editor, technical QC
- Standard report: creative, story, footage, editorial, sound, graphics, fact, critique, QC
- High-stakes production: full studio council และ human approvals หลายจุด

## Failure handling

- External process failure: เก็บ command แบบ redact, exit code, stderr และ retry policy
- AI uncertainty: ส่ง `needs_human_review` แทนการเดา
- Missing evidence: ห้ามสร้าง factual claim จาก filename เพียงอย่างเดียว
- Incompatible CapCut draft: quarantine artifact และเก็บ fixture สำหรับ regression
- Partial workflow: resume จาก checkpoint โดยไม่วิเคราะห์ asset เดิมซ้ำหาก hash/config/version ไม่เปลี่ยน

