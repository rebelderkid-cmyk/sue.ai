# SUE.AI Recreation Guide

This comprehensive guide allows you to recreate the **SUE.AI** platform (Legal RAG Assistant for Thai Law) from scratch. It includes the architecture overview, tech stack, configuration, and a "Mega Prompt" to generate the core codebase.

---

## 1. Executive Summary

**SUE.AI** is a high-performance **Legal RAG (Retrieval-Augmented Generation)** platform designed for Thai lawyers. It combines a **Go (Golang)** backend for speed and concurrency with a **Next.js** frontend for a polished user experience.

**Key Capabilities:**
*   **Hybrid Search:** Searches across ~1.2M Thai Supreme Court Rulings (Deka) and Legal Codes (Law) using Google Vertex AI Search.
*   **Intelligent RAG:** Uses **Gemini 3.0 Flash** to synthesize answers, assess legal risks, and provide strategic advice.
*   **Research Mode:** Generates comparison tables of relevant case laws with "Win/Lose" analysis.
*   **Streaming Response:** Real-time token streaming via Server-Sent Events (SSE).
*   **Citation Linking:** Automatically links legal citations to original PDF sources stored in Google Cloud Storage.

---

## 2. Tech Stack

| Component | Technology | Details |
| :--- | :--- | :--- |
| **Backend** | **Go (Golang) 1.23+** | Gin Framework, Native Concurrency for Parallel Search. |
| **Frontend** | **Next.js 16.1** | App Router, TypeScript, Tailwind CSS, Zustand (State Management), Framer Motion. |
| **AI Model** | **Gemini 3.0 Flash** | Fast, low-latency reasoning for legal summarization and intent classification. |
| **Search Engine** | **Vertex AI Search** | Two distinct engines: `DEKA` (Case Law) and `LAW` (Statutes). |
| **Infrastructure** | **Google Cloud Run** | Serverless container deployment. |
| **Storage** | **Google Cloud Storage** | PDF hosting for legal documents. |

---

## 3. The "Mega Prompt"

**Copy and paste the following block into a new AI session (e.g., Claude 3.5 Sonnet, Gemini 1.5 Pro) to generate the core system.**

***

**PROMPT STARTS HERE**

```markdown
I need you to build the **SUE.AI** platform, a Legal RAG system for Thai Law. 
The system consists of a **Go (Golang) Backend** and a **Next.js Frontend**.

### 1. Project Structure
Create the following directory structure:
```text
sue-ai/
├── src/
│   ├── backend-go/
│   │   ├── cmd/server/main.go
│   │   ├── internal/
│   │   │   ├── api/ (handlers.go, research_handler.go, routes.go)
│   │   │   ├── config/ (config.go)
│   │   │   ├── rag/ (service.go, search.go, types.go)
│   │   │   ├── agent/ (orchestrator.go)
│   │   ├── go.mod
│   │   ├── Dockerfile
│   ├── frontend/
│   │   ├── src/app/chat/page.tsx
│   │   ├── src/store/chatStore.ts
│   │   ├── package.json
├── deploy.sh
```

### 2. Backend Implementation (Go)

**`src/backend-go/internal/config/config.go`**
Load env vars: `PROJECT_ID`, `ENGINE_ID_DEKA`, `ENGINE_ID_LAW`, `GEMINI_API_KEY`.

**`src/backend-go/internal/rag/service.go`**
Initialize `discoveryengine.SearchClient` (Vertex AI) and `genai.Client` (Gemini 3.0 Flash).

**`src/backend-go/internal/rag/search.go`**
Implement a `Search` function that runs **parallel** searches against the `DEKA` and `LAW` Vertex AI engines.
- Use `sync.WaitGroup` to query both engines simultaneously.
- Struct `SearchResult`:
  ```go
  type SearchResult struct {
      Title    string `json:"title"`
      Link     string `json:"pdf_url"`
      Snippet  string `json:"snippet"`
      Source   string `json:"source"`   // "DEKA" or "LAW"
      ID       string `json:"id"`
      Year     string `json:"year"`
      Content  string `json:"content"`
  }
  ```
- Map the Vertex `discoveryenginepb.Document` to this struct. Construct PDF URLs:
  - DEKA: `https://storage.googleapis.com/sue-ai-pdfs-storage/{filename}`
  - LAW: `https://storage.googleapis.com/main_legal_data/pdfs/{filename}`

