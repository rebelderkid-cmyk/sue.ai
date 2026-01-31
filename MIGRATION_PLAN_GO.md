# 🦅 Operation Golden Go: Python to Golang Migration Plan

**Objective**: Migrate the Sue.AI Backend from Python (FastAPI) to Golang (Gin) for high performance, reduced latency (cold starts), and minimal docker image size.

## 📂 Source Code Audit

| Python File | Core Responsibility | Go Replacement Strategy |
| :--- | :--- | :--- |
| `main.py` | FastAPI Server, SSE Streaming, Routes | **Gin** (`github.com/gin-gonic/gin`) for HTTP & Streaming |
| `rag_core.py` | Vertex AI Search, Gemini GenAI, Logic | **Official Google Cloud Go SDKs** (`discoveryengine`, `genai`) |
| `models.py` | SQLAlchemy ORM Models, Enums | **GORM** (`gorm.io/gorm`) with Struct Tags |
| `auth.py` | Firebase Auth (JWT Verify) | **Firebase Admin Go SDK** (`firebase.google.com/go`) |
| `database.py`| DB Connection (SQLite/Postgres) | **GORM Driver** (`gorm.io/driver/sqlite` / `postgres`) |
| `Dockerfile` | Python 3.10 Slim Image (~150MB) | **Multi-Stage Build** (Builder -> Scratch/Distroless ~10MB) |

---

## 🏗️ Proposed Go Project Structure (Standard Layout)

```
src/backend-go/
├── cmd/
│   └── server/
│       └── main.go         # Entry point (Main Loop)
├── internal/
│   ├── api/
│   │   ├── handlers.go     # HTTP Handlers (Chat, Healthcheck)
│   │   └── routes.go       # Gin Router Setup
│   ├── auth/
│   │   └── middleware.go   # Firebase Verify Token Middleware
│   ├── config/
│   │   └── config.go       # Load Env Vars (godotenv)
│   ├── database/
│   │   └── db.go           # GORM Connection & AutoMigrate
│   ├── models/
│   │   └── schema.go       # Struct Definitions
│   └── rag/
│       ├── client.go       # Init Vertex/Gemini Clients
│       ├── search.go       # "retriever" logic (Vertex)
│       ├── generate.go     # "answer_synthesizer" logic (Gemini)
│       └── service.go      # Business Logic Wrapper
├── go.mod                  # Go Modules
├── go.sum
└── Dockerfile              # Optimizer Multi-Stage Dockerfile
```

---

## 🛠️ Step-by-Step Implementation Plan

### Phase 1: Foundation (Setup)
1. Initialize Go Module: `go mod init sue-ai-backend`.
2. Install Core Libs:
   - `go get github.com/gin-gonic/gin` (Web Framework)
   - `go get github.com/joho/godotenv` (Environment)
   - `go get gorm.io/gorm` (ORM)
   - `go get firebase.google.com/go` (Auth)

### Phase 2: Domain Logic (The Brain)
3. **Data Models**: Port `models.py` to Go Structs with JSON and GORM tags.
4. **Google Clients**: Setup `discoveryengine` client and `genai` client.
   - *Risk*: Ensure `discoveryengine` Go SDK supports Multi-DataStore querying (iterate loop).
   - *Action*: Replicate `smart_query_optimizer` using `genai` model.

### Phase 3: API & Streaming (The Voice)
5. **Streaming Response**: Implement Server-Sent Events (SSE) in Gin.
   - Go handles concurrency natively using Channels (`chan string`).
   - The Chat Handler will spawn a goroutine to fetch/generate answers and push to the channel.

### Phase 4: Deployment (The Body)
6. **Dockerfile**:
   - **Stage 1 (Builder)**: `golang:1.23-alpine`. Compile `main.go` -> `server`.
   - **Stage 2 (Runner)**: `gcr.io/distroless/static`. Copy binary + `.env` (optional).
   - **Result**: Image size drop from ~150MB to ~20MB.

---

## ⚠️ Key Differences & Pitfalls to Avoid

1.  **JSON Handling**:
    - Python is loose with JSON. Go is strict.
    - **Action**: Must verify `struct` tags match Vertex AI response fields exactly (e.g. `filename` vs `file_name`).

2.  **Env Vars**:
    - Go needs explicit loading of `.env` in local dev. In Cloud Run, it reads OS envs natively.

3.  **Vertex Protobufs**:
    - Retrieving map/struct data from Vertex AI in Go requires type casting `*structpb.Struct`. This is more verbose than Python's `dict()`.

4.  **Concurrency Safety**:
    - Since `rag_core` logic will run in Goroutines, ensure the Clients (Vertex/Gemini) are thread-safe (Standard Google Clients are safe).

## 🚀 Execution Command
If you verify this plan, I can start by creating the directory structure and implementing the **Main Server** and **RAG Logic** immediately.
