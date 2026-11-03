# Source Register

วันที่ตรวจ: 2 พฤศจิกายน 2026

| ID | แหล่งข้อมูล | ประเภท | ใช้ยืนยัน | ข้อจำกัด |
|---|---|---|---|---|
| SRC-001 | [pyCapCut English README](https://github.com/GuanYixuan/pyCapCut/blob/main/english_readme.md) | Upstream repository | workflow, version pin, export limitation, feature matrix | main branch เปลี่ยนได้ ต้องเทียบกับ tag/package 0.0.4 |
| SRC-002 | [pyCapCut demo.py](https://github.com/GuanYixuan/pyCapCut/blob/main/demo.py) | Upstream example | draft creation pattern | ตัวอย่าง main อาจเปลี่ยนจาก 0.0.4 |
| SRC-003 | [ffprobe documentation](https://ffmpeg.org/ffprobe.html) | Official documentation | machine-readable probe, JSON, stream/frame options | behavior บางส่วนขึ้นกับ build/format |
| SRC-004 | [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) | Official documentation | filter capabilities | ต้องทดสอบกับ build ที่ติดตั้ง |
| SRC-005 | [TransNetV2 repository](https://github.com/soCzech/TransNetV2/) | Research implementation | shot boundary candidate model | ไม่ใช่ editorial model |
| SRC-006 | [TransNet V2 paper](https://arxiv.org/abs/2008.04838) | Research paper | method/benchmark context | benchmark อาจไม่แทนคลิปของโครงการ |
| SRC-007 | [AutoShot paper](https://arxiv.org/abs/2304.06116) | Research paper | short-video shot dataset and results | ต้อง benchmark กับข้อมูลจริง |
| SRC-008 | [OpenAI Whisper](https://github.com/openai/whisper) | Primary model repository | transcription and timestamps | ภาษา/ชื่อเฉพาะต้องประเมินจริง |
| SRC-009 | [OpenAI CLIP](https://github.com/openai/CLIP) | Primary model repository | image-text retrieval | similarity ไม่ใช่ factual proof |
| SRC-010 | [CLIP model card](https://github.com/openai/CLIP/blob/main/model-card.md) | Model card | limitations and intended use | ไม่ครอบคลุม model อื่น |
| SRC-011 | [EBU R 128](https://tech.ebu.ch/publications/r128) | Industry recommendation | loudness concepts/reference | ไม่ใช่ target เดียวสำหรับทุก platform |
| SRC-012 | [W3C WebVTT](https://www.w3.org/TR/webvtt1/) | Web standard | timed text model/format | CapCut import behavior ต้องทดสอบแยก |
| SRC-013 | [TOML v1.0.0](https://toml.io/en/v1.0.0) | Language specification | TOML syntax/UTF-8 | project schema เป็นความรับผิดชอบของเรา |
| SRC-014 | [Python tomllib](https://docs.python.org/3/library/tomllib.html) | Official Python docs | parsing support and no write API | Python-version behavior ต่างกันได้ |
| LOC-001 | `pip show pycapcut` | Local observation | installed version 0.0.4 | เฉพาะ environment ปัจจุบัน |
| LOC-002 | `ffmpeg -version`, `ffprobe -version` | Local observation | installed build and libraries | ไม่รับรองทุก codec/path |
| LOC-003 | CapCut `ProductInfo.xml` | Local observation | active version 9.7.0.4153 | ไม่รับรอง draft compatibility |
| SRC-015 | [Motion Picture Editors Guild — post-production community](https://www.editorsguild.com/Join) | Professional guild | สาขาวิชาชีพในทีม post-production | รายการวิชาชีพ ไม่ใช่ workflow specification |
| SRC-016 | [Avid professional editing workflow](https://www.avid.com/resource-center/video-editing-workflow) | Professional vendor guidance | planning, media organization, editorial, finishing, collaboration | มีบริบทผลิตภัณฑ์ของผู้ขาย |
| SRC-017 | [Avid Media Composer professional architecture](https://apps.avid.com/mediacomposerfirst/) | Professional vendor documentation | media identity, conflict-free collaboration, pipeline fidelity | ไม่ใช่มาตรฐานเปิด |
| SRC-018 | [BBC Editorial Guidelines](https://downloads.bbc.co.uk/guidelines/editorialguidelines/pdfs/bbc-editorial-guidelines-whole-document.pdf) | Broadcaster editorial policy | accuracy, fairness, privacy, harm, editorial escalation | ใช้ปรับตามประเภทงาน ไม่ใช่ทุกงานเป็นข่าว |
| SRC-019 | [BBC stills and photographs editorial policy](https://downloads.bbc.co.uk/guidelines/editorialguidelines/pdfs/stills-photographs.pdf) | Broadcaster editorial policy | context, privacy, harm and image integrity | เอกสารเฉพาะภาพนิ่งแต่หลักการใช้กับการคัดภาพได้ |
| SRC-020 | [ACES overview](https://acescentral.com/) | Academy/industry color framework | color fidelity and managed interchange | การใช้จริงขึ้นกับ pipeline และ CapCut capability |
| SRC-021 | [ACES metadata specification](https://docs.acescentral.com/amf/specification/) | Industry specification | การรักษา color decisions/metadata ข้ามขั้นตอน | pyCapCut/CapCut support ต้องทดสอบ |
| SRC-022 | [EBU Tech 3343](https://tech.ebu.ch/docs/tech/tech3343.pdf) | Industry production guideline | loudness production and true-peak practice | delivery profile ต้องปรับตามช่องทาง |
| SRC-023 | [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | Web accessibility standard | captions and time-based media accessibility | compliance target ต้องกำหนดตามช่องทางเผยแพร่ |
| SRC-024 | [W3C Understanding Captions](https://www.w3.org/WAI/WCAG21/Understanding/captions-prerecorded.html) | W3C explanatory guidance | captions include dialogue, speaker and meaningful sound | ไม่กำหนดรูปแบบสไตล์ของ CapCut |
| SRC-025 | [Kanban Guide 2025](https://kanbanguides.org/wp-content/uploads/2025/05/Kanban-Guide-2025-05.pdf) | Official Kanban guide | Definition of Workflow, WIP, SLE และ flow metrics | ต้องปรับ policies จากข้อมูลจริงของทีม |
| SRC-026 | [Kanban Method](https://kanban.university/resources/kanbanmethodinfographic/) | Official method guidance | visualize, limit WIP, feedback loops, evolutionary improvement | ไม่กำหนด board สำหรับโครงการนี้โดยตรง |
| SRC-027 | [Agile Manifesto principles](https://agilemanifesto.org/principles) | Primary Agile principles | frequent delivery, response to change, working software, reflection | ไม่ใช่ process prescription |
| SRC-028 | [Video-MME](https://arxiv.org/abs/2405.21075) | Research paper/benchmark | multimodal short/medium/long video evaluation | benchmark ไม่แทนงานจริงของ MT |
| SRC-029 | [LongVideoBench](https://proceedings.neurips.cc/paper_files/paper/2024/hash/329ad516cf7a6ac306f29882e9c77558-Abstract-Datasets_and_Benchmarks_Track.html) | Peer-reviewed benchmark | long-context interleaved video-language understanding | ต้องประเมินภาษาไทยและโดเมนจริง |
| SRC-030 | [PaddleOCR multilingual PP-OCRv5](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html) | Official model documentation | multilingual OCR และ Thai model selection | dependency/Python compatibility ต้องทดลอง |
| SRC-031 | [Adobe EditDuet](https://research.adobe.com/publication/editduet-a-multi-agent-system-for-video-non-linear-editing/) | Primary research | editor–critic multi-agent video editing | research prototype ไม่ใช่ production guarantee |
| SRC-032 | [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) | Government framework | lifecycle AI governance and risk management | ต้องแปลงเป็น controls เฉพาะโครงการ |
| SRC-033 | [C2PA specifications](https://spec.c2pa.org/specifications/) | Industry specification | media provenance assertions, claims, ingredients and signatures | provenance ไม่พิสูจน์ว่าเนื้อหาจริง และ metadata อาจถูกถอด |
| SRC-034 | [OpenTelemetry](https://opentelemetry.io/docs/) | Official observability documentation | vendor-neutral traces, metrics และ logs | backend/retention ต้องออกแบบแยก |
| SRC-035 | [OpenRouter Chat Completions API](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request) | Official provider documentation | OpenAI-compatible endpoint, Bearer auth, streaming/non-streaming | model/provider capability และ privacy policy ต้องตรวจแยก |
| SRC-036 | [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility) | Official local AI documentation | local `/v1/chat/completions` และ vision-compatible examples | รองรับเพียง subset; model capability แตกต่างกัน |
| SRC-037 | [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) | Official project documentation | OpenAI-compatible local server/health/model APIs | multimodal/features บางส่วนยัง experimental |

## กฎการใช้แหล่งข้อมูล

1. ใช้เอกสารทางการ/source code/งานวิจัยก่อนบทความสรุป
2. บันทึก version/date และแยก fact จาก inference
3. Community issue ใช้เป็นสัญญาณเพื่อสร้าง test ไม่ใช้เป็นข้อยืนยันเพียงแหล่งเดียว
4. หากเอกสารกับเครื่องจริงขัดกัน ให้บันทึกทั้งสองและสร้าง reproducible experiment
5. เพิ่ม source ID ใน ADR หรือ research note ทุกครั้งที่ตัดสินใจด้านสถาปัตยกรรมจากหลักฐานภายนอก

