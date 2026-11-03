# Environment Baseline

ตรวจเมื่อ 2 พฤศจิกายน 2026 จากเครื่องพัฒนา Windows ปัจจุบัน

## ยืนยันแล้ว

| รายการ | ค่าที่ตรวจพบ | หลักฐาน |
|---|---|---|
| Project root | `D:\dev\MTCapcut` | workspace ที่ผู้ใช้กำหนด |
| Python executable | `D:\dev\MTCapcut\.venv\Scripts\python.exe` | เรียกใช้งานสำเร็จ |
| Python | `3.14.0` 64-bit | `sys.version` |
| pyCapCut | `0.0.4` | `python -m pip show pycapcut` |
| pyCapCut package | `D:\dev\MTCapcut\.venv\Lib\site-packages\pycapcut` | `pycapcut.__file__` |
| FFmpeg root | `D:\libs\ffmpeg` | ผู้ใช้กำหนดและ binary ทำงานได้ |
| FFmpeg | `2025-10-30-git-00c23bafb0` | `ffmpeg -version` |
| ffprobe | build เดียวกับ FFmpeg | `ffprobe -version` |
| CapCut apps root | `C:\Users\acer\AppData\Local\CapCut\Apps` | ตรวจ directory จริง |
| CapCut installed | `9.6.0.4097`, `9.7.0.4153` | directory listing |
| CapCut active product | `9.7.0.4153` | `ProductInfo.xml` |
| Git repository | ยังไม่มี | `git status` คืนค่า not a git repository |

## pyCapCut surface ที่ติดตั้ง

แพ็กเกจ export ประเภทหลัก ได้แก่ `DraftFolder`, `ScriptFile`, `VideoSegment`, `AudioSegment`, `TextSegment`, `EffectSegment`, `FilterSegment`, `Timerange`, `TrackType` และ metadata สำหรับ transition, animation, mask และ filter

นี่เป็นหลักฐานว่า adapter สามารถสร้างโครงสร้าง draft และองค์ประกอบ timeline ได้ในระดับไลบรารี แต่ยังไม่ใช่หลักฐานว่า draft ทุกชนิดเปิดได้กับ CapCut `9.7.0.4153`

## ข้อสังเกตด้าน compatibility

- pyCapCut README แนะนำให้ตรึง `0.0.4` หากใช้ API ปัจจุบัน เพราะ `0.1.0` จะเปลี่ยน track API
- README ระบุให้เปิด draft ใน CapCut และ export ด้วยมือ
- ตารางความสามารถของ upstream บันทึก validation เป็นรายความสามารถ/รุ่น ไม่ได้รับประกันทุกเวอร์ชัน
- เครื่องนี้ใช้ Python 3.14 ซึ่งใหม่กว่าหลายไลบรารี AI; dependency compatibility ต้องตรวจเป็นรายแพ็กเกจ

## ยังไม่ยืนยัน

- ตำแหน่ง CapCut Drafts ที่ใช้งานจริง
- ความสามารถเปิด draft จาก pyCapCut `0.0.4` บน CapCut `9.7.0.4153`
- การแสดงข้อความไทย ฟอนต์ transition effect และ keyframe ทุกชนิด
- round-trip หลังเปิด บันทึก ปิด และเปิดใหม่
- export fidelity และ timing tolerance
- AI runtime/model ที่รองรับ Python 3.14 และ hardware เครื่องนี้

## ความเสี่ยงทันที

1. ห้ามสร้างหรือทดสอบด้วยชื่อ draft ที่ตรงกับงานจริง
2. ต้องสำรอง/ใช้ test draft folder ก่อน compatibility test
3. ห้ามผสมตัวอย่างจาก pyCapCut main/0.1.0 กับ API `0.0.4`
4. หาก AI dependencies ไม่รองรับ Python 3.14 อาจต้องสร้าง environment แยกสำหรับ model runtime โดยยังคง contracts เดิม

