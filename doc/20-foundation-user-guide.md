# Foundation User Guide

ประเภท: How-to guide  
ผู้อ่าน: นักพัฒนา/ผู้ทดสอบ MTCapcut  
เป้าหมาย: ตรวจ environment, รับชุด assets, ดู SSOT และสร้าง draft ทดสอบโดยไม่เขียนทับงานเดิม

## 1. ตรวจ environment

```powershell
Set-Location 'D:\dev\MTCapcut'
& '.\.venv\Scripts\python.exe' -m mtcapcut doctor
```

exit code `0` หมายถึง dependency ที่ foundation ต้องใช้ผ่านทั้งหมด รายงาน `workspace.exists=false` ไม่ใช่ failure เพราะ CLI สร้าง workspace เมื่อลงทะเบียน project ครั้งแรก

## 2. เตรียม manifest ของ assets

สร้าง JSON array โดย path เป็น relative ต่อ manifest:

```json
[
  {"path": "brief.txt", "role": "brief", "rights_status": "owned"},
  {"path": "clip.mp4", "role": "footage", "rights_status": "owned"},
  {"path": "music.mp3", "role": "music", "rights_status": "licensed"},
  {"path": "photo.jpg", "role": "picture", "rights_status": "owned"}
]
```

อย่าระบุ `owned` หรือ `licensed` หากยังไม่มีหลักฐานสิทธิ ใช้ `unknown` แล้วส่ง human review

## 3. รับชุด assets เข้า SSOT

```powershell
& '.\.venv\Scripts\python.exe' -m mtcapcut ingest-bundle demo 'D:\media\assets.json'
& '.\.venv\Scripts\python.exe' -m mtcapcut assets demo
```

ฐานข้อมูลอยู่ที่ `workspace\demo\understanding.sqlite3` การรับซ้ำไฟล์เดิมใช้ logical asset/version เดิม; เมื่อเนื้อหาเปลี่ยนจะสร้าง version ใหม่และ current observations เดิมถูกกันออกโดยไม่ลบประวัติ

## 4. ดูหลักฐานตามเวลา

```powershell
& '.\.venv\Scripts\python.exe' -m mtcapcut timeline demo ASSET_ID
```

รายการนี้เป็น observations ไม่ใช่ข้อสรุปที่ยืนยันแล้ว Claims ต้องอ้าง observation IDs และผ่าน review ตามระดับความเสี่ยง

## 5. สร้าง draft ใน sandbox

โฟลเดอร์ output ต้องมีไฟล์ `.mtcapcut-draft-sandbox` และชื่อ draft ต้องยังไม่มีอยู่:

```powershell
New-Item -ItemType Directory -Path '.\draft-sandbox'
New-Item -ItemType File -Path '.\draft-sandbox\.mtcapcut-draft-sandbox'
& '.\.venv\Scripts\python.exe' -m mtcapcut create-draft demo '.\plan.json' '.\draft-sandbox' 'demo-001'
```

ตัวอย่าง `plan.json` ขั้นต่ำ (path ของ media เป็น relative ต่อไฟล์ plan):

```json
{
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "segments": [
    {
      "kind": "video",
      "start_us": 0,
      "duration_us": 3000000,
      "track": "main",
      "asset_id": "clip-001",
      "source_path": "clip.mp4",
      "source_start_us": 0,
      "rationale": "opening shot"
    },
    {
      "kind": "text",
      "start_us": 0,
      "duration_us": 2000000,
      "track": "titles",
      "text": "รายงานความคืบหน้า"
    }
  ]
}
```

adapter ไม่เขียนลง CapCut Drafts จริงโดยตรง การนำ draft ไปทดสอบกับ CapCut ต้องใช้ชื่อเฉพาะ, ตรวจ target ว่าไม่อยู่แล้ว และห้าม overwrite

## 6. รัน regression tests

```powershell
& '.\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

ชุดทดสอบสังเคราะห์พิสูจน์กลไก ไม่ได้พิสูจน์คุณภาพการเล่าเรื่อง ความถูกต้องของ ASR/OCR หรือระดับ world-class
