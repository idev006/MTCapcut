# Deployment, UI Bridge and AI Provider Architecture

วันที่ตรวจ: 2 พฤศจิกายน 2026  
ประเภท: Explanation + Reference  
สถานะ: baseline contracts implemented; production streaming/retry/cost policy ยังเป็นงานถัดไป

## เป้าหมายสถาปัตยกรรม

1. ผู้ใช้ Windows เปิด `start.bat` จาก source workspace และตรวจระบบด้วย `doctor.bat` ได้
2. UI เป็น shell ที่เรียก application services/engines เท่านั้น ไม่แตะ FFmpeg, SQLite, AI HTTP หรือ pyCapCut โดยตรง
3. งานหนักรันนอก UI thread มี events, polling, callback, cancellation และ structured failure
4. engine เดิมสลับ OpenRouter หรือ local OpenAI-compatible server ได้ผ่าน provider contract เดียว
5. settings แบ่งหมวดและ validate ก่อน engine เริ่ม; secret อยู่ใน environment variable

## Component boundaries

```text
UI shell (future)
  │ submit / cancel / poll events
  ▼
Application services
  │ typed request/result
  ▼
EngineRunner ── JobHandle ── EngineEvent queue
  │
  ├── Media / Evidence / Editorial / QC engines
  ├── AIProvider contract
  │     ├── OpenRouter profile
  │     └── local_openai profile (Ollama / llama.cpp / compatible server)
  └── Adapters: FFmpeg / pyCapCut / SQLite
```

`EngineRunner.submit()` คืน `JobHandle` ทันที UI จึงไม่รอ engine ทำงาน `JobHandle.drain_events()` เหมาะกับ timer ของ UI; `on_event` และ `add_done_callback` มีไว้สำหรับ integration ที่เข้าใจ threading โดย callback อาจรันบน worker thread ดังนั้น UI toolkit ต้อง marshal กลับ main thread เอง

Cancellation เป็น cooperative: engine ที่ทำงานเป็นช่วงต้องเรียก `context.raise_if_cancelled()` ที่ safe checkpoint การกด cancel ไม่ควร terminate process ระหว่าง SQLite transaction หรือระหว่างเขียน draft

## Event contract

`EngineEvent` มี `job_id`, stable engine name, kind, monotonic sequence ภายใน job, UTC timestamp, message, progress 0–1 และ structured payload ชนิด event baseline คือ `started`, `progress`, `completed`, `failed`, `cancelled`

UI ต้องใช้ `job_id + sequence` สำหรับ deduplicate/order และไม่ parse log text เป็น state หาก UI poll ช้า events ยังคงอยู่ใน queue; bounded/persistent event store เป็นงานถัดไปก่อนงานหลายชั่วโมงระดับ production

## AI provider boundary

OpenRouter ใช้ OpenAI-compatible `POST /api/v1/chat/completions` และ Bearer API key ตามเอกสารทางการ ส่วน Ollama local รองรับ subset ของ OpenAI API ที่ `/v1/chat/completions`; llama.cpp มี OpenAI-compatible server เช่นกัน จึงใช้ adapter baseline เดียวได้ ([OpenRouter API](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request), [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility), [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md))

ข้อจำกัด: “OpenAI-compatible” ไม่แปลว่าความสามารถเท่ากันทุก provider โดยเฉพาะ tools, structured output, vision, audio และ streaming ทุก engine ต้องประกาศ capability ที่ต้องใช้ และ provider registry ต้อง reject profile ที่ไม่ผ่าน probe ในระยะถัดไป

Baseline ที่ implement:

- `ChatMessage`, `ChatRequest`, `ChatResponse`
- `OpenAICompatibleProvider` แบบ non-streaming
- OpenRouter key อ่านจาก environment variable เท่านั้น
- local loopback HTTP ใช้ได้โดยไม่ต้องมี cloud key
- remote HTTP ถูกปิดโดย default; OpenRouter บังคับ HTTPS
- transport injection ทำให้ unit test ไม่โทรเครือข่าย

ยังไม่ implement: SSE streaming, retry/backoff, rate-limit/cost budget, tool calling, multimodal upload, provider health/capability probe และ persistent request receipt

## Configuration schema v2