**`src/backend-go/internal/api/handlers.go`**
- `ChatStream`:
  1. Use `agent.IntentAnalyzer` to decide between "SEARCH" or "ANSWER" based on conversation history.
  2. If "SEARCH": Call `rag.Search` with the user's query.
  3. Construct a prompt for Gemini acting as a "Senior Legal Advisor".
  4. Stream the response using **Server-Sent Events (SSE)**.
  5. Send sources as a JSON event `{"type": "sources", "data": [...]}` before the stream ends.

**`src/backend-go/internal/api/research_handler.go`**
- `ResearchHandler`:
  1. Perform a broad search (fetch 15+ results).
  2. Use Gemini to select the **Top 5** most relevant cases.
  3. Generate a JSON comparison table:
     ```json
     [
       {
         "case_id": "1234/2565",
         "facts": "...",
         "ruling": "...",
         "lawyer_opinion": "..."
       }
     ]
     ```

**`src/backend-go/cmd/server/main.go`**
Setup Gin router, load config, init RAG service, register routes (`POST /api/chat`, `POST /api/research`), and start server on port 8080.

### 3. Frontend Implementation (Next.js)

**`src/frontend/src/store/chatStore.ts`**
Use `zustand` with `persist` middleware.
- Store `sessions` (id, messages, title).
- Actions: `addMessage`, `setActiveSession`, `createSession`.

**`src/frontend/src/app/chat/page.tsx`**
- Main Chat Interface.
- Fetch `POST /api/chat` and handle SSE streaming.
- Render markdown using `react-markdown`.
- **Custom Link Rendering**: Detect citations like `cite:deka:1234` or text matching "ฎีกาที่ ..." and render a clickable button that shows a hover card with the case summary/snippet.

### 4. Deployment

**`deploy.sh`**
- Build the Go backend container using `gcloud builds submit`.
- Deploy to Cloud Run using `gcloud run deploy` with environment variables.

**Requirements:**
- Use standard Go libraries + `github.com/gin-gonic/gin`, `cloud.google.com/go/discoveryengine`, `github.com/google/generative-ai-go`.
- Ensure the frontend looks modern (Tailwind CSS) and handles streaming text smoothly.
```
***

---

## 4. Configuration Guide

To make the system functional, you need to configure **Google Cloud**.

### 1. Google Cloud Setup
1.  **Project**: Create a GCP Project (e.g., `sue-ai-legal`).
2.  **Vertex AI Search**:
    *   Create an App named `sue-ai-search`.
    *   Create a Data Store (**Unstructured**) for **Deka** (Upload PDF files). Copy its `Engine ID`.
    *   Create a Data Store (**Unstructured**) for **Law** (Upload PDF files). Copy its `Engine ID`.
3.  **Gemini API**: Enable the "Vertex AI API" or generate an AI Studio API Key.

### 2. Environment Variables (`.env`)
Create a `.env` file in `src/backend-go/`:

```env
PORT=8080
GCP_PROJECT_ID=your-project-id
# Vertex AI Search Engine IDs
ENGINE_ID_DEKA=your-deka-engine-id
ENGINE_ID_LAW=your-law-engine-id
# Credentials
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_APPLICATION_CREDENTIALS=service-account.json
```

---

## 5. Deployment Steps

Once you have the code generated from the Mega Prompt:

1.  **Initialize Git**:
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    ```

2.  **Authenticate GCP**:
    ```bash
    gcloud auth login
    gcloud config set project your-project-id
    ```

3.  **Deploy Backend**:
    Make the script executable and run it:
    ```bash
    chmod +x deploy.sh
    ./deploy.sh
    ```
    *This will build the Go binary, wrap it in a Docker container, push to Google Container Registry, and deploy to Cloud Run.*

4.  **Frontend**:
    *   Locally: `cd src/frontend && npm install && npm run dev`.
    *   Production: Deploy the `src/frontend` folder to **Vercel**. Set the `NEXT_PUBLIC_API_URL` environment variable in Vercel to your Cloud Run URL.
