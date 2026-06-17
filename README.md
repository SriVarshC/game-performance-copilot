# 🎮 Game Performance Copilot

An end-to-end AI system that helps PC gamers diagnose, predict, and optimize game performance in real time using machine learning, live hardware telemetry, and a natural language LLM assistant.

---

## 🚀 What It Does

Current tools like MSI Afterburner show raw numbers but never explain **why** performance is bad. Game Performance Copilot:

- **Collects** live GPU/CPU/RAM telemetry every 2 seconds
- **Diagnoses** 7 types of hardware bottlenecks automatically (GPU-bound, CPU-bound, VRAM pressure, thermal throttling, and more)
- **Predicts** FPS using a LightGBM model (R²=97.5%, MAE=7.8 FPS)
- **Recommends** ranked optimizations with estimated FPS gain per action
- **Answers** natural language questions about your hardware via an LLM assistant
- **Learns** from user feedback (thumbs up/down) with a full analytics dashboard

---

## 🏗️ Architecture

```
Hardware (GPU/CPU/RAM)
        │
        ▼
TelemetryCollector (pynvml + psutil)
        │
        ├──▶ DiagnosticsEngine (7 bottleneck detectors)
        │
        ├──▶ FPSPredictor (LightGBM R²=0.9746)
        │           │
        │           └──▶ RecommendationEngine (ranked optimizations + FPS gain estimates)
        │
        ├──▶ SQLite DB (telemetry + recommendations + feedback)
        │
        └──▶ Streamlit Dashboard (9 sections, live refresh)
                    │
                    └──▶ FastAPI Backend (8 endpoints)
                                │
                                └──▶ Ollama LLM (llama3.2, prompt-injected with live telemetry)
```

---

## 🧠 ML Model

| Model | R² | MAE (FPS) | RMSE | Accuracy |
|---|---|---|---|---|
| **LightGBM ★ BEST** | **0.9746** | **7.825** | **12.348** | **91.64%** |
| XGBoost | 0.9697 | 8.298 | 13.484 | 91.32% |
| RandomForest | 0.8924 | 16.105 | 25.404 | 81.34% |

- **Dataset:** 5,000 synthetic gaming sessions based on real hardware benchmark distributions
- **Split:** 80% train / 20% test
- **Features:** 20 inputs including game genre, resolution, quality preset, ray tracing, upscaling, GPU/CPU/RAM metrics
- **Winner:** LightGBM saved as `models/best_model.pkl`

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | API status + model loaded check |
| `/api/telemetry` | GET | Live GPU/CPU/RAM metrics |
| `/api/telemetry/diagnostics` | GET | AI bottleneck analysis |
| `/api/predict` | POST | FPS prediction from game settings + metrics |
| `/api/recommend` | POST | Ranked optimization recommendations |
| `/api/llm/ask` | POST | Natural language hardware Q&A (Ollama) |
| `/api/feedback/{id}` | POST | Submit thumbs up/down on a recommendation |
| `/api/feedback/summary` | GET | Aggregated feedback analytics |

Swagger UI: `http://localhost:8000/docs`

---

## 🧪 Tests

```
pytest tests/ -v
```

| File | Tests | Covers |
|---|---|---|
| `test_health.py` | 5 | API health, model loaded, version |
| `test_predict.py` | 7 | FPS prediction, frame time, performance tier |
| `test_recommend.py` | 7 | Recommendations count, fields, status |
| `test_feedback.py` | 9 | Feedback submission, summary stats, IDs |
| **Total** | **28** | **All passing ✅** |

CI/CD: GitHub Actions runs all 28 tests on `ubuntu-latest` on every push to `main`.

![CI](https://github.com/SriVarshC/game-performance-copilot/actions/workflows/test.yml/badge.svg)

---

## 🐳 Docker

```bash
# Build images (one at a time)
docker build -t game-copilot-api .
docker build -t game-copilot-dashboard -f Dockerfile.dashboard .

# Run full stack
docker-compose up
```

- Dashboard: `http://localhost:8501`
- API: `http://localhost:8000`

---

## ⚡ Local Development (Recommended)

```bash
# Activate virtual environment
venv\Scripts\activate          # Windows PowerShell

# Terminal 1 — FastAPI backend
uvicorn src.api.main:app --reload --port 8000

# Terminal 2 — Streamlit dashboard
streamlit run src/dashboard/app.py

# Terminal 3 — Tests / Git
pytest tests/ -v
```

---

## 📁 Project Structure

```
game-performance-copilot/
├── src/
│   ├── telemetry/collector.py          # GPU/CPU/RAM metrics (pynvml + psutil)
│   ├── database/db_manager.py          # SQLite manager
│   ├── diagnostics/engine.py           # 7 bottleneck detectors
│   ├── ml/
│   │   ├── dataset_generator.py        # 5000 synthetic training samples
│   │   ├── trainer.py                  # Trains XGB/LGB/RF, saves best model
│   │   ├── predictor.py                # LightGBM inference
│   │   └── recommendation_engine.py    # Ranked optimizations + FPS gain estimates
│   ├── api/
│   │   ├── main.py                     # FastAPI app (v2.0.0)
│   │   └── routes/                     # predict, recommend, telemetry, llm, feedback
│   ├── dashboard/app.py                # Streamlit dashboard (9 sections)
│   └── llm/prompt_builder.py           # Telemetry-aware prompt injection
├── tests/                              # 28 pytest tests
├── models/                             # Trained model files (best_model.pkl)
├── data/                               # SQLite database (auto-created)
├── Dockerfile                          # FastAPI container
├── Dockerfile.dashboard                # Streamlit container
├── docker-compose.yml                  # Full stack orchestration
└── .github/workflows/test.yml          # GitHub Actions CI/CD
```

---

## 🖥️ Hardware Tested On

| Component | Spec |
|---|---|
| GPU | NVIDIA GeForce RTX 3050 Ti Laptop (4GB VRAM) |
| CPU | Intel i7-12650H (10C/16T) |
| RAM | 16 GB |
| OS | Windows 11 |

> **Note:** GPU telemetry uses NVIDIA Optimus awareness — the dGPU powers down when idle, which is normal behavior and handled correctly.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Hardware Metrics | pynvml, psutil |
| ML Models | LightGBM, XGBoost, scikit-learn |
| Backend API | FastAPI, Uvicorn |
| Database | SQLite, SQLAlchemy |
| Dashboard | Streamlit, Plotly |
| LLM Assistant | Ollama, llama3.2 |
| Testing | pytest |
| DevOps | Docker, GitHub Actions |
| Language | Python 3.12 |

---

## 📈 Phases Completed

| Phase | What Was Built | Status |
|---|---|---|
| 1 | Live telemetry collection + Streamlit dashboard | ✅ Complete |
| 2 | ML FPS prediction (LightGBM) + recommendation engine | ✅ Complete |
| 3 | FastAPI REST backend (8 endpoints + Swagger) | ✅ Complete |
| 4 | LLM assistant (Ollama + llama3.2 + prompt engineering) | ✅ Complete |
| 5 | Docker + docker-compose + GitHub Actions CI/CD (28 tests) | ✅ Complete |
| 6 | User feedback loop (👍/👎 + analytics dashboard) | ✅ Complete |

---

## 👤 Author

**Srivarsh Cirigiri**  
Master's Student — Data Science   
University of Massachusetts Amherst | Graduation: May 2027