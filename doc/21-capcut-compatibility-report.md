# CapCut Compatibility Report

ประเภท: Reference / test evidence  
วันที่ทดสอบ: 2 พฤศจิกายน 2026  
ขอบเขต: pyCapCut draft พื้นฐานกับ CapCut Desktop บนเครื่องพัฒนา

## Matrix

| รายการ | รุ่น/ค่า | ผล |
|---|---|---|
| Python | 3.14.0, project `.venv` | PASS |
| pyCapCut | 0.0.4 (adapter pin) | PASS |
| CapCut | 9.7.0.4153 | PASS ในขอบเขตนี้ |
| FFmpeg/ffprobe | build 2025-10-30 | PASS |
| Canvas | 1080×1920, 30 fps plan | PASS |
| Timeline | video 2 s + picture 1 s + MP3 3 s + Thai text 3 s | PASS |
| Draft discovery | `MT_AI_COMPAT_20261102_01` ปรากฏในหน้า Projects | PASS |
| Open/display timeline | media/text/audio tracks แสดงและ preview frame ได้ | PASS |
| Local export | H.264/AAC MP4 | PASS |

## Export evidence

- ไฟล์: `D:\dev\MTCapcut\workspace\compatibility-20261102-01\MT_AI_COMPAT_20261102_01.mp4`
- ffprobe: video H.264, 720×1280; audio AAC; duration `3.018005`; size `1,902,659` bytes
- CapCut export UI รายงาน 720p, 30 fps, H.264, MP4, Rec.709 SDR
- `Sync exported videos to space` ถูกปิดก่อน export และไม่ได้กด Share; ไม่ได้ทำ network capture จึงไม่ใช้ผลนี้รับรอง traffic อื่นของ CapCut

## Safety evidence

- adapter ต้องพบ `.mtcapcut-draft-sandbox`
- adapter ปฏิเสธชื่อไม่ปลอดภัยและ draft ที่มีอยู่แล้ว
- สร้าง draft ใน `D:\dev\MTCapcut\workspace` ก่อน
- คัดลอกไป CapCut Drafts ด้วยชื่อใหม่หลังตรวจว่า target อยู่ใต้ draft root และยังไม่มีอยู่
- ไม่ลบหรือเขียนทับ draft ของผู้ใช้

## สิ่งที่ผลนี้ยังไม่พิสูจน์

- edit → save → close → reopen หลังแก้ทุกชนิด
- transitions, effects, fonts, captions, speed ramps, keyframes, color, loudness และหลาย resolution/frame-rate
- compatibility กับ CapCut รุ่นอื่นหรือหลัง auto-update
- automatic export; pyCapCut สร้าง draft แต่ export ยังเป็นขั้น manual/desktop automation
- คุณภาพเชิงบรรณาธิการหรือความถูกต้องกับงานจริง

## วิธีสร้าง fixture ซ้ำ

ใช้ output/draft name ใหม่ทุกครั้ง:

```powershell
& 'D:\dev\MTCapcut\.venv\Scripts\python.exe' -m scripts.create_compatibility_fixture `
  'D:\dev\MTCapcut\workspace\compatibility-NEW' 'MT_AI_COMPAT_NEW'
```

ห้ามใช้ชื่อเดิมเพื่อหลีกเลี่ยงการ overwrite และต้องตรวจด้วย CapCut อีกครั้งหลังเปลี่ยน CapCut หรือ pyCapCut version
