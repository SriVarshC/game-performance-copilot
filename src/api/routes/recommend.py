"""
POST /api/recommend
Returns ranked optimization recommendations with ML-predicted FPS gains.
Actual method signature: generate(live_metrics, game_genre, resolution, 
                                  preset, ray_tracing: bool, upscaling, issues)
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# ── Lazy singletons ──────────────────────────────────────────────────────────
_predictor  = None
_rec_engine = None
_db         = None                          # ← NEW


def get_rec_engine():
    global _predictor, _rec_engine
    if _predictor is None:
        from src.ml.predictor import FPSPredictor
        _predictor = FPSPredictor()
    if _rec_engine is None:
        from src.ml.recommendation_engine import RecommendationEngine
        _rec_engine = RecommendationEngine(_predictor)
    return _rec_engine


def get_db():                               # ← NEW
    global _db
    if _db is None:
        from src.database.db_manager import DatabaseManager
        _db = DatabaseManager()
    return _db


# ── Request Schema ───────────────────────────────────────────────────────────
class HardwareMetrics(BaseModel):
    gpu_utilization:  float = Field(0.0,  ge=0, le=100)
    vram_used_mb:     float = Field(0.0,  ge=0)
    vram_utilization: float = Field(0.0,  ge=0, le=100)
    cpu_utilization:  float = Field(0.0,  ge=0, le=100)
    ram_utilization:  float = Field(0.0,  ge=0, le=100)
    gpu_temperature:  float = Field(0.0,  ge=0)
    gpu_clock_mhz:    float = Field(0.0,  ge=0)
    gpu_power_watts:  float = Field(0.0,  ge=0)


class RecommendRequest(BaseModel):
    # Game settings — required
    game_genre:  str = Field(..., example="fps_aaa")
    resolution:  str = Field(..., example="2560x1440")
    preset:      str = Field(..., example="ultra")
    ray_tracing: int = Field(0, ge=0, le=1,
                             description="0=off, 1=on")
    upscaling:   str = Field("none", example="none")

    # Optional — enables hardware-aware recommendations
    metrics: Optional[HardwareMetrics] = Field(
        None,
        description=(
            "Live hardware metrics. Enables: Close Background Apps, "
            "Lower Textures, Free RAM, Use Cooling Pad recommendations."
        ),
    )
    diagnostics: Optional[List[Dict[str, Any]]] = Field(
        None,
        description=(
            "Issues list from GET /api/telemetry/diagnostics. "
            "Pass the 'issues' array for context-aware recommendations."
        ),
    )


# ── Endpoint ─────────────────────────────────────────────────────────────────
@router.post(
    "/recommend",
    summary="Get Optimization Recommendations",
    description=(
        "Returns up to 6 ranked optimization recommendations with ML-predicted FPS gains.\n\n"
        "**Settings-based:** Disable Ray Tracing, Enable DLSS, Enable FSR, "
        "Lower Preset, Lower Resolution, Preset+DLSS Combo\n\n"
        "**Hardware-based (pass metrics + diagnostics):** "
        "Close Background Apps, Lower Textures, Free RAM, Use Cooling Pad\n\n"
        "Sorted by estimated FPS gain (highest first)."
    ),
)
def get_recommendations(request: RecommendRequest):
    try:
        engine = get_rec_engine()

        # Build live_metrics dict — use provided values or empty dict
        if request.metrics:
            live_metrics = {
                "gpu_utilization":  request.metrics.gpu_utilization,
                "vram_used_mb":     request.metrics.vram_used_mb,
                "vram_utilization": request.metrics.vram_utilization,
                "cpu_utilization":  request.metrics.cpu_utilization,
                "ram_utilization":  request.metrics.ram_utilization,
                "gpu_temperature":  request.metrics.gpu_temperature,
                "gpu_clock_mhz":    request.metrics.gpu_clock_mhz,
                "gpu_power_watts":  request.metrics.gpu_power_watts,
            }
        else:
            live_metrics = {}

        issues = request.diagnostics or []

        # Exact method signature: generate(live_metrics, game_genre, resolution,
        #                                  preset, ray_tracing: bool, upscaling, issues)
        recommendations = engine.generate(
            live_metrics=live_metrics,
            game_genre=request.game_genre,
            resolution=request.resolution,
            preset=request.preset,
            ray_tracing=bool(request.ray_tracing),  # int -> bool
            upscaling=request.upscaling,
            issues=issues,
        )

        # ── Store to DB + attach ID to each recommendation ────────────────────
        # ← NEW BLOCK — every rec gets saved and gets an id back
        db = get_db()
        for rec in recommendations:
            rec_id = db.insert_recommendation(
                recommendation   = rec.get("action", ""),
                estimated_fps_gain = float(rec.get("estimated_fps_gain", 0)),
                category         = rec.get("category", "general")
            )
            rec["id"] = rec_id      # attach so caller can submit feedback later

        return {
            "status": "success",
            "game_settings": {
                "game_genre":  request.game_genre,
                "resolution":  request.resolution,
                "preset":      request.preset,
                "ray_tracing": request.ray_tracing,
                "upscaling":   request.upscaling,
            },
            "count":           len(recommendations),
            "recommendations": recommendations,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendations failed: {str(e)}"
        )