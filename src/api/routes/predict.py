from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from src.ml.predictor import predict
from src.api.dependencies import get_db
from src.database.models import Prediction

router = APIRouter()


class PredictRequest(BaseModel):
    # Hardware metrics — match frontend form field names exactly
    cpu_usage:   float = 50.0
    gpu_usage:   float = 70.0
    ram_usage:   float = 60.0
    vram_usage:  float = 50.0
    cpu_temp:    float = 50.0
    gpu_temp:    float = 65.0
    # Game settings — match frontend form field names exactly
    resolution:  str  = "1920x1080"
    game_genre:  str  = "fps_shooter"
    preset:      str  = "high"
    upscaling:   str  = "none"
    ray_tracing: bool = False


class PredictResponse(BaseModel):
    predicted_fps:    float
    frame_time_ms:    float
    performance_tier: str
    model_name:       str
    low_1pct_fps:     Optional[float] = None
    bottleneck_class: Optional[str]   = None
    health_score:     Optional[float] = None
    error:            Optional[str]   = None


@router.post("/predict", response_model=PredictResponse)
def predict_fps(request: PredictRequest, db: Session = Depends(get_db)):
    try:
        features = request.model_dump()

        # Add aliases so predictor._build_feature_vector() finds values
        # regardless of which naming convention the saved FeatureEngineer uses
        features["graphics_preset"]     = features["preset"]
        features["upscaling_enabled"]   = features["upscaling"] != "none"
        features["ray_tracing_enabled"] = features["ray_tracing"]

        result = predict(features)

        # ── Persist to PostgreSQL (non-fatal if it fails) ─────────────────────
        try:
            db_pred = Prediction(
                predicted_fps    = result.get("predicted_fps"),
                low_1pct_fps     = result.get("low_1pct_fps"),
                bottleneck_class = result.get("bottleneck_class"),
                health_score     = result.get("health_score"),
                game_genre       = features["game_genre"],
                resolution       = features["resolution"],
                preset           = features["preset"],
                ray_tracing      = features["ray_tracing"],
                upscaling        = features["upscaling"],
            )
            db.add(db_pred)
            db.commit()
        except Exception as db_err:
            db.rollback()
            print(f"[predict] DB save warning: {db_err}")

        return PredictResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )