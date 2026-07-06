from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from src.api.dependencies import get_db
from src.database.models import Telemetry, Prediction, Recommendation

router = APIRouter()


@router.get("/analytics", tags=["Analytics"])
def get_analytics(db: Session = Depends(get_db)):

    # ── Telemetry stats ───────────────────────────────────────────────────────
    tel_count    = 0
    avg_fps      = 0.0
    avg_cpu      = 0.0
    avg_gpu      = 0.0
    avg_ram      = 0.0
    try:
        tel_count = db.query(func.count(text("*"))).select_from(Telemetry).scalar() or 0
        avg_fps   = float(db.query(func.avg(Telemetry.fps)).scalar()       or 0)
        avg_cpu   = float(db.query(func.avg(Telemetry.cpu_usage)).scalar() or 0)
        avg_gpu   = float(db.query(func.avg(Telemetry.gpu_usage)).scalar() or 0)
        avg_ram   = float(db.query(func.avg(Telemetry.ram_usage)).scalar() or 0)
    except Exception as e:
        print(f"[analytics] telemetry query error: {e}")

    # ── Prediction stats ──────────────────────────────────────────────────────
    pred_count      = 0
    avg_pred_fps    = 0.0
    bottleneck_dist = {}
    try:
        pred_count   = db.query(func.count(text("*"))).select_from(Prediction).scalar() or 0
        avg_pred_fps = float(db.query(func.avg(Prediction.predicted_fps)).scalar() or 0)
        rows = (
            db.query(Prediction.bottleneck_class,
                     func.count(text("*")).label("cnt"))
            .filter(Prediction.bottleneck_class.isnot(None))
            .group_by(Prediction.bottleneck_class)
            .all()
        )
        bottleneck_dist = {str(r[0]): int(r[1]) for r in rows}
    except Exception as e:
        print(f"[analytics] prediction query error: {e}")

    # ── Feedback stats ────────────────────────────────────────────────────────
    total_fb    = 0
    helpful     = 0
    not_helpful = 0
    helpful_pct = 0.0
    try:
        total_fb = (
            db.query(func.count(text("*")))
            .select_from(Recommendation)
            .filter(Recommendation.was_helpful.isnot(None))
            .scalar() or 0
        )
        helpful = (
            db.query(func.count(text("*")))
            .select_from(Recommendation)
            .filter(Recommendation.was_helpful == True)
            .scalar() or 0
        )
        not_helpful = (
            db.query(func.count(text("*")))
            .select_from(Recommendation)
            .filter(Recommendation.was_helpful == False)
            .scalar() or 0
        )
        helpful_pct = round((helpful / total_fb * 100), 1) if total_fb > 0 else 0.0
    except Exception as e:
        print(f"[analytics] feedback query error: {e}")

    return {
        "status": "success",
        "telemetry": {
            "total_readings": tel_count,
            "avg_fps":        round(avg_fps, 1),
            "avg_cpu_usage":  round(avg_cpu, 1),
            "avg_gpu_usage":  round(avg_gpu, 1),
            "avg_ram_usage":  round(avg_ram, 1),
        },
        "predictions": {
            "total_predictions":       pred_count,
            "avg_predicted_fps":       round(avg_pred_fps, 1),
            "bottleneck_distribution": bottleneck_dist,
        },
        "feedback": {
            "total_feedback":     total_fb,
            "helpful_count":      helpful,
            "not_helpful_count":  not_helpful,
            "helpful_percentage": helpful_pct,
        },
    }