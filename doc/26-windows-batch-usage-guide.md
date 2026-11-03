# Windows Batch Usage Guide

ประเภท: How-to  
ผู้อ่าน: ผู้ใช้และทีมพัฒนาที่ใช้ environment `D:\dev\MTCapcut\.venv`

## ขอบเขต

โครงการยังไม่มี installer, portable ZIP หรือ UI เอกสารนี้อธิบาย batch files สำหรับเปิดและตรวจ engines ใน source workspace เท่านั้น

## เริ่มใช้งานง่าย

ดับเบิลคลิก `start.bat` แล้วเลือก:

1. ตรวจ environment
2. แสดง assets ของ project
3. ดูคำสั่ง CLI
0. ออกจากโปรแกรม

`start.bat` ไม่สร้าง environment และไม่ติดตั้ง library หาก `.venv` หรือ `config.toml` ไม่มี โปรแกรมจะแจ้งสิ่งที่ต้องเตรียมโดยไม่แก้เครื่อง

## Batch files

| File | หน้าที่ |
|---|---|
| `start.bat` | เมนูเริ่มต้นสำหรับผู้ใช้ |
| `doctor.bat` | ตรวจ Python, FFmpeg, pyCapCut, CapCut และ workspace |
| `mtcapcut.bat` | ส่ง arguments ไป CLI หลัก |
| `run-tests.bat` | รัน automated regression tests |

ตัวอย่าง:

```bat
doctor.bat
mtcapcut.bat assets PROJECT_ID
mtcapcut.bat timeline PROJECT_ID ASSET_ID
run-tests.bat
```

## Dependencies

`requirements.txt` แสดง dependency โดยตรง และ `requirements-lock.txt` บันทึก environment ที่พิสูจน์แล้ว แต่ batch files รอบนี้จะไม่ติดตั้งหรืออัปเกรด package อัตโนมัติ

ปัจจุบันยังไม่ต้องติดตั้ง OpenAI SDK, SQLAlchemy, Alembic หรือ UI framework เพิ่ม
