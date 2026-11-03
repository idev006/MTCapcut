# Agile Kanban Operating Model

วันที่กำหนด: 2 พฤศจิกายน 2026  
สถานะ: Provisional policy — ต้องปรับจาก flow data จริง  
เจ้าของนโยบาย: Product Owner และ Technical Lead

## เป้าหมาย

บริหารการไหลของ **คุณค่าและหลักฐานที่ผ่าน validation** ไม่ใช่จำนวนงานที่เริ่มแล้วหรือเปอร์เซ็นต์ความคืบหน้าที่ประเมินจากความรู้สึก

ระบบนี้ใช้ Kanban เป็นวิธีบริหาร flow และใช้หลัก Agile เรื่อง working software, feedback, technical excellence และการปรับตัว ไม่ใช้ sprint เป็นข้อบังคับ

แหล่งหลัก: [Kanban Guide 2025](https://kanbanguides.org/wp-content/uploads/2025/05/Kanban-Guide-2025-05.pdf), [Kanban Method](https://kanban.university/resources/kanbanmethodinfographic/), [Agile principles](https://agilemanifesto.org/principles)

## Definition of Workflow

```text
Options -> Ready -> Research -> Analyze -> Design -> Review -> Validate -> Done
                                                     |           |
                                                     v           v
                                                   Revise <---- Fix required
                                                     |
                                                     v
                                                  Re-review

Any started state --stop approved--> Abandoned
```

- `Options`: ความคิดหรือปัญหาที่ยังไม่ commit
- `Ready`: ผ่าน pull criteria และพร้อมเริ่มเมื่อมี capacity
- `Research`: รวบรวมหลักฐานปฐมภูมิหรือทำ experiment
- `Analyze`: สังเคราะห์ facts, hypotheses, risks และ alternatives
- `Design`: สร้าง contract, ADR, prototype หรือ implementation
- `Review`: ตรวจโดยบทบาทที่เหมาะสมและแยกจากผู้สร้างเมื่อความเสี่ยงสูง
- `Revise`: แก้ตาม findings พร้อมบันทึก disposition
- `Re-review`: ตรวจเฉพาะผลกระทบและ regression scope ที่กำหนด
- `Validate`: รัน gates/tests/acceptance กับหลักฐานจริง
- `Done`: ส่งมอบผลลัพธ์ที่ผ่าน finished policy
- `Abandoned`: terminal outcome เมื่อหยุดงานโดยมีเหตุผลและผู้อนุมัติ

`Blocked` เป็น flag ไม่ใช่ column ซ่อนงาน และยังนับ WIP

## จุดเริ่มและจุดจบ

- Started: card ถูก pull จาก `Ready` เข้า `Research`
- Finished for flow: card เข้า `Done` หรือ `Abandoned`
- Cycle Time: Started ถึง Finished
- Discovery Lead Time: `Options` ถึง `Ready` ใช้เป็น metric เสริม

## Work item types

- `RQ`: Research Question — จบด้วย evidence-backed conclusion
- `EXP`: Experiment/Spike — จบด้วยผลทำซ้ำได้
- `ADR`: Architecture Decision — จบด้วย alternatives/trade-offs และ approval
- `ENG`: Engine Capability — จบด้วย contract, implementation, tests และ evidence
- `DEF`: Defect/Risk Reduction — จบด้วย regression test หรือ mitigation ที่ยืนยันแล้ว
- `DOC`: Documentation — จบด้วย traceable sources และ review
- `CMP`: Compatibility Proof — จบด้วย artifact/report จากระบบจริง

ทุก card ต้องมี ID, type, value hypothesis, owner, class of service, risk tags, dependencies, acceptance criteria, evidence requirement, start date และ artifact links

## WIP limits เริ่มต้น

| State | WIP limit |
|---|---:|
| Research | 3 |
| Analyze | 2 |
| Design | 2 |
| Review + Re-review | 2 |
| Revise | 2 |
| Validate | 1 |

Policies:

- downstream เต็ม: ห้ามเริ่มงานใหม่ ให้ช่วยงานเก่าที่สุด
- Review queue เต็ม: หยุด Research/Design และ swarm ไปช่วย review/fix
- Expedite ได้ไม่เกิน 1 item ทั้งระบบ
- Blocked item ยังนับ WIP
- card ต้องเล็กพอให้ review/validate ได้อย่างอิสระ
- WIP limits เป็น hypothesis ต้องเปลี่ยนจากข้อมูล flow ไม่ใช่ความสะดวก

## Pull criteria เข้า Ready

- ปัญหาและคุณค่าที่ต้องการชัดเจน
- ระบุ type, owner และผู้อนุมัติ
- acceptance/evidence criteria ตรวจได้
- dependencies สำคัญและ risk tags ถูกระบุ
- มี source strategy หรือ experiment design
- ประเมิน privacy, rights, destructive action และ external AI use
- ขนาดเหมาะกับ review หนึ่งรอบ

## Entry criteria เข้า Review

- deliverable อยู่ใน SSOT
- แยก observed facts, inference, hypothesis และ unknowns
- มี source/version/date หรือ reproducible experiment
- self-review ผ่าน
- tests ที่เกี่ยวข้องรันแล้วพร้อมหลักฐาน หรือระบุ NOT RUN พร้อมเหตุผล
- ไม่มี placeholder ที่ซ่อนงานค้าง

## Finished policy

Card เป็น Done เมื่อ:

- acceptance criteria ผ่านทั้งหมด
- critical/high findings ปิดหรือมี waiver ที่ยังไม่หมดอายุ
- หลักฐานและ test artifacts แนบครบ
- docs, ADR, config, source register และ risk register อัปเดตตามผลกระทบ
- ไม่มี secret รั่วหรือข้อมูลจริงถูกเขียนทับ
- ผลทำซ้ำได้ หรืออธิบายข้อจำกัดชัดเจน
- ผู้มีอำนาจตาม decision-rights อนุมัติ
- remaining risks ถูกบันทึกเป็น follow-up cards

ผลทดลองที่ไม่สนับสนุนสมมติฐานเป็น Done แบบ `Learned/Invalidated` ได้ หากวิธีทดลองถูกต้องและหลักฐานครบ รายงาน outcome throughput แยก `Delivered`, `Learned/Invalidated` และ `Abandoned`; ห้ามตีความ Abandoned เป็น value delivered

## Allowed transitions และ minimum evidence

| Current | Outcome/minimum evidence | Next |
|---|---|---|
| Research | source log หรือ reproducible experiment artifacts ครบ | Analyze |
| Analyze | facts/inferences/unknowns, alternatives และ risks แยกชัด | Design |
| Design | deliverable, self-review, affected contracts/tests ระบุครบ | Review |
| Review | approved; findings มี disposition | Validate |
| Review | changes requested พร้อม owner/acceptance | Revise |
| Revise | fixes และ regression scope บันทึกครบ | Re-review |
| Re-review | approved | Validate |
| Re-review | findings remain/new regression | Revise หรือ Design |
| Validate | executable acceptance plan ผ่าน พร้อม gate report | Done |
| Validate | product/design defect | Revise หรือ Design ตาม finding |
| Any started | stop approved + reason/owner/date | Abandoned |

## Classes of service

- `Standard`: ค่าเริ่มต้น
- `Fixed Date`: มี due date, cost of delay และ latest responsible start
- `Expedite`: production/security/data-loss blocker เท่านั้น จำกัด 1
- `Intangible`: research debt, refactoring, observability และ infrastructure; pull อย่างน้อย 1 ในทุก 5 items

Standard เรียงตาม value, risk และ age ใน Replenishment หาก Expedite เข้าระบบ ต้องไม่เพิ่ม total WIP: หยุด pull งานใหม่และ swarm; item ที่ถูกเลื่อนต้องมองเห็นได้

## Feedback loops

- Daily Flow Review 10–15 นาที: ดูขวาไปซ้าย, blocked, age, WIP, SLE risk
- Replenishment รายสัปดาห์: pull เข้า Ready ตาม capacity/value/risk
- Research/Design Review: เมื่อ item พร้อม ไม่รอรอบเวลา
- Delivery Review รายสัปดาห์: แสดง Done evidence ต่อ Product Owner
- Flow Review ทุก 2 สัปดาห์: cycle time, throughput, aging, blocked/rework
- Risk/Operations Review รายเดือน: security, rights, compatibility, model drift, cost
- Retrospective รายเดือน: เปลี่ยน policy แบบ experiment พร้อม success metric/rollback

## Flow metrics

ขั้นต่ำตาม Kanban Guide:

- WIP
- Throughput ต่อสัปดาห์
- Work Item Age
- Cycle Time

เพิ่มเติมสำหรับ MTCapcut:

- Blocked time และ reason
- Queue time ก่อน Review/Validate
- Rework rate: Review -> Revise
- Review escape rate
- Evidence completeness และ experiment reproducibility
- Critical factual error count
- CapCut compatibility pass rate
- Human correction severity/override rate
- AI cost/run, cache hit rate และ processing time

Metrics ใช้ปรับระบบ ไม่ใช้กดดันหรือจัดอันดับรายบุคคล

## Provisional SLE

ยังไม่มี historical data:

- RQ: 85% ภายใน 5 calendar days
- EXP: 85% ภายใน 7 calendar days
- ADR: 85% ภายใน 7 calendar days
- ENG: 85% ภายใน 10 calendar days
- DEF: 85% ภายใน 5 calendar days
- DOC: 85% ภายใน 4 calendar days
- CMP: 85% ภายใน 7 calendar days

ตัวเลขนี้เป็น local best guess ไม่ใช่ข้อกำหนดของ Kanban Guide เมื่อมี finished items 20–30 รายการต่อชนิด ให้คำนวณ percentile จากข้อมูลจริงและทบทวน SLE

## Aging and stop policy

เมื่อ Work Item Age เกิน 80% ของ SLE ต้องเลือก `continue`, `split`, `swarm`, `pause` หรือ `stop` พร้อมเหตุผล Pause ระยะสั้นยังนับ WIP และ age; การรอภายนอกระยะยาวต้องส่งกลับ Options โดยปิด cycle เดิมหรือเข้า Abandoned ห้าม reset start date เพื่อทำให้ age ลดลง Unknown ที่มีผลสูงต้องสร้าง `RQ` ห้ามแปลงเป็น assumption เงียบ ๆ

Items ใน Review และ Re-review รวมกันต้องไม่เกิน 2 รวมทั้ง waiting และ active review

