from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from src.database.connection import init_db
from src.api.routes import telemetry, predict, recommend, feedback, analytics

# LLM route is optional — won't crash if Ollama not installed
try:
    from src.api.routes import llm
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

app = FastAPI(
    title="Game Performance Copilot API",
    description="AI-powered game performance optimization — RTX 3050 Ti + i7-12650H",
    version="3.0.0",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # ← Vite (React) — THIS IS THE FIX
        "http://localhost:3000",
        "http://localhost:8501",
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── STARTUP ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    init_db()

    # Phase 7 — preload the RAG knowledge base + embedding model here,
    # at startup, rather than lazily on the first chat request. The
    # embedding model load alone takes several seconds; doing it lazily
    # meant the very first Copilot question stacked that load time on
    # top of telemetry fetch + Ollama's own response time, which could
    # exceed the frontend's 30s request timeout. Preloading here means
    # only uvicorn's startup takes the hit, and every real chat request
    # afterward is fast.
    if LLM_AVAILABLE:
        try:
            from src.llm.knowledge_base import _load_index, _get_embedder
            _get_embedder()   # loads all-MiniLM-L6-v2 into memory now
            _load_index()     # loads the FAISS index + chunks.json now
            print("[startup] Knowledge base preloaded successfully.")
        except Exception as e:
            # Non-fatal — Copilot still works without RAG context if this fails
            print(f"[startup] WARNING: Knowledge base preload failed: {e}")

# ─── HEALTH ──────────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
def health_check():
    model_loaded = Path("models/best_model.pkl").exists()
    return {
        "status": "healthy",
        "version": "3.0.0",
        "model_loaded": model_loaded,
        "database": "postgresql",
        "model_name": "LightGBM" if model_loaded else "not loaded",
    }

# ─── ROUTERS ─────────────────────────────────────────────────────────────────
app.include_router(telemetry.router,  prefix="/api", tags=["Telemetry"])
app.include_router(predict.router,    prefix="/api", tags=["Prediction"])
app.include_router(recommend.router,  prefix="/api", tags=["Recommendations"])
app.include_router(feedback.router,   prefix="/api", tags=["Feedback"])
app.include_router(analytics.router,  prefix="/api", tags=["Analytics"])

if LLM_AVAILABLE:
    app.include_router(llm.router, prefix="/api", tags=["LLM"])