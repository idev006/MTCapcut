# Review and Revise Governance

วันที่กำหนด: 2 พฤศจิกายน 2026  
สถานะ: Required policy

## State machine

```text
DRAFT -> SELF_REVIEWED -> IN_REVIEW
                         |       |
                         |       +-> APPROVED -> VALIDATING -> ACCEPTED
                         |
                         +-> CHANGES_REQUESTED -> REVISING -> RE_REVIEW
                         |
                         +-> REJECTED

Any active state -> PAUSED / ABANDONED
```

งานจาก `REVISING` ห้ามข้าม `RE_REVIEW` ไป `ACCEPTED`

## Finding schema

ทุก finding ต้องมี:

- stable finding ID
- severity: Critical, High, Medium, Low, Note
- dimension: fact, ethics, rights, security, architecture, test, creative, technical, cost
- exact target และ EvidenceRef/file location
- observed fact แยกจาก hypothesis
- impact
- required action หรือ acceptance condition
- owner
- disposition: fixed, accepted-risk, false-positive, duplicate, deferred
- reviewer และ approver
- created/resolved timestamps
- waiver ID/expiry หากไม่แก้

## Severity policy

- Critical: data loss, security/privacy breach, unsupported high-impact claim, destructive action, unusable output — block ทันที
- High: ความถูกต้อง/compatibility/architecture defect ที่ทำให้ acceptance หลักไม่ผ่าน — block release
- Medium: maintainability, quality หรือ coverage gap — ต้องแก้หรือมี tracked follow-up
- Low/Note: improvement ที่ไม่ block

## Reviewer independence

- high-risk item ต้องมี reviewer คนละบทบาทกับผู้สร้าง
- AI reviewer ที่ใช้ model/prompt family เดียวกับผู้สร้างไม่ถือเป็น independent validation
- Fact/Ethics/Rights/Security/Technical QC มีอำนาจ block เฉพาะขอบเขตตน
- Clip Director สังเคราะห์ creative conflicts แต่ override trust blocker ไม่ได้
- Product Owner อนุมัติ intent/facts และ accepted-risk ที่อยู่ในอำนาจ

## Revision policy

- revision ต้องตอบ finding ทีละข้อ ไม่แก้แบบกลบปัญหา
- เปลี่ยน contract/schema ต้องวิเคราะห์ downstream impact
- re-review scope ต้องรวม regression ที่อาจเกิดจากการแก้
- เกิน 3 revision loops ให้หยุดและเลือก split/redesign/abandon/escalate
- finding ที่ deferred ต้องสร้าง Kanban card ก่อนปิดงาน

## Waiver policy

Waiver ต้องมีเหตุผล ขอบเขต ผู้อนุมัติ ความเสี่ยงคงเหลือ mitigation และ expiry ห้าม waive เด็ดขาดสำหรับ active credential exposure, unresolved destructive path ที่อาจเขียนทับ/ลบข้อมูลจริง, critical factual fabrication ใน high-stakes output และการขาดสิทธิใช้งานที่จำเป็นต่อการเผยแพร่ Critical อื่นยกเว้นได้เฉพาะ Product Owner ร่วมกับเจ้าของขอบเขต (Security, Fact, Rights หรือ Technical QC) และต้องมี recovery/containment plan

## Review packs

- Research: question, sources, evidence table, inference, unknowns
- Architecture: requirements, alternatives, trade-offs, threat/risk, ADR
- Engine: role contract, fixtures, benchmark, failures, cost
- Compatibility: versions, steps, artifacts, screenshots/probe, pass/fail
- Creative: brief, candidate timeline, rationale, objections, audience/fact review

## Exit criteria

Review จบเมื่อ findings ทุกข้อมี disposition, blockers ปิด, re-review scope ผ่าน และ decision ledger บันทึกเหตุผล การเงียบหรือไม่มี comment ไม่ถือเป็น approval

