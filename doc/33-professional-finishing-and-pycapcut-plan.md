# Professional Finishing and pyCapCut Integration

วันที่: 4 พฤศจิกายน 2026

## Outcome

ระบบเพิ่ม `ProfessionalFinishingEngine` ซึ่งให้ OpenRouter Senior Finishing Editor เลือก treatment จาก allowlist แบบ typed และมี rationale ต่อ segment จากนั้น `capcut_adapter` materialize ลง editable CapCut draft โดย Codex ไม่เลือก effect หรือ transition ให้ชิ้นงาน

## Contract v1

- New OpenRouter finishing: transitions `Mix`, `Overlay` หรือ `none`; filters `Soft_Grain`, `BW_2` หรือ `none`. Pinned pyCapCut 0.0.4 marks these resources `is_vip=false`. Older plans remain readable but a new plan cannot select a Pro resource.
- Motion: `locked`, `slow_push_in`, `slow_pull_out`
- Text animation: restrained intro/outro allowlist
- Multi-visual plan ต้องมี intentional transition อย่างน้อยหนึ่งจุดเพื่อให้ review transition craft ได้
- Filter intensity ใช้หน่วยเปอร์เซ็นต์และถูกจำกัด 10–45%; `none` ต้องเป็น 0
- Engine เปลี่ยนไม่ได้: timing, facts, text, assets หรือ music

## Live proof

- Draft: `MT_ROAD_REPORT_001_AUTONOMOUS_PRO_V2`
- Duration: 35,000,000 µs
- Tracks: video, audio, text
- Finishing: Swipe Left 800,000 µs; Enhance 30%/25%; Soft Light 20%; slow push-in; Wiping In/Out
- Saved materials: transitions 1, effects 3, material animations 1, videos 3, audio 1, text 1
- CapCut 9.7: draft discovered, opened and played successfully

## Compatibility finding

CapCut แสดง `Couldn't download filter` และ `Animation loss` สำหรับ resource บางรายการ แม้ draft schema ถูกอ่านได้ จึงแยกความสำเร็จเป็น:

- Draft/schema/timeline compatibility: PASS
- Transition material: PRESENT
- Filter and text-animation resource availability: PARTIAL
- Creative quality review: รอ feedback จากผู้ใช้

CapCut 9.8 เปิดร่าง V16 ความยาว 3 นาทีได้ แต่ Export แจ้งว่า `Swipe Left` เป็น Pro material ตาม [คำอธิบายของ CapCut](https://www.capcut.com/help/join-capcut-pro-for-exporting). จึงเปลี่ยน allowlist ของงานใหม่เป็นวัสดุที่ metadata ระบุว่าใช้ฟรี และตั้ง text animation เป็น `none` สำหรับงานยาว การเปิดและ export ร่างใหม่ยังต้องทดสอบจริง เพราะวัสดุฟรีอาจต้องดาวน์โหลดใน CapCut.
