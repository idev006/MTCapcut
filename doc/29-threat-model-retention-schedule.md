# Threat Model and Retention Schedule

วันที่: 2 พฤศจิกายน 2026  
ขอบเขต: asset intake → evidence extraction → AI provider → SSOT observations

## Trust boundaries

1. User/project workspace — raw originals และ brief เป็น untrusted input
2. Local engines — ffmpeg, Python models, SQLite และ derived evidence
3. External provider — ข้อมูลข้ามเครื่องและอยู่นอกการควบคุมโดยตรง
4. UI/CapCut/export — แสดงผลและนำผลที่อนุมัติไปใช้; ไม่ควรเข้าถึง secret โดยตรง

## Threat register

| Threat | Likelihood / Impact | Control ปัจจุบัน | งานคงเหลือ |
|---|---|---|---|
| Prompt injection ใน OCR/transcript/brief | Medium / High | media เป็น evidence ไม่ใช่ system instruction; structured response validator; machine-proposed status | adversarial fixture และ explicit content delimiting benchmark |
| PII/ใบหน้า/เสียงถูกส่งเกินจำเป็น | Medium / High | per-asset approval, classification allowlist, bounded frame/audio artifact, payload limit | redaction engine และ human preview ก่อนส่ง |
| API key รั่วใน repr/log/CLI | Medium / Critical | secret field ถูกตัดจาก repr; CLI ไม่พิมพ์ config; endpoint pinning สำหรับ OpenRouter | OS credential store และ automated log scan |
| ส่ง full media หรือ payload ใหญ่โดยผิดพลาด | Low / High | engine/gate size limits; workflow ใช้ evidence slices | aggregate per-job budget และ duration limit |
| Provider เก็บข้อมูลนานหรือใช้ต่างวัตถุประสงค์ | Unknown / High | explicit external approval; local provider alternative | ตรวจ provider terms/retention และบันทึก provider snapshot |
| Policy เก่าถูกใช้หลัง revoke | Low / High | อ่าน latest append-only policy ทุก request | transaction-bound authorization receipt/job ledger |
| Path traversal/asset substitution | Medium / High | safe project ID, registered asset identity/hash/version | bind evidence hash to authorization decision |
| AI hallucination กลายเป็น fact | High / High | observations เป็น `machine_proposed`; claims/reviews แยกชั้น | fact-review queue, benchmark และ approval gate ก่อน timeline/export |
| Database corruption/concurrent writers | Low / High | SQLite transaction, rollback journal, backup/reopen tests | ADR-003 migration/concurrency implementation |
| Derived evidence ค้างเกินกำหนด | Medium / Medium | retention target ใน TOML | cleanup job + dry-run + deletion receipt ยังไม่ implement |

## Retention schedule

| Record | Target retention | Owner | Disposal/control | Implementation status |
|---|---|---|---|---|
| Raw originals | อายุโครงการหรือตามคำสั่งผู้ใช้ | Project Owner | ผู้ใช้ควบคุม; ห้าม auto-delete ใน slice นี้ | Policy only |
| Derived local evidence (frames/audio chunks) | 7 วันหลังสร้างเป็นค่าเริ่มต้น | Security/Data Steward | cleanup เฉพาะ artifact ที่ตรวจ provenance และไม่ใช่ original | NOT IMPLEMENTED |
| External request payload | ไม่เก็บสำเนาเพิ่มโดย MTCapcut หลัง request | AI Engine | encode in-memory; ห้าม log base64 | Implemented for engine path |
| Provider-side copy/log | ตาม provider terms | Provider + Product Owner | ต้องตรวจ/ยอมรับก่อน production | UNVERIFIED |
| Observations/claims/reviews | อายุโครงการ | Fact Editor | append-only correction/review; backup ตาม project | Implemented slice |
| Asset AI policies | อายุโครงการและ audit requirement | Security Owner | append-only; revoke ด้วย record ใหม่ | Implemented |
| Operational logs | เป้าหมาย 30 วันและไม่มี secret/media payload | Platform Owner | rotate/redact | Backend/rotation NOT IMPLEMENTED |
| Export/draft | ตามผู้ใช้และ publication policy | Project Owner | ผู้ใช้จัดการ; ไม่ลบ CapCut drafts อัตโนมัติ | User controlled |

## Incident and recovery rule

หากสงสัยว่าส่ง asset ผิด ให้บันทึก deny policy ใหม่ทันที, ปิด `allow_remote_ai`, เก็บ policy/job evidence ที่ไม่เผย secret, ระบุ provider/request window และให้ Product Owner ประสาน provider ตามข้อตกลง ห้ามลบ audit historyเพื่อกลบเหตุ การ rotate key และ notification เป็นขั้นตอนผู้มีอำนาจ ไม่ทำอัตโนมัติใน engine

## Acceptance state

- Code enforcement สำหรับ per-asset external AI: PASS
- Append-only revoke history: PASS
- Automated evidence cleanup: NOT RUN / NOT IMPLEMENTED
- Provider terms and provider-side retention verification: BLOCKED pending provider policy review
- Professional privacy/security sign-off: NOT RUN

