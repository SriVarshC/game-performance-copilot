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