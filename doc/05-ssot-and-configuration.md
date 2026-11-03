# SSOT and Central Configuration

## หลักการ

SSOT หมายถึงเจ้าของข้อมูลแต่ละประเภทที่ชัดเจน ไม่ใช่ไฟล์เดียวเก็บทุกอย่าง การ cache หรือ export สำเนาได้ แต่ต้องระบุ source, version และวิธี invalidation

## SSOT map

| ข้อมูล | เจ้าของ/SSOT | ห้ามทำ |
|---|---|---|
| ค่าระบบและ paths | typed `AppConfig` ที่โหลดจาก TOML | engine เปิด TOML เอง |
| ข้อเท็จจริงจากผู้ใช้ | `ProjectBrief` | AI เขียนทับโดยไม่มี approval |
| รายการ input และบทบาทไฟล์ | `ProjectAssetBundle`/`AssetManifest` | เดาจาก extension หรือใช้ text ทุกไฟล์เป็นบรีฟ |
| metadata สื่อ | `MediaCatalog` | แต่ละ engine probe แล้วเก็บคนละค่า |
| observations และ claims | versioned `EvidenceStore` | เขียนทับหลักฐานเก่าหรือยกระดับ observation เป็น fact เงียบ ๆ |
| ความสัมพันธ์ของ assets, evidence, claims และ decisions | `Asset Understanding Map` ราย project | แต่ละ engine เก็บความหมายคนละชุดและไม่เชื่อมเวอร์ชัน |
| creative direction | active `CreativeBrief` | prompt แต่ละตัวตีความใหม่โดยไม่มี version |
| editorial state | `TimelinePlan` | pyCapCut object เป็นแผนหลัก |
| การตัดสินใจ | `DecisionLedger` | เก็บเฉพาะ final answer แล้วทิ้ง objections |
| workflow status | `JobStateStore` | ใช้ log text เป็นสถานะ |
| output files | `ArtifactManifest` | อาศัยชื่อไฟล์เพื่อเดาความสัมพันธ์ |

## Configuration layers

รายละเอียดการจัดเก็บและ query ของ map อยู่ใน [Asset Understanding Map Design](./16-asset-understanding-map-design.md) โดย `EvidenceStore` เป็นส่วนข้อมูลของ map เดียวกัน ไม่ใช่ SSOT อีกชุดที่ขัดกัน

ลำดับจากค่าพื้นฐานไปค่าที่มีอำนาจสูงกว่า:

1. defaults ใน typed schema
2. `config/default.toml`
3. `config/local.toml` ซึ่งไม่ commit
4. project configuration
5. environment variables สำหรับ secret/CI
6. CLI override สำหรับการรันครั้งนั้น

หลังรวมค่าแล้วต้อง validate ครั้งเดียวและส่ง immutable `AppConfig` ให้ components

## TOML baseline (schema v2)

```toml
schema_version = 2

[paths]
workspace = "D:/dev/MTCapcut/workspace"

[ffmpeg]
ffprobe = "D:/libs/ffmpeg/bin/ffprobe.exe"

[capcut]
apps_root = "C:/Users/acer/AppData/Local/CapCut/Apps"
apps_root = "C:/Users/acer/AppData/Local/CapCut/Apps"

[runtime]
max_workers = 2

[ui_bridge]
poll_interval_ms = 100

[storage]
journal_mode = "delete"

[security]
allow_remote_ai = false
allow_insecure_remote_http = false

[observability]
log_level = "INFO"

[ai]
# default_provider = "ollama"

[ai.providers.ollama]
kind = "local_openai"
base_url = "http://127.0.0.1:11434/v1"
model = "qwen3:8b"
enabled = false

[ai.providers.openrouter]
kind = "openrouter"
base_url = "https://openrouter.ai/api/v1"
model = "openai/gpt-4o-mini"
api_key_env = "OPENROUTER_API_KEY"
enabled = false
```

## Configuration rules

- TOML ต้องเป็น UTF-8 ตาม TOML specification
- Python 3.14 `tomllib` อ่าน TOML ได้แต่ไม่เขียน; หากต้องรักษารูปแบบตอนแก้ config ให้ประเมิน TOML Kit แยกต่างหาก
- path ภายใน TOML ใช้ forward slash เพื่อลด escaping บน Windows
- secret ใช้ environment variable reference ห้ามเก็บค่าจริง
- ทุก config snapshot ที่ใช้สร้าง draft ต้องถูก hash และบันทึกใน Artifact Manifest
- เปลี่ยน `schema_version` เมื่อโครงสร้าง config ไม่ backward-compatible
- startup ต้อง fail fast หาก executable ไม่มีจริงหรือ version policy ไม่ผ่าน

แหล่งข้อมูล: [TOML v1.0.0](https://toml.io/en/v1.0.0), [Python tomllib](https://docs.python.org/3/library/tomllib.html)

