# 🎮 Game Performance Copilot

An end-to-end AI system that helps PC gamers diagnose, predict, and optimize game performance in real time — combining machine learning, live hardware telemetry, a retrieval-augmented local LLM assistant, and full multi-user authentication.

![CI](https://github.com/SriVarshC/game-performance-copilot/actions/workflows/test.yml/badge.svg)

---

## 🚀 What It Does

Tools like MSI Afterburner show raw numbers but never explain **why** performance is bad. Game Performance Copilot:

- **Collects** live GPU/CPU/RAM telemetry continuously
- **Diagnoses** hardware bottlenecks automatically — GPU-bound, CPU-bound, VRAM pressure, thermal throttling, memory pressure, or balanced
- **Predicts** FPS, 1%-low FPS, and a composite health score using 4 specialized ML models
- **Recommends** ranked, severity-labeled optimizations with estimated FPS gain per action
- **Answers** natural language questions via a local LLM Copilot, grounded in your real-time hardware state through Retrieval-Augmented Generation (RAG)
- **Learns from its own usage** — helpful Copilot answers are automatically folded back into its knowledge base
- **Isolates every user's data** — full JWT authentication with per-user data scoping across telemetry, predictions, recommendations, and chat history
- **Monitors itself** — a full observability layer tracking request performance and errors in real time

---

## 🏗️ Architecture

```
        React + TypeScript (Vite)
                  │  JWT / REST
                  ▼
          FastAPI Backend
                  │
   ┌──────────────┼───────────────────┬─────────────────┐
   ▼              ▼                   ▼                 ▼
PostgreSQL      Ollama             LightGBM ×4      FAISS + sentence-
(users,        (llama3.2,          (FPS / low-FPS /  transformers
 telemetry,     GPU-accelerated)    bottleneck /       (RAG knowledge
 predictions,                       health score)       base)
 recs, chat,
 errors,
 requests)
```

Deployed as a 5-container Docker Compose stack: backend, frontend (nginx), PostgreSQL, Ollama, pgAdmin — with GPU passthrough configured for both live telemetry collection and LLM inference.

---

## 🧠 Machine Learning

Four specialized LightGBM models, all surfaced from a single `/predict` call:

| Model | Purpose |
|---|---|
| FPS Predictor | Best-estimate FPS from game settings + live hardware metrics |
| 1% Low FPS | Worst-case frame rate estimate |
| Bottleneck Classifier | GPU / CPU / MEMORY / THERMAL / BALANCED |
| Health Score | Composite 0–100 system health rating |

The winning FPS model (LightGBM, compared against XGBoost and RandomForest) scores **R²=0.9746, MAE=7.8 FPS** on a 5,000-session synthetic training set spanning 5 genres, 4 resolutions, 5 quality presets, ray tracing on/off, and 4 upscaling modes.

---

## 🤖 AI Copilot (RAG + Self-Improving Knowledge Base)

The Copilot doesn't just call an LLM — it retrieves relevant, vetted context before answering:

- **Local inference** via Ollama (llama3.2), GPU-accelerated, fully offline, no API costs
- **Retrieval-Augmented Generation** — a FAISS vector index over curated hardware/optimization knowledge, embedded locally with `sentence-transformers`
- **Live telemetry injection** — answers can be grounded in your actual current GPU/CPU/RAM state
- **Self-improving loop** — every answer can be rated helpful/not helpful; helpful, general-purpose answers are automatically embedded and folded back into the knowledge base, so the Copilot's knowledge grows from real usage over time

---

## 🔐 Authentication & Multi-User Isolation

- JWT-based auth (register/login), password hashing via `pbkdf2_sha256`
- **Every** piece of user-generated data — telemetry, predictions, recommendations, chat history — is scoped to the authenticated user via database-level foreign keys and query filtering
- Verified with real multi-account testing, not just code review

---

## 📊 Observability

- **Global exception handling** — every unhandled error across the entire API is caught centrally, logged with full context (endpoint, user, traceback), and never leaks internals to the client
- **Request performance monitoring** — every API call is timed and logged; a dedicated dashboard page visualizes average response time and request volume per endpoint, plus live error rates

---

## 🔌 Key API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/auth/register`, `/api/auth/login` | POST | Account creation and JWT issuance |
| `/api/telemetry`, `/api/telemetry/history` | GET | Live and historical hardware metrics |
| `/api/predict` | POST | 4-model FPS / bottleneck / health prediction |
| `/api/recommend` | POST | Ranked, severity-labeled optimization suggestions |
| `/api/llm/ask` | POST | RAG-grounded natural language Copilot |
| `/api/llm/feedback/{id}` | POST | Rate a Copilot answer (feeds the self-improving loop) |
| `/api/feedback/{id}`, `/api/feedback/summary` | POST / GET | Recommendation feedback + analytics |
| `/api/analytics` | GET | Per-user aggregated performance analytics |
| `/api/errors` | GET | Recent application errors |
| `/api/performance/summary` | GET | Request timing & volume analytics |

Interactive API docs: `http://localhost:8000/docs`

---

## 🧪 Testing & CI/CD

Full pytest suite covering auth, prediction, recommendations, feedback, and analytics, running automatically on every push via GitHub Actions against a real, freshly-provisioned PostgreSQL service container — including running Alembic migrations from scratch, so CI validates the exact same schema path a brand-new deployment would take.

---

## 🐳 Running Locally

**Full stack via Docker Compose:**
```bash
docker-compose --env-file .env.docker up -d
```
- Frontend: `http://localhost:5173`
- API: `http://localhost:8000` (docs at `/docs`)
- pgAdmin: `http://localhost:5050`

**Local development (backend + frontend separately):**
```bash
# Backend
uvicorn src.api.main:app --reload

# Frontend
cd frontend && npm run dev
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, React Router, ECharts |
| Backend | FastAPI, Pydantic, Uvicorn |
| Database | PostgreSQL, SQLAlchemy 2.0, Alembic |
| ML | LightGBM, XGBoost, RandomForest, scikit-learn |
| LLM / RAG | Ollama (llama3.2), FAISS, sentence-transformers |
| Auth | JWT (python-jose), pbkdf2_sha256 |
| Infra | Docker, Docker Compose, nginx |
| CI/CD | GitHub Actions, pytest |

---

## 🖥️ Reference Hardware

Developed and tuned against an NVIDIA RTX 3050 Ti Laptop GPU (4GB VRAM), Intel i7-12650H (10C/16T), 16GB RAM, Windows 11 — including working around real hardware quirks like NVIDIA Optimus (GPU powers off at idle) and VRAM-constrained local LLM inference (GPU/CPU workload splitting, resolved by tuning the model's context window to fit entirely in available VRAM).

---

## 👤 Author

**Srivarsh Cirigiri**
Master's Student, Data Analytics and Computational Social Science (DACSS)
University of Massachusetts Amherst | Graduating May 2027

[GitHub](https://github.com/SriVarshC) · [Repo](https://github.com/SriVarshC/game-performance-copilot)
