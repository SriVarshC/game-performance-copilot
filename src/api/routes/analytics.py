from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from src.api.dependencies import get_db, get_current_user
from src.database.models import Telemetry, Prediction, Recommendation, User

router = APIRouter()


@router.get("/analytics", tags=["Analytics"])
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # ── Telemetry stats ───────────────────────────────────────────────────────
    tel_count    = 0
    avg_fps      = 0.0
    avg_cpu      = 0.0
    avg_gpu      = 0.0
    avg_ram      = 0.0
    try:
        tel_filter = Telemetry.user_id == current_user.user_id
        tel_count = db.query(func.count(text("*"))).select_from(Telemetry).filter(tel_filter).scalar() or 0
        avg_fps   = float(db.query(func.avg(Telemetry.fps)).filter(tel_filter).scalar()       or 0)
        avg_cpu   = float(db.query(func.avg(Telemetry.cpu_usage)).filter(tel_filter).scalar() or 0)
        avg_gpu   = float(db.query(func.avg(Telemetry.gpu_usage)).filter(tel_filter).scalar() or 0)
        avg_ram   = float(db.query(func.avg(Telemetry.ram_usage)).filter(tel_filter).scalar() or 0)
    except Exception as e:
        print(f"[analytics] telemetry query error: {e}")

    # ── Prediction stats ──────────────────────────────────────────────────────
    pred_count      = 0
    avg_pred_fps    = 0.0
    bottleneck_dist = {}
    try:
        pred_filter  = Prediction.user_id == current_user.user_id
        pred_count   = db.query(func.count(text("*"))).select_from(Prediction).filter(pred_filter).scalar() or 0
        avg_pred_fps = float(db.query(func.avg(Prediction.predicted_fps)).filter(pred_filter).scalar() or 0)
        rows = (
            db.query(Prediction.bottleneck_class,
                     func.count(text("*")).label("cnt"))
            .filter(pred_filter, Prediction.bottleneck_class.isnot(None))
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
        rec_filter = Recommendation.user_id == current_user.user_id
        total_fb = (
            db.query(func.count(text("*")))
            .select_from(Recommendation)
            .filter(rec_filter, Recommendation.was_helpful.isnot(None))
            .scalar() or 0
        )
        helpful = (
            db.query(func.count(text("*")))
            .select_from(Recommendation)
            .filter(rec_filter, Recommendation.was_helpful == True)
            .scalar() or 0
        )
        not_helpful = (
            db.query(func.count(text("*")))
            .select_from(Recommendation)
            .filter(rec_filter, Recommendation.was_helpful == False)
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


@router.get("/predictions/history", tags=["Analytics"])
def get_predictions_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the most recent N predictions in chronological order, with
    health_score, predicted_fps, and bottleneck_class — used to chart
    system health trends over time on the Analytics page.
    """
    try:
        rows = (
            db.query(Prediction)
            .filter(Prediction.user_id == current_user.user_id)
            .order_by(Prediction.created_at.desc())
            .limit(limit)
            .all()
        )
        predictions = [
            {
                "created_at":       r.created_at.isoformat() if r.created_at else None,
                "health_score":     r.health_score,
                "predicted_fps":    r.predicted_fps,
                "bottleneck_class": r.bottleneck_class,
            }
            for r in reversed(rows)
        ]
        return {"status": "success", "predictions": predictions}
    except Exception as e:
        print(f"[analytics] predictions history query error: {e}")
        return {"status": "error", "predictions": []}