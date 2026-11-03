# AI Media Engine Research Architecture

วันที่ศึกษา: 2 พฤศจิกายน 2026  
สถานะ: Research architecture — ยังไม่เลือก production models

## ข้อสรุป

Video understanding ต้องไม่เป็น engine เดียวและไม่ควรอาศัย fixed frame sampling เพียงอย่างเดียว งาน benchmark อย่าง Video-MME และ LongVideoBench แสดงความสำคัญของช่วงเวลาหลายขนาด เสียง subtitles และ long-context reasoning [SRC-028, SRC-029]

ระบบจึงต้องสร้าง evidence บน timebase เดียวก่อน reasoning และแยก `Observation` ออกจาก `Claim`

สำหรับเครื่องเป้าหมาย RAM 8 GB และไม่มี GPU แยก ให้ใช้แนวทาง **Lightweight Hybrid, Analyze Once**: local tools ทำ fingerprint/probe/extraction/quality checks และ cache; cloud multimodal ใช้เฉพาะข้อมูลที่ผ่านการคัดเลือกและเฉพาะคำถามที่ต้องตีความความหมาย ระบบต้อง provider-agnostic และยังไม่กำหนด Gemini, OpenAI, OpenRouter หรือโมเดลใดเป็น production default จนกว่าจะผ่าน benchmark เดียวกัน

## Execution profile: RAM 8 GB / no discrete GPU

| Stage | Default execution | Budget policy |
|---|---|---|
| hash, ffprobe, media validation | local, streaming | ไม่โหลด media ทั้งไฟล์เข้า RAM |
| shot candidates / frame extraction | local FFmpeg; process ทีละ asset | จำกัด frame cache และ worker = 1 เริ่มต้น |
| speech extraction | local WAV chunks | แบ่งช่วงและลบ temporary artifacts ตาม retention |
| ASR/OCR/vision model | benchmark local-small เทียบ cloud | เลือกจาก accuracy/cost/latency/privacy ไม่เลือกจากชื่อโมเดล |
| semantic reasoning | cloud เฉพาะ evidence package หรือ local fallback | ห้ามส่ง restricted assets หาก policy ไม่อนุญาต |
| persistent memory | SQLite + content-addressed artifacts | cache key รวม asset/config/model version |
| CapCut generation | local pyCapCut adapter | สร้าง draft revision ใหม่ ไม่ overwrite |

Cloud request ต้องส่ง evidence package ที่เล็กที่สุดเท่าที่ตอบโจทย์ได้ เช่น transcript ช่วงที่เกี่ยวข้อง, contact sheet, selected frames และคำถามเฉพาะ ห้ามส่งวิดีโอเต็มโดยอัตโนมัติ การวิเคราะห์ซ้ำทำได้เฉพาะเมื่อ asset hash, extractor/model/config หรือคำถามเปลี่ยน

## ตา หู และสมองของทีม

`Python scripts` เป็นตัวเชื่อมไฟล์ เครื่องมือ และ AI models เข้ากับ contracts ของระบบ ส่วน Codex หรือ AI provider อื่นเป็น implementation ทางเลือกของความสามารถด้านการตีความและให้เหตุผล ต้องระบุ model/version และเปลี่ยน provider ได้โดยไม่เปลี่ยน domain contracts

| ความสามารถ | รับข้อมูล | ส่งผลลัพธ์ที่ตรวจย้อนกลับได้ | เกณฑ์พิสูจน์ |
|---|---|---|---|
| ตา | clips, pictures, sampled frames | วัตถุ บุคคล การกระทำ ข้อความในภาพ คุณภาพภาพ และเวลา/ตำแหน่งต้นทาง | ตรวจเทียบ annotation ของมนุษย์ รวมเหตุการณ์สั้นและบริบทที่คล้ายกัน |
| หู | เสียงจาก clips, mp3 | คำพูด ผู้พูดโดยประมาณ เหตุการณ์เสียง ดนตรี ความดัง และช่วงเวลา | ตรวจคำไทย ชื่อเฉพาะ ตัวเลข timing และ false positives |
| ผู้อ่านบรีฟ | text files และข้อมูลที่ผู้ใช้ยืนยัน | intent, facts, constraints, candidate captions และสิ่งที่ยังไม่ชัด | แยกคำสั่ง ข้อเท็จจริง และข้อความสำหรับขึ้นจอได้ |
| สมองเฉพาะฝ่าย | observations จากทุก modality + brief | claims, story beats, shot recommendations, objections และ edit decisions พร้อมหลักฐาน | factual review, temporal QA และ blind editorial review |

`ProjectAssetBundle` เป็น input contract สำหรับ clips, mp3, pictures และ text files แต่ละรายการมี stable asset ID, path, hash, role, source, rights และสถานะ ingest ข้อความต้องประกาศบทบาท เช่น `brief`, `confirmed_facts`, `script`, `captions`, `on_screen_copy` หรือ `restrictions` ระบบต้องถามผู้ใช้เมื่อจำแนกบทบาทไม่ได้อย่างมั่นใจ

การเห็นเฟรมหรือถอดคำพูดถูกต้องยังไม่เพียงพอที่จะสรุปสถานะเหตุการณ์ เช่น ภาพช่างทำงานไม่ยืนยันว่าโครงการเสร็จแล้ว `Observation` จึงต้องผ่าน temporal/context reasoning และ Fact Editor ก่อนเป็น `Claim` ที่นำไปสื่อสารในคลิป

## Evidence pipeline

