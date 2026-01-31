# Sue.AI Data Architecture V2 (Clean & Structured)

## 🚨 Status Dashboard
- **Backend**: Go (Cloud Run & Localhost)
- **Frontend**: Next.js (Vercel & Cloud Run)
- **AI Model**: Gemini 2.0 Flash (Vertex AI) via API Key
- **Search System**: Vertex AI Agent Builder (Structured Data)

## 🗺️ Index Mapping

### 1. Deka (Supreme Court Cases)
| Category | GCS Source (`gs://main_legal_data/...`) | Vertex Data Store ID | Engine Used |
| :--- | :--- | :--- | :--- |
| **Civil** | `structured_flat_v2/deka-civil/*.jsonl` | `deka-civil-clean` | *(Unused)* |
| **Criminal** | `structured_flat_v2/deka-criminal/*.jsonl` | `deka-criminal-struct` | *(Unused)* |
| **Labor** | `structured_flat_v2/deka-labor/*.jsonl` | `deka-labor-struct` | *(Unused)* |
| **General** | `structured_flat_v2/deka-general/*.jsonl` | `deka-general-struct` | *(Unused)* |
| **Legacy** | *(Unknown)* | `deka_1768730204117` | **`sue-ai-search_1768730959752`** (Active) |

> **Note:** Backend uses the Legacy Engine for Deka queries as per user request. The new structured stores are ready but currently idle for Deka.

### 2. Law (Legislation & Acts)
| Category | GCS Source (`gs://main_legal_data/...`) | Vertex Data Store ID | Engine Used |
| :--- | :--- | :--- | :--- |
| **Civil** | `structured_flat_v2/law-civil/*.jsonl` | `law-civil-clean` | `law-ultimate-struct` |
| **Criminal** | `structured_flat_v2/law-criminal/*.jsonl` | `law-criminal-struct` | `law-ultimate-struct` |
| **Labor** | `structured_flat_v2/law-labor/*.jsonl` | `law-labor-struct` | `law-ultimate-struct` |
| **General** | `structured_flat_v2/law-general/*.jsonl` | `law-general-struct` | `law-ultimate-struct` |

> **Critical Note:** The `law-criminal` source data currently lacks the full "Criminal Code" text (only amendments/announcements). Manual injection of key sections (e.g., 288, 289) has been performed to demonstrate capability.

## 🛠️ Configuration
- **Backend Config**: `src/backend-go/config/config.go`
- **Frontend Config**: `src/frontend/next.config.ts` (API URL Hardcoded)
- **Import Scripts**: `scripts/import_structured_v1.py`
