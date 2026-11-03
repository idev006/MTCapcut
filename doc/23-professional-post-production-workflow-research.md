# Professional Post-Production Workflow Research

วันที่ตรวจ: 2 พฤศจิกายน 2026  
ประเภท: Explanation + research reference  
ผู้อ่าน: Product Owner, Senior Software Engineer, Studio-role designers และ QA  
เป้าหมาย: ใช้หลักฐานจากองค์กรวิชาชีพ ผู้ผลิตเครื่องมือ และมาตรฐานอุตสาหกรรมกำกับการจำลองทีมตัดต่อของ MTCapcut

## ขอบเขตและข้อจำกัด

ไม่มี workflow เดียวที่ทุกสตูดิโอเรียกว่า “world-class” เหมือนกันทั้งหมด งานภาพยนตร์ ซีรีส์ ข่าว สารคดี โฆษณา และ social video มีบทบาทกับลำดับ approval ต่างกัน เอกสารนี้จึงสรุปเฉพาะรูปแบบร่วมที่แหล่งอุตสาหกรรมสนับสนุน และแยกข้อเสนอของ MTCapcut ออกจากข้อเท็จจริงที่ตรวจพบ

`Clip Director`, `Director Council` และชื่อ engines เป็นคำออกแบบของ MTCapcut ไม่ใช่ชื่อตำแหน่งมาตรฐานสากล

## สิ่งที่ยืนยันจากแหล่งอุตสาหกรรม

### 1. Assistant Editor ทำให้ Editor ทำงานสร้างสรรค์ได้โดยไม่ติดงานระบบ

Motion Picture Editors Guild อธิบายงาน Assistant Editor ว่าครอบคลุมการรับและจัด dailies, cross-check camera/sound/script records, QC ภาพและเสียง, logging/scripting, จัดโครงการให้เป็นระเบียบ, temp sound/music/VFX และเตรียม turnovers ไป sound, picture online และ VFX หลัง lock งานจึงไม่ใช่เพียง “ผู้ช่วยกดปุ่ม” แต่เป็นเจ้าของความพร้อม ความถูกต้อง และความเป็นระเบียบของ editorial system

ผลต่อ MTCapcut:

- `Asset Intake`, `Media Preflight`, `Sync`, `Proxy`, `Logging`, `Metadata`, `Relink` และ `Turnover` ต้องเป็นความสามารถชั้นแรก
- AI Director ไม่ควรเสียเวลาแก้ path, codec, metadata หรือไฟล์หาย; Assistant Editorial Engines ต้องเตรียมข้อมูลพร้อมใช้

