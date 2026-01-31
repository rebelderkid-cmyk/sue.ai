# 🗺️ Sue.AI Project Map

Welcome to the **Sue.AI** project (Deka Scraping & Legal AI).
This document serves as a **Table of Contents** for the project structure following the "Grand Refactoring".

## 📂 Top-Level Directories

| Directory | Status | Description |
| :--- | :--- | :--- |
| **`src/`** | 🟢 **Active** | **Core Application Code**. Contains the live Backend API and Frontend Web App. |
| **`pipelines/`** | 🟠 **Scripts** | **Data Processing Tools**. Scripts for OCR, Cleaning, and Cloud Uploading. |
| **`data/`** | 🔵 **Storage** | **Local Data Storage**. Contains PDFs, JSONL datasets, and Logs. (Git Ignored) |
| **`archive/`** | ⚪ **Legacy** | **Historical Code** (Phase 2-6). Old versions kept for reference. |

---

## 🏗️ Source Code (`src/`)
Code responsible for the running application (Deployment).

### `src/backend/` (Python Flask + RAG)
- `app.py`: **Main Entry Point**. The Flask API server (Cloud Run).
- `rag_core.py`: **RAG Logic**. Handles Vertex AI Search, Prompt Engineering, and Gemini integration.
- `Dockerfile`: Configuration for building the backend container.

### `src/frontend/` (Next.js)
- `src/app/`: Next.js App Router source code.
- `src/app/chat/page.tsx`: **Main Chat Interface**.

---

## ⚙️ Pipelines (`pipelines/`)
Scripts for data preparation and maintenance.

- **`pipelines/ocr/`**: Scripts for extracting text from PDFs (`process_batch.py`).
- **`pipelines/cleaning/`**: Text cleaning logic (`analyze_anomalies.py`).
- **`pipelines/uploading/`**: Deployment and Data Upload scripts.
    - `deploy_to_cloud_run.sh`: **One-click Deploy Script**.
    - `upload_pdfs_to_gcs.py`: Uploads PDF files to Google Cloud Storage.

---

## 💾 Data (`data/`)
Local storage for operational data.

- **`data/raw/`**: Original input files (`all_pdfs.zip`, `downloads/`).
- **`data/processed/`**: Cleaned data ready for AI (`dataset.jsonl`).
- **`data/logs/`**: Execution logs (`debug_*.txt`).

---

## 📚 Documentation
- `Agent_Journal.md`: **Dev Diary**. A story-like log of all changes made by the AI Agent.
- `PROJECT_MAP.md`: This file.
