# Project Charter

## วิสัยทัศน์

สร้างทีมผลิตและตัดต่อวิดีโอเสมือนระดับสตูดิโอที่เข้าใจ insight และ intent ของผู้สั่งงาน วิเคราะห์และสังเคราะห์สื่อได้ ใช้วิจารณญาณจากผู้เชี่ยวชาญหลายฝ่าย ตรวจสอบกันเอง และสร้างโปรเจกต์ CapCut ที่แก้ไขต่อได้อย่างโปร่งใสและตรวจย้อนกลับได้

ระบบไม่ใช่เพียงตัวต่อคลิปอัตโนมัติ และไม่พยายามสร้าง CapCut ขึ้นใหม่ทั้งโปรแกรม แต่เป็นระบบตัดสินใจและเตรียมงานระดับ production ที่ใช้ CapCut เป็น finishing room

## ผู้มีส่วนร่วมหลัก

- ผู้สั่งงาน/เจ้าของข้อเท็จจริง: กำหนดเป้าหมาย ข้อเท็จจริง ข้อห้าม และอนุมัติงาน
- ทีมสร้างสรรค์เสมือน: วิเคราะห์ intent, insight, story, picture, sound, graphics และผู้ชม
- ทีมวิศวกรรม: ดูแล media pipeline, engines, pyCapCut adapter, configuration, observability และ tests
- CapCut operator: เปิดตรวจ ปรับละเอียด และ export งานจริง

## เป้าหมาย

1. รับบรีฟ คลิป ภาพ เสียง และข้อมูลประกอบเป็นโครงการเดียวกัน
   โดยมี `ProjectAssetBundle` ที่ระบุบทบาทและแหล่งที่มาของทุกไฟล์ รวมทั้ง text files ที่เป็นบรีฟ ข้อเท็จจริง สคริปต์ หรือคำบรรยาย
2. สำรวจสื่อด้วย Python, ffprobe, FFmpeg และโมเดลวิเคราะห์ที่เหมาะสม
3. สร้าง Creative Brief และ Timeline Plan ที่อธิบายเหตุผลได้
4. ให้ผู้เชี่ยวชาญเสมือนหลายฝ่ายเสนอ ทักท้วง และวิจารณ์งาน
5. ป้องกันภาพหรือข้อความที่สวยแต่ผิดข้อเท็จจริงหรือผิดเจตนา
6. สร้าง CapCut draft ผ่าน pyCapCut โดยแยกจาก domain logic
7. รองรับ UI ในอนาคตโดยไม่ย้ายตรรกะเข้า UI
8. ทดสอบอัตโนมัติได้ตั้งแต่ unit ถึง compatibility test
9. เก็บ configuration, decisions, artifacts และ provenance แบบมี SSOT

## ขอบเขตรอบแรก

- Media inventory และ metadata extraction
- Asset Intake และการตรวจความสมบูรณ์/บทบาท/สิทธิของ clips, audio, pictures และ text files
- Proxy, thumbnail, audio extraction และ technical inspection
- โครงสร้าง domain models กลาง
- Intent/creative/story workflow ระดับ prototype
- Timeline Plan และ validation
- pyCapCut `0.0.4` adapter
- CapCut compatibility proof กับ `9.7.0.4153`
- CLI/test harness ก่อน UI

## นอกขอบเขตรอบแรก

- การรับรองว่า AI ตัดต่อได้ระดับโลกโดยไม่มีมนุษย์ตรวจ
- การ export จาก CapCut แบบอัตโนมัติ
- UI production-ready
- การแก้ไขไฟล์ CapCut งานจริงที่ไม่มีสำเนาปลอดภัย
- การเลือก AI provider ถาวรก่อน benchmark กับสื่อไทยจริง

## หลักการที่ห้ามละเมิด

- ผู้ใช้เป็นเจ้าของ intent และข้อเท็จจริงสูงสุด
- Fact, ethics และ technical safety สามารถหยุด workflow ได้
- AI output เป็นข้อเสนอพร้อม evidence/confidence ไม่ใช่ข้อเท็จจริงโดยอัตโนมัติ
- Engines ไม่เรียกกันโดยตรง การประสานงานผ่าน orchestrator และ typed contracts
- UI ไม่เรียก FFmpeg หรือ pyCapCut โดยตรง
- pyCapCut เป็น adapter ไม่ใช่ domain model
- path และค่าร่วมต้องมาจาก typed central configuration
- secret ห้ามเก็บใน TOML ที่ commit เข้า repository
- ทุก draft ที่สร้างต้องมี project ID, job ID, engine version และ decision history

## นิยามความสำเร็จระยะแรก

ระบบผ่านระยะแรกเมื่อ:

1. ตรวจ environment และ media fixture ได้แบบ deterministic
2. สร้าง Timeline Plan จาก fixture และ validate ได้
3. สร้าง CapCut draft ใหม่โดยไม่เขียนทับงานจริง
4. เปิด draft ใน CapCut `9.7.0.4153` ได้
5. วิดีโอ ภาพ เสียง และข้อความยังแยกชั้นแก้ไขได้
6. ปิดและเปิด draft ใหม่ได้โดยองค์ประกอบไม่สูญหาย
7. export ด้วย CapCut ด้วยมือแล้วผลตรงกับ Timeline Plan ภายใน tolerance ที่กำหนด
8. unit/integration tests ไม่ต้องเปิด CapCut ยกเว้น compatibility suite ที่แยกไว้

