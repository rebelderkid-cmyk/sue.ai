# Law5 AI (formerly Sue.AI) - The Legal Operating System 🤵⚖️

**Law5 AI** is a specialized Legal Assistant and Research Platform designed for Thai lawyers. It combines high-precision Retrieval-Augmented Generation (RAG) with a professional, lawyer-centric interface to analyze Supreme Court rulings (Deka), legal statutes, and provide strategic case advice.

![Law5 AI Platform](https://placehold.co/1200x600/1e1b4b/white?text=Law5+AI+Platform)

---

## 🚀 Features

### 1. 🤖 AI Legal Assistant (Chat)
- **Role:** Professional "Assistant to Lawyer" persona.
- **Capabilities:** Drafting legal documents, analyzing case facts, and suggesting legal strategies.
- **Evidence-Based:** Every answer is grounded in retrieved Deka (Supreme Court Rulings) or Statutory Law.
- **Smart Citations:** Inline clickable citations linking directly to sources.

### 2. ⚖️ Research Tool (Search)
- **AI Wisdom Search:** Uses hybrid ranking (Year + Keyword Density) to find the most relevant precedents.
- **Comparison Cards:** Side-by-side comparison of retrieved cases against user facts.
- **Vertical Analysis:** 'Fact', 'Legal Issue', 'Ruling', and 'AI Strategy' breakdown.
- **Mobile Optimized:** Responsive design with stacked cards for easy reading on phones.

---

## 🛠 Tech Stack

- **Frontend:** [Next.js 14](https://nextjs.org/) (App Router), Tailwind CSS, Framer Motion, Lucide React.
- **Backend:** [Go (Golang)](https://go.dev/) 1.21+, Gin Web Framework.
- **AI & RAG:** 
  - **LLM:** Google Gemini Pro 1.5 (via Vertex AI).
  - **Vector Search:** Google Cloud Discovery Engine.
- **Database:** Firebase/Firestore (Chat History), Local Caching.
- **Deployment:** Google Cloud Run (Backend), Vercel (Frontend).

---

## 📂 Project Structure

```bash
.
├── src/
│   ├── frontend/          # Next.js Application
│   │   ├── src/app/       # App Router Pages (Chat, Search)
│   │   ├── src/components/# UI Components (Sidebar, Hero, etc.)
│   │   └── ...
│   ├── backend-go/        # Go API Server
│   │   ├── cmd/server/    # Entry point
│   │   ├── internal/rag/  # RAG Logic (Search, Answer, Client)
│   │   └── ...
│   └── ...
├── deploy.sh              # One-click deployment script for Cloud Run
└── README.md              # Project Documentation
```

---

## ⚡ Getting Started (Local Development)

### Prerequisites
- Node.js 18+
- Go 1.21+
- Google Cloud Project with Vertex AI & Discovery Engine enabled.

### 1. Backend Setup
```bash
cd src/backend-go
cp .env.example .env
# Edit .env with your GCP Credentials:
# GCP_PROJECT_ID=...
# GEMINI_API_KEY=...
# ENGINE_ID_DEKA=...

go run cmd/server/main.go
# Server starts at http://localhost:8080
```

### 2. Frontend Setup
```bash
cd src/frontend
cp .env.local.example .env.local
# Set Backend URL:
# NEXT_PUBLIC_API_URL=http://localhost:8080

npm install
npm run dev
# App starts at http://localhost:3000
```

---

## ☁️ Deployment

### Backend (Google Cloud Run)
We use a helper script `deploy.sh` to build and deploy the Go backend container.

```bash
# Ensure you are authenticated with gcloud
gcloud auth login

# Run deployment script
./deploy.sh
```

### Frontend (Vercel)
Connect your GitHub repository to Vercel.
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Environment Variable:** Set `NEXT_PUBLIC_API_URL` to your Cloud Run Backend URL.

---

## 🤝 Contribution Guide

1. **Clone Repo:** `git clone https://github.com/rebelderkid-cmyk/sue.ai.git`
2. **Branch:** Create a feature branch `git checkout -b feat/new-feature`
3. **Commit:** Use semantic commit messages (e.g., `feat: add PDF export`, `fix: mobile layout`).
4. **Push:** `git push origin feat/new-feature`

---

## 🔐 Security Note
- **API Keys:** Never commit `.env` files. The `.gitignore` is configured to exclude them.
- **Access:** Ensure Google Cloud IAM permissions are correctly set for the Service Account used by the backend.

---

*© 2026 Law5 AI by Antigravity Team*
