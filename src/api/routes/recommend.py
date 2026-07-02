"""
POST /api/recommend
Returns ranked optimization recommendations with ML-predicted FPS gains.
Saves recommendations to PostgreSQL.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import Recommendation as RecommendationModel

router = APIRouter()

# ── Lazy singletons ──────────────────────────────────────────────────────────
_predictor  = None
_rec_engine = None


def get_rec_engine():
    global _predictor, _rec_engine
    if _predictor is None:
        from src.ml.predictor import FPSPredictor
        _predictor = FPSPredictor()
    if _rec_engine is None:
        from src.ml.recommendation_engine import RecommendationEngine
        _rec_engine = RecommendationEngine(_predictor)
    return _rec_engine


# ── Request Schema ───────────────────────────────────────────────────────────
class HardwareMetrics(BaseModel):
    gpu_utilization:  float = Field(0.0, ge=0, le=100)
    vram_used_mb:     float = Field(0.0, ge=0)
    vram_utilization: float = Field(0.0, ge=0, le=100)
    cpu_utilization:  float = Field(0.0, ge=0, le=100)
    ram_utilization:  float = Field(0.0, ge=0, le=100)
    gpu_temperature:  float = Field(0.0, ge=0)
    gpu_clock_mhz:    float = Field(0.0, ge=0)
    gpu_power_watts:  float = Field(0.0, ge=0)


class RecommendRequest(BaseModel):
    game_genre:  str = Field(..., example="fps_aaa")
    resolution:  str = Field(..., example="2560x1440")
    preset:      str = Field(..., example="ultra")
    ray_tracing: int = Field(0, ge=0, le=1, description="0=off, 1=on")
    upscaling:   str = Field("none", example="none")
    metrics:     Optional[HardwareMetrics] = Field(None)
    diagnostics: Optional[List[Dict[str, Any]]] = Field(None)


# ── Endpoint ─────────────────────────────────────────────────────────────────
@router.post(
    "/recommend",
    summary="Get Optimization Recommendations",
    description=(
        "Returns up to 6 ranked optimization recommendations with "
        "ML-predicted FPS gains. Sorted by estimated FPS gain (highest first).\n\n"
        "Each recommendation includes an 'id' field for submitting feedback."
    ),
)
def get_recommendations(
    request: RecommendRequest,
    db: Session = Depends(get_db),
):
    try:
        engine = get_rec_engine()

        # Build live_metrics dict
        live_metrics = {}
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

        issues = request.diagnostics or []

        recommendations = engine.generate(
            live_metrics = live_metrics,
            game_genre   = request.game_genre,
            resolution   = request.resolution,
            preset       = request.preset,
            ray_tracing  = bool(request.ray_tracing),
            upscaling    = request.upscaling,
            issues       = issues,
        )

        # ── Save each rec to PostgreSQL + attach its ID ───────────────────────
        for rec in recommendations:
            db_rec = RecommendationModel(
                message            = rec.get("action", ""),
                severity           = rec.get("severity", "MEDIUM"),
                category           = rec.get("category", "general"),
                estimated_fps_gain = float(rec.get("estimated_fps_gain", 0)),
            )
            db.add(db_rec)
            db.flush()                          # assigns recommendation_id
            rec["id"] = db_rec.recommendation_id

        db.commit()

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
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Recommendations failed: {str(e)}"
        )