แหล่ง: [Editors Guild — Jason Brotman](https://www.editorsguild.com/About/What-Do-Our-Members-Do/Past-Featured-Members/ArticleID/392/JASON-BROTMAN-ASSISTANT-EDITOR-BOARD-MEMBER), [Ben Insler](https://www.editorsguild.com/About/What-Do-Our-Members-Do/Past-Featured-Members/ArticleID/405/BEN-INSLER-ASSISTANT-EDITOR), [Sabrina Gimenez](https://www.editorsguild.com/About/What-Do-Our-Members-Do/Past-Featured-Members/ArticleID/377/SABRINA-GIMENEZ-ASSISTANT-EDITOR)

### 2. การเตรียมก่อนตัดช่วยลดเวลาและความผิดพลาด

BBC Academy แนะนำให้เตรียม script/shot list/storyboard, จัด rushes, ทำ shot list พร้อม timecode, transcript และ paper edit รวมทั้งเตรียม archive/stills/music ก่อนเข้าห้องตัด งาน tapeless ยังต้องมี naming convention, backup และตรวจความต้องการของ post-production ก่อนถ่าย

ผลต่อ MTCapcut:

- Brief, shot log, transcript, rights และ source timecode ต้องเข้าสู่ SSOT ก่อน Story/Timeline approval
- ระบบต้องมี readiness gate; ห้ามรีบสร้าง draft เมื่อ assets ยังไม่ครบหรือยังไม่ตรวจ

แหล่ง: [BBC — Preparing for the Edit](https://downloads.bbc.co.uk/academy/collegeofproduction/docs/preparing_for_the_edit_ts.pdf), [BBC — Tapeless Workflow](https://downloads.bbc.co.uk/academy/collegeofproduction/docs/tapeless_workflow_ts.pdf)

### 3. งานระดับมืออาชีพใช้ proxy/offline แล้ว relink กลับต้นฉบับ

Avid และ Adobe อธิบายการตัดด้วยสื่อความละเอียดต่ำเพื่อให้ทำงานคล่อง ก่อน relink/conform กลับ high-resolution media สำหรับ finishing และ delivery วิธีนี้ตรงกับเครื่องเป้าหมาย RAM 8 GB ไม่มี GPU แยก

ผลต่อ MTCapcut:

- `ProxyEngine` ต้องรักษา source identity, timecode, duration และ audio mapping
- Final delivery ต้องตรวจว่าใช้ source/master ที่ถูกต้อง ไม่ใช่ proxy

แหล่ง: [Avid Media Composer Editing Guide](https://resources.avid.com/SupportFiles/attach/Media_Composer_Editing_Guide_7_0.pdf), [Adobe Ingest and Proxy Workflow](https://helpx.adobe.com/premiere/desktop/organize-media/ingest-proxy-workflow/ingest-and-proxy-workflow.html)

### 4. การตัดเป็นวงรอบหลาย revision และมีลำดับผู้ให้ notes

คำอธิบายงานจาก Editors Guild แสดงวงรอบ editor’s cut → director notes → showrunner/producer/network notes → lock แล้วจึง turnovers การ lock ไม่ได้หมายความว่าจะไม่มีการเปลี่ยนอีก แต่การเปลี่ยนหลัง lock ต้องส่ง update ให้ทีม downstream อย่างมีวินัย

ผลต่อ MTCapcut:

- ต้องมี `EditorialRevision`, timestamped findings, approval authority และสถานะ `Assembly`, `Editor Review`, `Director Review`, `Client Review`, `Picture Lock`
- การแก้หลัง lock ต้องสร้าง change receipt และคำนวณ downstream impact

แหล่ง: [Editors Guild — Priscilla Zambrano](https://www.editorsguild.com/About/What-Do-Our-Members-Do/Past-Featured-Members/ArticleID/460/Priscilla-Zambrano-Assistant-Editor), [Frame.io timestamped review](https://help.frame.io/en/articles/9105251-commenting-on-your-media)

### 5. Lock แล้วจึง turnover ไปทำ finishing เฉพาะทาง

Editors Guild อธิบาย turnovers หลัง lock ไป picture online, sound editing/mixing และ VFX พร้อมส่งการเปลี่ยนแปลงเพิ่มเติมเมื่อจำเป็น Blackmagic แสดง conform workflow ที่ต้องแก้ conflict และ lock การเลือก media ที่ถูกต้อง

ผลต่อ MTCapcut:

- แยก Creative Editorial ออกจาก `Conform`, `Color`, `Sound`, `Graphics/VFX`, `Caption` และ `Delivery`
- Timeline/Receipt ต้องส่ง source range, handle, media/version IDs และ change list ให้ downstream engines

แหล่ง: [Editors Guild — Jason Brotman](https://www.editorsguild.com/About/What-Do-Our-Members-Do/Past-Featured-Members/ArticleID/392/JASON-BROTMAN-ASSISTANT-EDITOR-BOARD-MEMBER), [Blackmagic Design Colorist Guide](https://documents.blackmagicdesign.com/UserManuals/DaVinci-Resolve-20-Colorist-Guide.pdf)

### 6. Collaboration ต้องมี ownership, locking/versioning และ review ที่ผูก timecode

Avid ใช้ shared projects/bin locking; Adobe Team Projects ให้ผู้ร่วมงาน accept/reject changes; Frame.io เก็บ comments และ annotations ตาม timecode พร้อมสถานะ review สิ่งเหล่านี้ชี้ว่าการประสานงานต้องมี ownership และ version history ไม่ใช่ให้ engines เขียน timeline เดียวกันพร้อมกัน

ผลต่อ MTCapcut:

- Workflow Orchestrator เป็นผู้ commit revision
- Engines ส่ง proposals/receipts; ห้ามแก้ shared state โดยตรง
- ReviewFinding ต้องผูก revision + time range + owner + disposition

แหล่ง: [Avid Shared Projects](https://www.avid.com/resource-center/media-composer-shared-projects), [Adobe collaboration](https://helpx.adobe.com/premiere/desktop/collaborate-with-others/collaboration-in-premiere.html), [Frame.io comments](https://help.frame.io/en/articles/9105278-comments-panel-overview)

### 7. QC เป็นทั้ง automated และ manual

Netflix แยกสถานะ delivery, automated QC/encoding และ manual QC ออกจากกันอย่างชัดเจน การส่งไฟล์สำเร็จจึงไม่เท่ากับผ่าน QC หรือพร้อมเผยแพร่

ผลต่อ MTCapcut:

- `DraftCreated`, `Exported`, `TechnicalQCPassed`, `EditorialApproved` และ `Delivered` ต้องเป็นคนละสถานะ
- ห้ามสรุปว่า output ผ่านเพียงเพราะ ffmpeg/CapCut export สำเร็จ

แหล่ง: [Netflix — Delivered vs Processed](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215652537-What-is-the-difference-between-Delivered-and-Processed-on-Backlot)

### 8. เสียงต้องใช้ delivery profile ไม่ใช้ค่าตายตัวเดียวทุกงาน

EBU R 128 กำหนดวิธีวัด programme loudness, loudness range และ true peak สำหรับ broadcast และมี supplements สำหรับ short-form, streaming และ cinematic content ค่าเป้าหมายต้องมาจากปลายทางส่งมอบ ไม่ควร hard-code ค่าเดียวให้ทุก platform

ผลต่อ MTCapcut:

- `DeliveryProfile` ระบุ loudness target, tolerance, true peak และ measurement method
- Audio Engine ต้องรายงาน measured values และไม่อ้าง compliance หากไม่ได้วัดตาม profile

แหล่ง: [EBU R 128](https://tech.ebu.ch/publications/r128), [EBU Loudness](https://tech.ebu.ch/loudness/)

### 9. AI เหมาะกับงานรอบการตัด แต่ creative authorship ต้องมีมนุษย์กำกับ

งานสำรวจร่วม Avid/ACE ปี 2026 รายงานการใช้ AI มากใน transcription, audio cleanup และ search ขณะที่ผู้ตอบยืนยันความสำคัญของ creative authorship Avid เองอธิบาย AI-assisted multicam เป็น editable first pass โดย Editor ยังควบคุม story, pacing และ reaction shots

ผลต่อ MTCapcut:

- AI ทำ dailies prep, search, transcription, alternatives, first assembly และ QC ได้
- Final editorial authority ต้องเป็น human-approved policy โดยเฉพาะงาน factual, rights-sensitive หรือ public communication

แหล่ง: [Avid/ACE — AI in Post-Production](https://www.avid.com/resource-center/ai-in-post-production-film-tv-editors), [Avid Media Composer 2026.8](https://www.avid.com/resource-center/whats-new-avid-media-composer-2026-8)

## Workflow อ้างอิงสำหรับ MTCapcut

```text
1. Brief / Intent Approval
2. Ingest, Backup, Hash, Rights, Proxy
3. Dailies QC, Sync, Logging, Transcript, Selects
4. Paper Edit / Story Architecture
5. Assembly Cut
6. Editor Review and Fine Cut
7. Director / Client Review
8. Picture Lock
9. Turnovers: Picture Online, Sound, Color, Graphics, Captions
10. Conform and Finishing
11. Automated Technical QC
12. Independent Editorial / Fact / Rights QC
13. Human Approval
14. Delivery, Receipt, Archive and Recovery Manifest
```

แต่ละขั้นต้องมี input contract, owner, exit criteria, artifacts, findings และ receipt ห้ามใช้ชื่อขั้นเพื่อจำลองความเป็นมืออาชีพโดยไม่มี behavior และ quality gate จริง

## Mapping บทบาทจริงกับระบบ

| งานวิชาชีพที่พบ | Studio role ใน MTCapcut | Engines สนับสนุน |
|---|---|---|
| Assistant editorial / dailies | Assistant Editor | Intake, Sync, Proxy, Metadata, ASR/OCR, Relink |
| Picture/story editing | Lead/Story Editor | Retrieval, Selects, Story, Edit Decision, Timeline |
| Director/producer review | Clip Director + Human Authority | Alternatives, Review, Approval Ledger |
| Sound/music editorial | Sound/Music Director | Dialogue, Music, Loudness, Mix, Audio QC |
| Online/conform/color | Finishing/Conform Editor | Relink, Timebase, Color, Output Conform |
| Captions/graphics/VFX | Specialist Editors | Caption, Graphic, Effect adapters |
| QC/delivery | Independent QC + Delivery Owner | Technical, Fact, Rights, Export, Receipt |

Studio role ใช้ judgment และ rubric; Engine เป็น capability ที่เปลี่ยน implementation ได้ บทบาทหนึ่งใช้หลาย engines และ engine หนึ่งสนับสนุนหลายบทบาทได้

## Tune-up ที่มีหลักฐาน

การ “ผ่านการ tune-up” ต้องหมายถึง:

1. มี golden projects ที่สิทธิชัดเจน
2. ผู้ตัดต่อมืออาชีพกำหนด corrections/rubrics
3. วัดผล assembly, selects, factual accuracy, revision count, delivery defects และเวลา
4. เปรียบเทียบ StudioProfile รุ่นเก่ากับรุ่นใหม่แบบ blind review
5. เพิ่ม failure เป็น regression case
6. Promote profile/recipe/engine version เมื่อผ่าน gates เท่านั้น
7. เก็บ rollback และ receipt ของทุก promotion

จนกว่าจะมี real-asset benchmark และ professional blind review ให้ใช้คำว่า `world-class target` ไม่ใช่ `world-class achieved`