```text
MediaAsset + content hash
  -> AssetIntakeEngine (role, rights, file integrity)
  -> MediaProbeEngine
  -> ShotCandidateEngine + AdaptiveFrameSamplingEngine
  -> ASREngine + OCREngine + AudioEventEngine
  -> TemporalEvidenceEngine
  -> SemanticIndexEngine
  -> MultimodalUnderstandingEngine
  -> FootageJudgment / Story / Editorial Engines
  -> CriticEngine + HumanApprovalGate
  -> TimelinePlan
```

## Engine boundaries

- `MediaProbeEngine`: technical metadata/raw ffprobe; ไม่ตีความเนื้อหา
- `AssetIntakeEngine`: ตรวจชนิดจริง ความสมบูรณ์ hash บทบาท และสิทธิของไฟล์; ส่ง `ProjectAssetBundle` และข้อสงสัยกลับผู้ใช้
- `ShotCandidateEngine`: boundaries/confidence/model version; ไม่ใช่ editorial cut
- `AdaptiveFrameSamplingEngine`: เลือกเฟรมตาม shots/motion/policy; ไม่รับรองว่าเห็นทุกเหตุการณ์
- `ASREngine`: timed speech observations; ชื่อเฉพาะ/ตัวเลขยังไม่ใช่ facts
- `OCREngine`: polygon/text/confidence/frame/time/language; ต้อง benchmark ภาษาไทย [SRC-030]
- `AudioEventEngine`: speech/music/noise/event candidates
- `TemporalEvidenceEngine`: align modalities เป็น microsecond timebase
- `SemanticIndexEngine`: retrieval เท่านั้น ไม่ตัดสินความจริง
- `MultimodalUnderstandingEngine`: สร้าง claims ที่อ้าง EvidenceRefs
- `FootageJudgmentEngine`: ประเมินคุณภาพ ความหมาย brief alignment และ risks
- `EditDecisionEngine`: เสนอ source/timeline ranges พร้อม alternatives
- `CriticEngine`: review อิสระ; ไม่เป็น judge เพียงตัวเดียว [SRC-031]
- `ProvenanceEngine`: graph ของ assets, derivatives, tools, models, configs และ approvals
- `HumanApprovalGate`: บังคับ review ตาม risk tier [SRC-032]

## Shared contracts

```text
EvidenceRef(
  asset_id, start_us, end_us, modality,
  extractor_id, extractor_version, confidence, artifact_hash
)

Observation(
  observation_id, evidence_refs, text_or_label,
  confidence, assumptions, status
)

Claim(
  claim_id, claim_type, statement,
  evidence_refs, confidence, assumptions, fact_status
)

EditDecision(
  source_range, timeline_range, purpose,
  rationale, evidence_refs, alternatives, risks
)

ReviewFinding(
  severity, dimension, evidence_refs,
  requested_action, owner, disposition
)
```

## Benchmark plan

- Shot: F1 ภายใน frame tolerance แยก hard/gradual cuts
- ASR: CER/WER, Thai named-entity/number accuracy, timestamp error
- OCR: CER/word accuracy, polygon IoU, Thai overlay/signage set
- Retrieval: precision@k, nDCG, duplicate rate
- Temporal QA: short/medium/long และ ablation video-only vs audio/subtitle
- Editorial constraints: brief coverage, duration, contradictions, unsupported claims
- Creative quality: blind pairwise review โดยผู้ตัดต่อที่มีประสบการณ์ พร้อม inter-rater agreement
- Production: edit time, revision count, critical fact errors, override rate, latency/cost

LLM judge ใช้เป็นสัญญาณหนึ่งได้ แต่ห้ามเป็นผู้ตัดสินเพียงตัวเดียว

## End-to-end proof ที่ต้องมี

ชุดทดสอบหนึ่งงานต้องมีคลิปที่แสดงการปฏิบัติงาน ภาพนิ่งจากคนละวัน MP3 ที่มีคำพูดภาษาไทย และ text file ที่ยืนยันสถานะว่า “กำลังดำเนินการ” ระบบต้องระบุเวลาและ asset ของสิ่งที่เห็น/ได้ยิน สรุปว่าภาพไม่พิสูจน์การแล้วเสร็จ เสนอช็อตพร้อมเหตุผล และไม่สร้างข้อความ “แล้วเสร็จ” ใน Timeline Plan หากไม่มีข้อเท็จจริงยืนยัน

## Provenance

Internal provenance graph เป็น requirement แรก: asset hash, origin, derivatives, engine/tool/model/config versions, edit decisions และ approvals C2PA เป็น future adapter สำหรับ standardized assertions/claims/ingredients แต่ provenance ยืนยันประวัติและ integrity ไม่ได้ยืนยันว่าความหมายของเนื้อหาจริง [SRC-033]

## Promotion gate ของ model/engine

- frozen benchmark set และ data rights ผ่าน
- baseline และ candidate ใช้ environment/config ที่บันทึกได้
- ไม่มี regression ใน critical factual/temporal metrics
- cost/latency อยู่ใน budget
- privacy/security review ผ่าน
- model card, dependency/license และ known failures บันทึกครบ
- canary evaluation ผ่านก่อนเปลี่ยน default

## ความเสี่ยง

- Python 3.14 อาจไม่รองรับ dependencies บางตัว
- sparse sampling พลาดเหตุการณ์สั้น
- ASR/OCR hallucination และชื่อไทยผิด
- temporal ordering ผิดแม้ frame recognition ถูก
- confidence ไม่ calibrated
- editor/critic ใช้โมเดลเดียวกันอาจล้มเหลวแบบสัมพันธ์กัน
- dataset/domain bias
- biometrics/privacy และ external provider retention
- model drift/version changes
- provenance metadata อาจถูก export/platform ถอดออก

