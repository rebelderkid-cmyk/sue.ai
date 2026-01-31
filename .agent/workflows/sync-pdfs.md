---
description: Pipeline สำหรับการกู้คืนและ Sync ไฟล์ PDF จาก ZIP Archives เข้าสู่ Google Cloud Storage แบบ Turbo Mode
---

# Workflow: PDF Recovery & Cloud Sync

Workflow นี้ใช้สำหรับจัดการกระบวนการ Sync ข้อมูลไฟล์กฎหมาย (140 ปี) จากเครื่อง Worker ไปยัง GCS เผื่อในกรณีที่การเชื่อมต่อหลุดหรือต้องการตรวจสอบสถานะระยะยาว

## 1. 🔍 ตรวจสอบความคืบหน้า (Monitoring)

ใช้คำสั่งเหล่านี้เพื่อดูว่าระบบยังทำงานอยู่หรือไม่:

// turbo
```bash
# เช็คจำนวนไฟล์บน Cloud ล่าสุด
gcloud storage ls gs://main_legal_data/pdfs/ --project gen-lang-client-0464468580 | wc -l

# เช็คจำนวนไฟล์ที่รอส่ง (Local) ในเครื่อง VM
gcloud compute ssh recovery-worker --project gen-lang-client-0464468580 --zone asia-southeast1-b --command "find ~/turbo_temp -name '*.pdf' | wc -l"

# ดู Log การทำงานปัจจุบัน
gcloud compute ssh recovery-worker --project gen-lang-client-0464468580 --zone asia-southeast1-b --command "tail -f turbo_sync_v2.log"
```

## 2. 🛠 การกู้คืนระบบ (Recovery)

หากพบว่า Process หยุดทำงาน (ไม่มีไฟล์ใหม่เพิ่มขึ้นบน Cloud นานเกิน 30 นาที):

1. ตรวจสอบว่ามี Python Process รันอยู่หรือไม่:
   `gcloud compute ssh recovery-worker ... --command "ps aux | grep python3"`

2. หากไม่มี ให้รันสคริปต์ Turbo Sync ใหม่ (ควรใช้ Screen หรือ Nohup):
   `gcloud compute ssh recovery-worker ... --command "nohup python3 turbo_sync_v2.py > turbo_sync_v2.log 2>&1 &"`

## 3. ✅ การปิดภารกิจ (Completion)

เมื่อการ Sync เสร็จสิ้น (จำนวนไฟล์บน Cloud นิ่งและสอดคล้องกับจำนวน Zip):
1. ตรวจสอบ Errors ใน Log (`bad CRC`).
2. ลบโฟลเดอร์ชั่วคราว: `rm -rf ~/turbo_temp`
3. บันทึกวันเวลาที่เสร็จสิ้นลงใน `Agent_Journal.md`