| Category | เจ้าของค่า | ตัวอย่าง |
|---|---|---|
| `paths` | local installation | workspace |
| `ffmpeg` | media adapter | ffprobe path |
| `capcut` | CapCut adapter | apps root |
| `runtime` | engine scheduler | max workers |
| `ui_bridge` | future UI shell | poll interval |
| `storage` | persistence policy | rollback journal mode |
| `security` | trust boundary | remote/insecure AI policy |
| `observability` | operations | log level |
| `ai` | provider registry | default provider |
| `ai.providers.<name>` | provider profile | kind, endpoint, model, key env, timeout |

Config v1 ยังอ่านได้เพื่อไม่ทำลาย tests/installation เดิม แต่ไฟล์ตัวอย่างและ active config ใช้ v2 ค่า secret จริงห้ามอยู่ใน TOML

## Windows launch model

- โครงการยังไม่สร้าง installer หรือ release ZIP
- batch files ใช้ `.venv` ที่ `D:\dev\MTCapcut\.venv` และไม่ติดตั้ง/อัปเกรด package
- `start.bat` เป็นเมนูเริ่มต้นสำหรับผู้ใช้ในระยะก่อนมี UI
- `doctor.bat` เป็น acceptance check ของเครื่อง
- `mtcapcut.bat` เป็น CLI wrapper เดียวก่อนมี UI

FFmpeg, CapCut, local AI server และ model weights ยังคงเป็นของ environment ภายนอก; doctor/provider probe ต้องอธิบายสิ่งที่ขาด

## Dependency decision

ปัจจุบัน dependency โดยตรงมีเพียง `pycapcut==0.0.4`; HTTP, TOML, threading, queue และ ZIP ใช้ Python standard library เพื่อลดความซับซ้อน `requirements-lock.txt` ตรึง transitive packages จาก environment ที่พิสูจน์แล้ว

SQLAlchemy/Alembic, UI framework, OpenAI SDK และ model libraries จะเพิ่มเมื่อ card ที่ต้องใช้ผ่าน ADR/compatibility tests ไม่เพิ่มล่วงหน้า

## Failure handling and observability

- config/path/secret ผิด: fail fast ก่อน submit
- provider connection/HTTP/response shape ผิด: structured exception; ห้ามแปลงเป็นคำตอบว่าง
- engine fail: `failed` event มี error type; future คง exception เดิม
- cancel: `cancelled` event หลัง engine ถึง safe checkpoint
- UI ปิด: งาน in-process หยุดตาม shutdown policy; persistent job resume ยังไม่พร้อม
- logs/receipts ต้อง redact Authorization และ prompt ที่ถูกจัดชั้นข้อมูล

## Acceptance และความเสี่ยงคงเหลือ

- PASS เมื่อ submit ไม่ block, event order คงที่, callback/cancel ทำงาน และ provider transport ทดสอบโดยไม่ใช้ network
- PASS เมื่อ config แยกหมวด, ไม่เก็บ secret และปิด remote insecure endpoint โดย default
- PASS เมื่อ batch files หา `.venv`/config ได้, ส่ง exit code ถูกต้อง และเริ่ม CLI โดยไม่ต้องพิมพ์ path ยาว
- NOT RUN: live OpenRouter/local model request จนผู้ใช้ตั้ง key/server/model
- NOT RUN: UI toolkit integration และ long-running persistent queue
- ความเสี่ยง: callback ที่ UI ใช้โดยตรงผิด thread, local server ที่เปิดรับ LAN, model capability ไม่ตรง engine และ queue ใน memory สูญหายเมื่อ process crash
## OpenRouter key storage for local private tests

`[ai.providers.openrouter]` accepts either `api_key_env` or a plaintext `api_key` in TOML. If both exist, the environment variable wins. The in-memory settings representation suppresses the TOML key from `repr`, but the TOML file itself remains plaintext and must not be shared, uploaded, or included in a release ZIP.

```toml
[ai.providers.openrouter]
api_key_env = "OPENROUTER_API_KEY"
api_key = ""
```

For this workstation-only test workflow, enter the key between the quotes in `config.toml`, then set `enabled = true`, `allow_remote_ai = true`, and select `default_provider = "openrouter"` only when remote AI use is intended.

