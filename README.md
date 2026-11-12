# 🎓 AI-Powered Student Performance & Career Guidance System

An **IBM Bob Agentic AI** production platform that analyzes academic performance, detects skill gaps, recommends career paths, generates personalized learning roadmaps, analyzes resumes, and prepares students for interviews using a **multi-agent LLM system**.

---

## 📐 Architecture

```
Frontend (React 18 + TailwindCSS)
         ↕ REST + WebSocket
    FastAPI Backend (Python 3.11)
         ↕
   LiteLLM Gateway (IBM watsonx + OpenAI + Anthropic)
         ↕
 LangGraph Multi-Agent Orchestrator
  ├─ Academic Performance Agent  (IBM watsonx granite-13b)
  ├─ Skill Gap Detection Agent   (OpenAI GPT-4o)
  ├─ Career Recommendation Agent (Anthropic Claude 3.5)
  ├─ Learning Path Generator     (OpenAI GPT-4o)
  ├─ Resume Analysis Agent       (Anthropic Claude 3.5)
  └─ Interview Preparation Agent (IBM watsonx + OpenAI)
         ↕
   MCP Tool Server (Node.js/TypeScript)
   ├─ search_jobs · lookup_courses
   ├─ generate_qna · ats_check
   └─ search_career_info
         ↕
 Memory: ChromaDB (vectors) + Redis (sessions)
 Storage: PostgreSQL + MinIO
 Observability: LangSmith + Prometheus + Grafana
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local dev)
- Node.js 20+ (for MCP server and frontend)

### 2. Clone & configure
```bash
git clone <repo-url>
cd student-ai-platform/backend
cp .env.example .env
# Fill in your API keys in .env
```

### 3. Start all services with Docker Compose
```bash
cd infra
docker compose up -d
```

Services started:
| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| MinIO Console | http://localhost:9001 |

### 4. Local development (backend)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 5. Local development (frontend)
```bash
cd frontend
npm install
npm run dev
```

### 6. MCP Server
```bash
cd mcp-server
npm install
npm run dev
```

---

## 🤖 AI Agents

| Agent | LLM | Key Function |
|---|---|---|
| Academic Performance | IBM watsonx granite-13b | CGPA analysis, weakness detection |
| Skill Gap Detection | OpenAI GPT-4o | Role vs. skills delta, market ranking |
| Career Recommendation | Anthropic Claude 3.5 | Top-5 role matching with scores |
| Learning Path Generator | OpenAI GPT-4o | Week-by-week roadmap + courses |
| Resume Analysis | Anthropic Claude 3.5 | ATS scoring, improvements |
| Interview Preparation | IBM watsonx + OpenAI | Q gen + HITL answer evaluation |

---

## 🔒 Security & Governance

- **JWT auth** with role-based access (Student / Faculty / Admin)
- **Prompt injection defense** — input preprocessing strips adversarial patterns
- **Guardrails AI** output validators — no PII leakage, no hallucinated data
- **Token budget** — per-user daily spend cap enforced via Redis
- **HITL** — low-confidence agent outputs routed to admin review queue
- **Audit log** — every agent call stored in `agent_sessions` table
- **Policy engine** — agents restricted to approved MCP tool whitelist

---

## 📊 Observability

- **LangSmith** — per-agent trace visualization
- **Prometheus** — agent latency, token cost, error rate metrics
- **Grafana** — pre-built dashboards at `http://localhost:3000`
- **structlog** — structured JSON logging throughout

---

## 🧪 Tests

```bash
cd backend
pytest tests/ -v
```

---

## 📁 Project Structure

```
student-ai-platform/
├── backend/          # FastAPI + agents + LLM gateway
├── mcp-server/       # Custom MCP tool server (Node.js/TypeScript)
├── frontend/         # React 18 + Vite + TailwindCSS dashboard
├── infra/            # Docker Compose, Nginx, Prometheus config
└── .github/          # GitHub Actions CI/CD
```

---

## 🌐 API Reference

Full interactive docs: `http://localhost:8000/docs`

Key endpoints:
- `POST /auth/register` — Student/admin registration
- `POST /auth/login` — JWT login
- `POST /academic/records/bulk` — Upload semester marks
- `GET /academic/analytics` — CGPA and subject analytics
- `POST /agents/full-pipeline` — Run all 4 core agents
- `POST /agents/analyze-performance` — Academic agent only
- `POST /agents/detect-skill-gaps` — Skill gap agent only
- `POST /agents/career-recommendations` — Career agent only
- `POST /agents/learning-path` — Learning path agent only
- `POST /resume/upload` — Upload PDF resume
- `POST /resume/analyze/{id}` — Resume analysis agent
- `POST /agents/interview/start` — Generate interview questions
- `POST /agents/interview/evaluate` — Evaluate answer with HITL
- `GET /admin/dashboard` — Admin overview
- `GET /admin/token-usage` — LLM cost monitoring
- `GET /admin/hitl-queue` — HITL review queue
- `GET /metrics` — Prometheus scrape endpoint

---

*Built with IBM Bob · Multi-Agent Agentic AI · LangGraph · LiteLLM · ChromaDB*
