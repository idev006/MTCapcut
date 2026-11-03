# ADR-002 — AI Data and Provider Policy

วันที่: 2 พฤศจิกายน 2026  
สถานะ: Accepted for implementation slice; Product Owner publication approval remains separate

## บริบท

ระบบต้องใช้ทั้ง local AI และ external AI เพื่อวิเคราะห์ evidence ที่สกัดจาก clips, audio และ pictures แต่ global switch เพียงตัวเดียวไม่สามารถตอบได้ว่า asset ใดส่งออกได้ ใครอนุมัติ และการอนุมัติถูกเพิกถอนเมื่อใด ขณะเดียวกันการห้าม cloud ทั้งหมดจะตัด workflow ที่ผู้ใช้ต้องการทดสอบกับ OpenRouter

## การตัดสินใจ

ใช้การอนุญาตสองชั้นแบบ fail-closed:

1. Central TOML `[security].allow_remote_ai` ต้องเปิด
2. asset ต้องมี policy ล่าสุดใน Asset Understanding Map ซึ่งระบุ classification และ `external_ai_allowed=true`
3. classification ต้องอยู่ใน `[data_policy].allowed_external_classifications`
4. evidence package ต้องไม่เกิน `[data_policy].max_evidence_bytes`
5. policy ทุกครั้งเป็น append-only record พร้อม actor, reason และเวลา; การเพิกถอนทำด้วย record ใหม่

Classification SSOT มี 4 ค่า:

| Classification | ความหมาย | ค่าเริ่มต้นที่ส่ง external ได้ |
|---|---|---|
| `public_source` | สื่อจากแหล่งสาธารณะที่มี provenance | ได้ เมื่ออนุมัติราย asset |
| `internal_test` | สื่อที่ผู้ใช้ให้เพื่อทดสอบภายใน | ได้ เมื่ออนุมัติราย asset |
| `confidential` | ข้อมูลภายในที่ไม่ควรออก trust boundary | ไม่ได้ |
| `restricted` | ข้อมูลจำกัดสูง/อ่อนไหว | ไม่ได้ |

Loopback providers (`localhost`, `127.0.0.1`, `::1`) ไม่ออกจากเครื่อง จึงไม่ต้องมี external approval แต่ยังต้องผ่าน schema validation และ evidence-size limit ของ engine ส่วน remote LAN host ถือเป็น external ตามนโยบายนี้

## จุดบังคับใช้

`MediaCognitionEngine` ตรวจ policy หลังอ่านเฉพาะ file metadata และก่อนอ่าน payload เป็น base64/ก่อน transport call หาก provider เป็น external แต่ไม่มี gate, ไม่มี `asset_id`, ไม่มี policy, ถูกเพิกถอน, classification ไม่อนุญาต หรือ payload ใหญ่เกิน จะหยุดด้วย `PermissionError` และไม่ส่ง request

CLI ที่รองรับ audit workflow:

```powershell
python -m mtcapcut set-ai-policy PROJECT ASSET public_source --allow-external --actor "project-owner" --reason "approved private test"
python -m mtcapcut show-ai-policy PROJECT ASSET
```

การไม่ใส่ `--allow-external` คือบันทึก policy ใหม่เพื่อ deny/revoke ไม่ใช่แก้ record เดิม

## ทางเลือกที่พิจารณา

1. Global flag อย่างเดียว — ปฏิเสธ เพราะไม่มี least privilege, per-asset audit หรือ revoke history
2. Local-only — ปลอดภัยกว่าและยังรองรับเป็น deployment profile แต่ปฏิเสธเป็นข้อบังคับเดียวเพราะไม่ตอบโจทย์ cloud provider ที่ผู้ใช้อนุมัติ
3. Global gate + append-only per-asset policy — เลือก เพราะตรวจย้อนหลังได้ ทดสอบอัตโนมัติได้ และเปลี่ยน provider โดยไม่เปลี่ยน domain model

## ผลตามมาและข้อจำกัด

- media usage rights กับ permission ส่งข้อมูลให้ AI เป็นคนละ gate; ผ่านอย่างหนึ่งไม่แปลว่าผ่านอีกอย่าง
- ระบบส่งเฉพาะ bounded evidence artifact ไม่ส่ง full video โดยปริยาย
- provider-side storage/training/retention ยังขึ้นกับข้อตกลงของ provider และยังไม่ได้ยืนยันในระบบ จึงต้องถือเป็น residual risk
- การลบ evidence ตามอายุยังไม่มี background cleanup; ค่า retention ปัจจุบันเป็น policy target ไม่ใช่หลักฐานว่าลบอัตโนมัติแล้ว
- policy authorization ไม่รับรองความถูกต้องของ AI output; output ยังคง `machine_proposed` จนผ่าน review

## Quality gates

- external provider ไม่มี gate ต้องหยุดก่อน transport
- central remote switch, per-asset allow, classification allowlist และ size ceiling ต้องมี automated tests
- policy revoke ต้องไม่ลบ audit history
- logs และ CLI output ต้องไม่มี API key หรือ base64 media

