# 🏗️ Project Infrastructure Map (Blueprint)

เอกสารนี้รวบรวม "ความจริงหนึ่งเดียว" (Single Source of Truth) ของโครงสร้างพื้นฐานในโปรเจกต์ Deka Scraping เพื่อให้ AI และทีมงานมีความเข้าใจที่ตรงกัน

## ☁️ Google Cloud Infrastructure

### 🆔 Projects
- **Primary Project**: `gen-lang-client-0464468580`
- **Vertex AI Project**: `gen-lang-client-0464468580` (Deka/Law Search)

### 📦 Storage (GCS Buckets)
- **Deka PDFs**: `gs://sue-ai-pdfs-storage/` (Publicly Accessible)
- **Law/General PDFs**: `gs://main_legal_data/pdfs/` (Backup/Internal)
- **Source Data**: `gs://deka-legal-search-data/`

### 🖥️ Compute (VM Instances)
- **`recovery-worker`**: (Zone: `asia-southeast1-b`)
  - **Purpose**: Data recovery, Unzipping, and Syncing.
  - **Mount Point**: `/mnt/data/downloads/zip` (Contains 171GB of ZIP archives)
- **`hf-transfer-worker`**:
  - **Purpose**: Original indexing and miscellaneous data handling.

### 🔍 Vertex AI Search (Search Apps)
- **DEKA Engine**: `sue-ai-search_1768730959752`
- **LAW Engine**: `main-legal-search_1768906502953`

---

## 🚀 Data Pipelines

### 1. Turbo Sync Pipeline
- **Script**: `turbo_sync_v2.py` (located on `recovery-worker`)
- **Action**: Threaded Unzip -> gsutil parallel sync.
- **Workflow**: See `.agent/workflows/sync-pdfs.md`

## 🛠 Tech Stack
- **Backend**: Go (Golang) 1.24
- **Frontend**: Next.js (Vercel)
- **Search**: Vertex AI Search & Conversation (RAG)
- **Storage**: Google Cloud Storage
