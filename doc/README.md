# MTCapcut Documentation

เอกสารชุดนี้เป็นฐานความรู้และข้อกำหนดเริ่มต้นสำหรับการพัฒนา MTCapcut ให้เป็นทีมผลิตและตัดต่อวิดีโอเสมือนระดับสตูดิโอ โดยใช้ AI เพื่อทำความเข้าใจเจตนาและสื่อ ใช้ FFmpeg/ffprobe เป็นเครื่องมือวิเคราะห์และเตรียมสื่อ และใช้ pyCapCut เป็น adapter หลักสำหรับสร้างโปรเจกต์ CapCut ที่มนุษย์เปิดตรวจ แก้ไข และส่งออกได้

## สถานะเอกสาร

- วันที่ตรวจสอบล่าสุด: 2 พฤศจิกายน 2026
- สถานะ: Foundation implementation + synthetic CapCut compatibility proof — ยังไม่ใช่ production/world-class certification
- Environment หลัก: `D:\dev\MTCapcut\.venv`
- pyCapCut: `0.0.4`
- CapCut active version: `9.7.0.4153`
- FFmpeg build: `2025-10-30-git-00c23bafb0`

## เอกสาร

1. [Project Charter](./01-project-charter.md) — เป้าหมาย ขอบเขต คุณค่าหลัก และนิยามความสำเร็จ
2. [World-Class Studio Architecture](./02-world-class-studio-architecture.md) — ทีมเสมือน engines การประสานงาน และขอบเขตอำนาจ
3. [Environment Baseline](./03-environment-baseline.md) — ข้อเท็จจริงที่ตรวจจากเครื่องจริง
4. [Research Findings](./04-research-findings.md) — ผลศึกษารอบแรกและผลกระทบต่อการออกแบบ
5. [SSOT and Configuration](./05-ssot-and-configuration.md) — SSOT, central TOML และลำดับการ override
6. [Test and Validation Strategy](./06-test-and-validation-strategy.md) — test pyramid, compatibility gates และเกณฑ์ยอมรับ
7. [Source Register](./07-source-register.md) — แหล่งอ้างอิง วันที่ตรวจ และระดับความน่าเชื่อถือ
8. [Foundation Implementation Plan](./08-foundation-implementation-plan.md) — แผนสร้างฐานระบบแบบ test-first
9. [World-Class Grade Definition](./09-world-class-grade-definition.md) — นิยามทีม บทบาท สมรรถนะ และเกณฑ์พิสูจน์ระดับคุณภาพ
10. [Agile Kanban Operating Model](./10-agile-kanban-operating-model.md) — Definition of Workflow, WIP, policies, cadences และ flow metrics
11. [AI Media Engine Research Architecture](./11-ai-media-engine-research-architecture.md) — evidence pipeline, engine contracts และ benchmarks
12. [Review and Revise Governance](./12-review-revise-governance.md) — review state machine, findings, waivers และ exit policy
13. [Risk, Security, Rights and Observability](./13-risk-security-rights-observability.md) — trust boundaries, rights gates, telemetry และ cost control
14. [Initial Kanban Backlog](./14-initial-kanban-backlog.md) — backlog เริ่มต้นที่ trace กลับ findings และหลักฐาน
15. [Asset Intake and Cognition Contract](./15-asset-intake-and-cognition-contract.md) — input clips/audio/pictures/text และเกณฑ์พิสูจน์ตา หู สมอง
16. [Asset Understanding Map Design](./16-asset-understanding-map-design.md) — SSOT ราย project, schema, versioning, queries และการตรวจย้อนกลับ
17. [Development Status](./17-development-status.md) — สิ่งที่ implement และยังไม่ผ่านเกณฑ์ ณ ปัจจุบัน
18. [Development Roadmap](./18-development-roadmap.md) — ระยะพัฒนา M0–M6 และเกณฑ์ส่งมอบ
19. [Progress Dashboard](./19-progress-dashboard.md) — สถานะที่ตรวจได้สำหรับผู้ใช้และทีม
20. [Foundation User Guide](./20-foundation-user-guide.md) — วิธีตรวจระบบ รับ assets ดู map และสร้าง draft ใน sandbox
21. [CapCut Compatibility Report](./21-capcut-compatibility-report.md) — หลักฐาน create/open/export กับ CapCut 9.7.0.4153
22. [Long-form Editorial Model](./22-long-form-editorial-model.md) — Chapter/Scene/Segment/Element/Receipt และการแก้เฉพาะช่วง
23. [Professional Post-Production Workflow Research](./23-professional-post-production-workflow-research.md) — workflow และบทบาทที่ตรวจเทียบจากแหล่งอุตสาหกรรม
24. [ENG-007 Persisted Localized Change Plan](./24-eng-007-persisted-localized-change-plan.md) — แผน implementation/test สำหรับ revision, receipt และการแก้เฉพาะช่วงแบบ recoverable
25. [Deployment, UI Bridge and AI Provider Architecture](./25-deployment-ui-bridge-ai-provider-architecture.md) — non-blocking engine contract, provider adapters, batch launch และ config categories
26. [Windows Batch Usage Guide](./26-windows-batch-usage-guide.md) — วิธีเริ่ม ตรวจระบบ และเรียก engines ด้วย batch files

## ภาษาที่ใช้ในโครงการ

- **Engine**: หน่วยความสามารถเฉพาะด้านที่มี interface ชัดเจน ทดสอบแยกได้ และไม่ขึ้นกับ UI
- **Studio role**: บทบาทวิชาชีพที่ใช้วิจารณญาณ เช่น Story Architect หรือ Sound Director อาจใช้ engine หนึ่งตัวหรือหลายตัวสนับสนุน
- **Clip Director**: ผู้รักษาความเป็นเอกภาพของงานทั้งเรื่อง ไม่ใช่สมองเพียงตัวเดียวของระบบ
- **Workflow Orchestrator**: ผู้เดินกระบวนการทางเทคนิค ไม่มีอำนาจตัดสินเชิงสร้างสรรค์
- **Timeline Plan**: แผนตัดต่อกลางที่ไม่ผูกกับ pyCapCut หรือ UI
- **SSOT**: แหล่งข้อมูลที่เป็นเจ้าของข้อมูลชนิดหนึ่งอย่างชัดเจน

## หลักฐานกับสมมติฐาน

ข้อความในเอกสารใช้ป้ายกำกับต่อไปนี้:

- **ยืนยันแล้ว** — ตรวจจากเครื่องจริงหรือเอกสารปฐมภูมิ
- **ข้อเสนอออกแบบ** — แนวทางที่ต้องพิสูจน์ด้วย prototype/test
- **ยังไม่ยืนยัน** — ข้อมูลหรือความเข้ากันได้ที่ยังไม่มีหลักฐานเพียงพอ

