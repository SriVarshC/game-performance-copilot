"""
Analytics endpoint — aggregated performance stats from PostgreSQL.
GET /api/analytics
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.connection import get_db
from src.database.models import Telemetry, Prediction, Recommendation

router = APIRouter()


@router.get("/analytics", summary="Aggregated Performance Analytics")
def get_analytics(db: Session = Depends(get_db)):
    """
    Returns aggregated stats across all stored telemetry and predictions.
    Used by the React Analytics page.
    """
    try:
        # ── Telemetry Averages ────────────────────────────────────────────────
        tel = db.query(
            func.avg(Telemetry.gpu_usage).label("avg_gpu"),
            func.avg(Telemetry.cpu_usage).label("avg_cpu"),
            func.avg(Telemetry.ram_usage).label("avg_ram"),
            func.avg(Telemetry.gpu_temp).label("avg_gpu_temp"),
            func.count(Telemetry.id).label("total_readings"),
        ).first()

        # ── Prediction Averages ───────────────────────────────────────────────
        pred = db.query(
            func.avg(Prediction.predicted_fps).label("avg_predicted_fps"),
            func.avg(Prediction.health_score).label("avg_health_score"),
            func.count(Prediction.prediction_id).label("total_predictions"),
        ).first()

        # ── Bottleneck Distribution ───────────────────────────────────────────
        bottleneck_rows = db.query(
            Prediction.bottleneck_class,
            func.count(Prediction.prediction_id).label("count"),
        ).group_by(Prediction.bottleneck_class).all()

        bottleneck_distribution = {
            row.bottleneck_class: row.count
            for row in bottleneck_rows
            if row.bottleneck_class is not None
        }

        # ── Feedback Stats ────────────────────────────────────────────────────
        total_recs = db.query(
            func.count(Recommendation.recommendation_id)
        ).scalar() or 0

        helpful_recs = db.query(
            func.count(Recommendation.recommendation_id)
        ).filter(Recommendation.was_helpful == True).scalar() or 0

        return {
            "status": "success",
            "telemetry": {
                "total_readings": tel.total_readings or 0,
                "avg_gpu_usage":  round(tel.avg_gpu      or 0, 2),
                "avg_cpu_usage":  round(tel.avg_cpu      or 0, 2),
                "avg_ram_usage":  round(tel.avg_ram      or 0, 2),
                "avg_gpu_temp":   round(tel.avg_gpu_temp or 0, 2),
            },
            "predictions": {
                "total_predictions": pred.total_predictions or 0,
                "avg_predicted_fps": round(pred.avg_predicted_fps or 0, 2),
                "avg_health_score":  round(pred.avg_health_score  or 0, 2),
            },
            "bottleneck_distribution": bottleneck_distribution,
            "feedback": {
                "total_recommendations": total_recs,
                "helpful_recommendations": helpful_recs,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics failed: {str(e)}"
        )