"""
Game Performance Copilot — FastAPI Backend
Phase 3: REST API wrapping ML model, telemetry, diagnostics, recommendations.
Run: uvicorn src.api.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ── Lifespan: preload heavy models at startup so first request is instant ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("[API] Starting up — preloading LightGBM model...")
    try:
        from src.api.routes.predict import get_predictor
        get_predictor()
        print("[API] Model preloaded successfully.")
        print("[API] API ready   → http://localhost:8000")
        print("[API] Swagger UI  → http://localhost:8000/docs")
    except Exception as e:
        print(f"[API] Warning: Could not preload model at startup: {e}")

    yield  # ← server is running here

    # SHUTDOWN
    print("[API] Shutting down...")
    try:
        from src.api.routes import telemetry as tel_module
        if tel_module._collector is not None:
            tel_module._collector.cleanup()
            print("[API] TelemetryCollector cleaned up.")
    except Exception:
        pass


# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Game Performance Copilot API",
    description=(
        "REST API for the Game Performance Copilot.\n\n"
        "Provides:\n"
        "- **FPS Prediction** — LightGBM model, R2=97.5%, MAE=7.8 FPS\n"
        "- **Live Telemetry** — GPU / CPU / RAM / System metrics in real time\n"
        "- **AI Diagnostics** — 7 bottleneck types auto-detected\n"
        "- **Recommendations** — Up to 6 ranked optimizations with ML-estimated FPS gains\n\n"
        "Hardware: RTX 3050 Ti + i7-12650H + 16 GB RAM"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allows the Streamlit dashboard (port 8501) to call this API (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ─────────────────────────────────────────────────────────
from src.api.routes import predict, telemetry, recommend  # noqa: E402

app.include_router(predict.router,   prefix="/api", tags=["Prediction"])
app.include_router(telemetry.router, prefix="/api", tags=["Telemetry"])
app.include_router(recommend.router, prefix="/api", tags=["Recommendations"])


# ── Health Endpoint ──────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"], summary="API Health Check")
def health_check():
    """Check API status and confirm ML model is loaded."""
    # ✅ ALL variables initialized BEFORE try block
    # so return statement never hits NameError
    model_loaded = False
    model_name   = "unknown"
    trained_at   = "unknown"

    try:
        meta_path = os.path.join("models", "model_meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
            model_name   = meta.get("best_model", "unknown")
            trained_at   = meta.get("trained_at",  "unknown")
            model_loaded = True
    except Exception:
        pass

    return {
        "status":       "healthy",
        "model_loaded": model_loaded,
        "model_name":   model_name,
        "trained_at":   trained_at,
        "api_version":  "1.0.0",
    }


# ── Root ─────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "project": "Game Performance Copilot",
        "version": "1.0.0",
        "endpoints": {
            "health":      "GET  /api/health",
            "telemetry":   "GET  /api/telemetry",
            "diagnostics": "GET  /api/telemetry/diagnostics",
            "predict":     "POST /api/predict",
            "recommend":   "POST /api/recommend",
        },
        "docs":  "/docs",
        "redoc": "/redoc",
    }