# Research Findings — รอบที่ 1

วันที่ศึกษา: 2 พฤศจิกายน 2026

## 1. pyCapCut เป็น draft adapter ไม่ใช่ renderer

**ยืนยันแล้ว:** เอกสาร upstream ระบุ workflow ว่าให้สร้าง draft แล้วเปิดใน CapCut เพื่อ export ด้วยมือ และ automated export ยังไม่รองรับ นอกจากนี้ upstream เตือนว่า API รุ่นถัดไปจะเปลี่ยนและแนะนำให้ตรึง `0.0.4` สำหรับ behavior ปัจจุบัน

**ผลต่อการออกแบบ:**

- Domain layer ต้องสร้าง `TimelinePlan` ที่ไม่ขึ้นกับ pyCapCut
- `PyCapCutAdapter` ต้องเป็น infrastructure boundary
- Export automation ไม่อยู่ใน acceptance criteria ระยะแรก
- Compatibility suite ต้องใช้ CapCut จริงและแยกจาก unit tests

แหล่งข้อมูล: [pyCapCut English README](https://github.com/GuanYixuan/pyCapCut/blob/main/english_readme.md), [demo.py](https://github.com/GuanYixuan/pyCapCut/blob/main/demo.py)

## 2. ffprobe เหมาะเป็น metadata authority

**ยืนยันแล้ว:** ffprobe ออกแบบให้แสดงข้อมูล stream/container แบบ machine-readable รองรับ JSON, stream selection, frame/packet inspection และ error reporting

**ผลต่อการออกแบบ:**

- Media Catalog ใช้ normalized ffprobe JSON เป็นหลักฐานต้นทาง
- เก็บ raw probe artifact ควบคู่ normalized model
- ตรวจ exit code และ ERROR section ห้ามอนุมานว่าไฟล์ปกติจาก extension
- duration ต้องระบุ source และ tolerance เพราะ container/stream duration อาจต่างกัน

แหล่งข้อมูล: [ffprobe documentation](https://ffmpeg.org/ffprobe.html)

## 3. Shot boundary detection ควรเป็น candidate generator

**ยืนยันแล้ว:** TransNet V2 เป็นงานและ implementation สำหรับ shot boundary detection ส่วนงาน AutoShot ชี้ว่าข้อมูล short video มีลักษณะเฉพาะและรายงานผลเหนือ TransNetV2 บนชุด SHOT ของตน

**ข้อสรุป:** ไม่มีเหตุผลให้เลือก model ถาวรก่อน benchmark กับคลิปจริงของโครงการ Shot detector ควรเสนอ candidate boundaries พร้อม confidence ไม่ใช่ตัดสิน editorial beats

แหล่งข้อมูล: [TransNetV2 repository](https://github.com/soCzech/TransNetV2/), [TransNet V2 paper](https://arxiv.org/abs/2008.04838), [AutoShot paper](https://arxiv.org/abs/2304.06116)

## 4. Speech recognition ต้องเก็บ timestamp และ uncertainty

**ยืนยันแล้ว:** OpenAI Whisper implementation รองรับ segment/word timestamp modes และมี thresholds สำหรับ no-speech, log probability และ compression ratio

**ผลต่อการออกแบบ:**

- Transcript model ต้องเก็บ segment timing, language, confidence indicators และ model version
- ชื่อเฉพาะ ภาษาไทย คำย่อ และตัวเลขต้องมี human/fact review
- Transcript ไม่ใช่ SSOT ของข้อเท็จจริง แต่เป็น evidence ที่ค้นหาได้

แหล่งข้อมูล: [OpenAI Whisper repository](https://github.com/openai/whisper), [transcribe.py](https://github.com/openai/whisper/blob/main/whisper/transcribe.py)

## 5. Image-text similarity ช่วยค้นภาพ แต่ไม่เท่ากับความเข้าใจเรื่อง

**ยืนยันแล้ว:** CLIP เข้ารหัสภาพและข้อความใน embedding space เพื่อจัดอันดับความสัมพันธ์ และเอกสาร/model card ระบุข้อจำกัดและความเสี่ยงด้าน bias

**ผลต่อการออกแบบ:**

- ใช้ embedding retrieval เพื่อสร้าง candidate shots
- ห้ามใช้ similarity score เป็นคำตัดสินด้านข้อเท็จจริง คุณภาพ หรือความเหมาะสมทางจริยธรรม
- Footage Curator ต้องรวม evidence จาก image, transcript, OCR, time และ brief

แหล่งข้อมูล: [OpenAI CLIP repository](https://github.com/openai/CLIP), [CLIP model card](https://github.com/openai/CLIP/blob/main/model-card.md), [CLIP paper](https://arxiv.org/abs/2103.00020)

## 6. Audio quality ต้องมี delivery profile

**ยืนยันแล้ว:** EBU R 128 กำหนดแนวคิด loudness normalization โดยใช้ programme loudness, Loudness Range และ maximum true peak; ค่าอ้างอิง broadcast หลักคือ -23 LUFS แต่ platform/งานแต่ละชนิดอาจต้องใช้ profile ต่างกัน

**ผลต่อการออกแบบ:**

- ห้าม hard-code -23 LUFS เป็นเป้าหมายของทุกงาน
- สร้าง `AudioDeliveryProfile` เป็น SSOT ตามช่องทางส่งมอบ
- Sound Director กำหนด creative dynamics; Technical QC ตรวจ compliance

แหล่งข้อมูล: [EBU R 128](https://tech.ebu.ch/publications/r128), [EBU loudness resources](https://tech.ebu.ch/loudness/)

## 7. Timed text ต้องเป็น model กลาง

**ยืนยันแล้ว:** WebVTT เป็นรูปแบบข้อความที่สัมพันธ์กับเวลาและรองรับ captions, subtitles, descriptions, chapters และ metadata

**ผลต่อการออกแบบ:**

- Subtitle domain model ต้องแยกจากรูปแบบ export
- รองรับการแปลงไป SRT/WebVTT/CapCut text โดยไม่สูญเสีย timing/provenance
- ตรวจ overlap, reading duration, language และ safe area แยกจาก ASR

แหล่งข้อมูล: [W3C WebVTT specification](https://www.w3.org/TR/webvtt1/)

## 8. ข้อสรุปเชิงสถาปัตยกรรม

ระบบที่เหมาะสมคือ evidence-first studio workflow:

```text
raw media -> technical evidence -> semantic candidates
          -> studio recommendations -> reviewed decisions
          -> provider-neutral timeline -> pyCapCut draft
          -> human/technical validation
```

AI ต้องอธิบายว่าตัดสินจากหลักฐานใด และการไม่มีหลักฐานต้องเปลี่ยนเป็นคำขอข้อมูลหรือ human review ไม่ใช่การแต่งเติม

