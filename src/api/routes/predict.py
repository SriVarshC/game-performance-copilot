"""
POST /api/predict
Predicts FPS using all 4 ML models:
  Model 1 — predicted_fps        (LightGBM, R2=97.6%)
  Model 2 — low_1pct_fps         (worst-case FPS)
  Model 3 — bottleneck_class     (GPU/CPU/THERMAL/MEMORY/BALANCED)
  Model 4 — health_score         (0-100)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# ── Lazy singleton ────────────────────────────────────────────────────────────
_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        from src.ml.predictor import FPSPredictor
        _predictor = FPSPredictor()
    return _predictor


# ── Request Schema ────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    # Game settings (required)
    game_genre: str = Field(
        ...,
        example="fps_competitive",
        description=(
            "Game genre. Options: fps_competitive, fps_aaa, rpg_open_world, "
            "moba, battle_royale, racing, strategy"
        ),
    )
    resolution: str = Field(
        ...,
        example="1920x1080",
        description="Options: 1280x720, 1920x1080, 2560x1440, 3840x2160",
    )
    preset: str = Field(
        ...,
        example="high",
        description="Options: low, medium, high, ultra, epic",
    )
    ray_tracing: int = Field(
        0, ge=0, le=1,
        description="Ray tracing: 0=off, 1=on (~48% FPS penalty on RTX 3050 Ti)",
    )
    upscaling: str = Field(
        "none",
        example="none",
        description=(
            "Upscaling mode. Options: none, dlss_quality, dlss_balanced, "
            "dlss_performance, fsr_quality, fsr_balanced"
        ),
    )

    # Hardware metrics (optional — defaults = typical RTX 3050 Ti gaming load)
    gpu_utilization: float = Field(85.0,   ge=0.0, le=100.0, description="GPU utilization %")
    vram_used_mb:    float = Field(2048.0, ge=0.0,            description="VRAM used in MB")
    cpu_utilization: float = Field(60.0,   ge=0.0, le=100.0, description="CPU utilization %")
    ram_utilization: float = Field(75.0,   ge=0.0, le=100.0, description="RAM utilization %")
    gpu_temperature: float = Field(75.0,   ge=0.0,            description="GPU temp Celsius")
    gpu_clock_mhz:   float = Field(1400.0, ge=0.0,            description="GPU core clock MHz")
    gpu_power_watts: float = Field(60.0,   ge=0.0,            description="GPU power watts")


# ── Response Schema ───────────────────────────────────────────────────────────
class PredictResponse(BaseModel):
    # Model 1
    predicted_fps:    float
    frame_time_ms:    float
    performance_tier: str
    model_name:       str
    # Model 2
    low_1pct_fps:     Optional[float] = None
    # Model 3
    bottleneck_class: Optional[str]   = None
    # Model 4
    health_score:     Optional[float] = None


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Predict FPS + Bottleneck + Health Score",
    description=(
        "Runs all 4 ML models and returns complete performance analysis.\n\n"
        "**Model 1** — Average FPS (LightGBM, R2=97.6%, MAE=7.6 FPS)\n"
        "**Model 2** — 1% Low FPS (worst-case frame spikes)\n"
        "**Model 3** — Bottleneck class (GPU/CPU/THERMAL/MEMORY/BALANCED)\n"
        "**Model 4** — Health score 0-100 (overall system performance rating)\n\n"
        "Performance tiers: Excellent >=144 | Playable >=60 | Acceptable >=30 | Poor <30"
    ),
)
def predict_fps(request: PredictRequest):
    try:
        predictor = get_predictor()

        live_metrics = {
            "gpu_utilization": request.gpu_utilization,
            "vram_used_mb":    request.vram_used_mb,
            "cpu_utilization": request.cpu_utilization,
            "ram_utilization": request.ram_utilization,
            "gpu_temperature": request.gpu_temperature,
            "gpu_clock_mhz":   request.gpu_clock_mhz,
            "gpu_power_watts": request.gpu_power_watts,
        }

        result = predictor.predict(
            live_metrics = live_metrics,
            game_genre   = request.game_genre,
            resolution   = request.resolution,
            preset       = request.preset,
            ray_tracing  = bool(request.ray_tracing),
            upscaling    = request.upscaling,
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return PredictResponse(
            predicted_fps    = round(float(result["predicted_fps"]), 1),
            frame_time_ms    = round(float(result["frame_time_ms"]), 2),
            performance_tier = result["performance_tier"],
            model_name       = result["model_name"],
            low_1pct_fps     = round(float(result["low_1pct_fps"]), 1)
                               if result.get("low_1pct_fps") else None,
            bottleneck_class = result.get("bottleneck_class"),
            health_score     = round(float(result["health_score"]), 1)
                               if result.get("health_score") else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )