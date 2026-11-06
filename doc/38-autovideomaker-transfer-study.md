# AutoVideoMaker → MTCapcut: research transfer and implementation

อัปเดต: 6 พฤศจิกายน 2026

## ขอบเขตที่ตรวจ

ตรวจ repository `bonciarello/AutoVideoMaker` ที่ commit `31250d9`, README, `src/cleanup_rules.py`, `src/cleanup.py`, `src/silence_analysis.py`, `src/transcription.py`, `src/capcut_export.py` และ `tools/evaluate_cleanup.py` โดยเทียบกับโค้ด MTCapcut ใน `main` และ [PR #1 ของโครงการเรา](https://github.com/idev006/MTCapcut/pull/1) ต้นทางที่ตรวจ **ไม่พบ LICENSE/COPYING/NOTICE** จึงนำมาเฉพาะแนวคิด ไม่คัดลอกโค้ดต้นทาง และไม่ใช้ตัวสร้าง CapCut draft ของต้นทางแทน pyCapCut บน Windows

## สิ่งที่เรียนรู้และการตัดสินใจ

| แนวคิดจากต้นทาง | ผลประเมิน | วิธีใช้ใน MTCapcut |
|---|---|---|
| ตัดตาม word timestamps พร้อม margin | ลดโอกาสตัดกลางคำ แต่ ASR อาจผิด | เก็บคำ/เวลาใน SSOT; ยังไม่สั่งตัดอัตโนมัติ |
| FFmpeg silence fallback | มีประโยชน์เมื่อไม่มี ASR แต่ความเงียบเชิงระดับเสียงไม่บอกเจตนา | งานถัดไป: เทียบ word gap กับ acoustic silence และรักษา ambience/music |
| rule หา false start, repeat, retake, cue word | ช่วยคัดจุดตรวจ แต่ภาษาไทย/คำเน้นอาจทำให้ false positive | รอบนี้รับเฉพาะ pause และ adjacent repeat เป็นข้อเสนอให้ review; no auto-delete |
| transcript cache (`words.json`) | ลดการเรียก ASR ซ้ำ; upstream cache ใช้ชื่อ/ขนาด/ระยะเวลา | ใช้ asset version/content hash ของ Understanding Map เป็นขอบเขต; CLI reuse word rows รุ่นปัจจุบัน |
| CapCut/EDL export | ต้นทางระบุ manual check บน macOS CapCut 9.4 | ใช้ pyCapCut adapter และ sandbox ที่ทดสอบบน Windows ของเรา |
| benchmark เทียบงานตัดมือ | วัด false deletion ได้ดีกว่าจำนวน suggestion | เตรียมชุดคลิปไทยที่มี label, วัดเวลาเสียงที่เสนอผิดและช่วงที่พลาด |

แหล่งต้นทาง: [README](https://github.com/bonciarello/AutoVideoMaker), [cleanup rules](https://github.com/bonciarello/AutoVideoMaker/blob/main/src/cleanup_rules.py), [silence analysis](https://github.com/bonciarello/AutoVideoMaker/blob/main/src/silence_analysis.py), [transcription/cache](https://github.com/bonciarello/AutoVideoMaker/blob/main/src/transcription.py), [evaluation](https://github.com/bonciarello/AutoVideoMaker/blob/main/tools/evaluate_cleanup.py)

## ส่วนที่พัฒนาแล้ว

- นำ `take_review.py` และ tests ซึ่งเป็นโค้ดเขียนใหม่ใน PR #1 ของ MTCapcut มาตรวจและต่อยอดใน `main`; ย้ายเอกสารจากเลข 37 เป็นเลข 38 เพื่อไม่ชนกับเอกสาร V22
- `FasterWhisperEar.transcribe_detail` เก็บ word timestamps และ probability ตาม asset source time; `transcribe_and_store` ลงทะเบียน `speech` และ `speech_word` observations ภายใต้ asset version เดียวกัน
- `suggest_for_asset` อ่านคำจาก **current asset version** แล้วคืน `TakeSuggestion` ที่มี asset ID, source interval และ evidence observation IDs; ไม่แก้ไฟล์, timeline หรือ draft
- `build_studio_snapshot` ไม่ส่ง `speech_word` ทั้งชุดไป Studio Council; segment speech ยังคงเข้าบรีฟ/คำแนะนำตามเดิม
- CLI `transcribe-asset PROJECT_ID ASSET_ID` ใช้ FFmpeg extract และ faster-whisper ใน `.venv`/central config, reuse current word evidence เมื่อ asset hash และค่าถอดเสียงตรงกัน; `review-takes PROJECT_ID ASSET_ID` แสดงข้อเสนอ JSON หรือ `no_word_transcript`

ตัวอย่าง (ต้องตั้ง `[local_ear].enabled = true` ใน `config.toml` ก่อน):

```powershell
& 'D:\dev\MTCapcut\.venv\Scripts\python.exe' -m mtcapcut transcribe-asset PROJECT_ID ASSET_ID
& 'D:\dev\MTCapcut\.venv\Scripts\python.exe' -m mtcapcut review-takes PROJECT_ID ASSET_ID
```

## Gate และขีดจำกัด

| Gate | สถานะ | หลักฐาน/งานค้าง |
|---|---|---|
| Source/license review | PASS สำหรับการศึกษา; BLOCKED สำหรับ vendoring | ไม่พบ license grant ใน commit ที่ตรวจ |
| Pure take rules + SSOT word handoff | PASS | unit/integration fake ASR, asset-version invalidation และ full suite 135 tests บน Windows `.venv` |
| CLI read-only smoke | PASS | `review-takes` บน asset เพลงที่ยังไม่มี word transcript คืน `no_word_transcript`; ไม่ใช่การทดสอบคุณภาพ ASR |
| Thai real speech benchmark | NOT RUN | ไม่มีคลิปพูดพร้อมคำเฉลยที่อนุญาตให้ใช้; เพลง/คลิปไร้เสียงใน `road-report-001` ใช้ประเมินไม่ได้ |
| Approval → timeline cut → receipt → pyCapCut | NOT RUN | ยังต้องออกแบบการยืนยันคำแนะนำและการ rollback ก่อนตัดจริง |
| Acoustic silence cross-check | NOT RUN | word gap ไม่ใช่หลักฐานว่าช่วงนั้นเงียบ |

หากเปลี่ยนโมเดล/ภาษา/VAD โดยที่ asset version ยังเดิม CLI จะปฏิเสธการรวมผลถอดเสียงคนละค่ากำหนดใน transcript เดียว ต้องทำ workflow revision/replace ที่มี provenance ก่อนเปิดการ re-transcribe โดยตั้งค่าใหม่

การทำข้อเสนอให้ตัดเป็นการวิเคราะห์ก่อนตัดต่อเท่านั้น ระบบยังไม่ควรลบคำซ้ำโดยอัตโนมัติ เพราะคำซ้ำอาจเป็นการเน้นความหมาย ชื่อบุคคล หรือการพูดหลายคน งานต่อไปใน [Kanban](./14-initial-kanban-backlog.md) คือ review/approval receipts, FFmpeg acoustic comparison และ benchmark กับคลิปพูดภาษาไทยจริง
