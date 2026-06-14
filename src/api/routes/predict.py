"""
POST /api/predict
Predicts FPS for given game settings using the LightGBM model (R2=97.5%).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# ── Lazy singleton — model loads once, reused for all requests ───────────────
_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        from src.ml.predictor import FPSPredictor
        _predictor = FPSPredictor()
    return _predictor


# ── Request / Response Schemas ───────────────────────────────────────────────
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
        description="Ray tracing: 0=off, 1=on (causes ~48% FPS reduction on RTX 3050 Ti)",
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
    gpu_utilization: float = Field(85.0,  ge=0.0, le=100.0, description="GPU utilization %")
    vram_used_mb:    float = Field(2048.0, ge=0.0,           description="VRAM used in MB")
    cpu_utilization: float = Field(60.0,  ge=0.0, le=100.0, description="CPU utilization %")
    ram_utilization: float = Field(75.0,  ge=0.0, le=100.0, description="RAM utilization %")
    gpu_temperature: float = Field(75.0,  ge=0.0,            description="GPU temp Celsius")
    gpu_clock_mhz:   float = Field(1400.0, ge=0.0,           description="GPU core clock MHz")
    gpu_power_watts: float = Field(60.0,  ge=0.0,            description="GPU power watts")


class PredictResponse(BaseModel):
    predicted_fps:    float
    frame_time_ms:    float
    performance_tier: str
    model_name:       str


# ── Endpoint ─────────────────────────────────────────────────────────────────
@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Predict FPS",
    description=(
        "Predicts FPS using LightGBM (R2=97.5%, MAE=7.8 FPS).\n\n"
        "Performance tiers: Excellent >=144 | Playable >=60 | Acceptable >=30 | Poor <30"
    ),
)
def predict_fps(request: PredictRequest):
    try:
        predictor = get_predictor()

        # Bundle hardware metrics into the dict that predict() expects
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
            live_metrics=live_metrics,
            game_genre=request.game_genre,
            resolution=request.resolution,
            preset=request.preset,
            ray_tracing=bool(request.ray_tracing),  # int -> bool (0/1 -> False/True)
            upscaling=request.upscaling,
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return PredictResponse(
            predicted_fps=round(float(result["predicted_fps"]), 1),
            frame_time_ms=round(float(result["frame_time_ms"]), 2),
            performance_tier=result["performance_tier"],
            model_name=result["model_name"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")