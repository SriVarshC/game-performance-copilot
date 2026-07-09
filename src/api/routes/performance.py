"""
GET /api/performance/summary — aggregated request timing stats.
Any logged-in user can view (operational data, not personal).
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import RequestLog, User
from src.api.dependencies import get_current_user

router = APIRouter()


@router.get("/performance/summary", summary="Get Performance Summary")
def get_performance_summary(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(hours=hours)

    total_requests = (
        db.query(func.count(RequestLog.id))
        .filter(RequestLog.created_at >= since)
        .scalar() or 0
    )

    avg_duration = (
        db.query(func.avg(RequestLog.duration_ms))
        .filter(RequestLog.created_at >= since)
        .scalar()
    )

    error_count = (
        db.query(func.count(RequestLog.id))
        .filter(RequestLog.created_at >= since)
        .filter(RequestLog.status_code >= 400)
        .scalar() or 0
    )

    # Per-endpoint breakdown
    endpoint_rows = (
        db.query(
            RequestLog.endpoint,
            func.count(RequestLog.id).label("count"),
            func.avg(RequestLog.duration_ms).label("avg_ms"),
            func.max(RequestLog.duration_ms).label("max_ms"),
        )
        .filter(RequestLog.created_at >= since)
        .group_by(RequestLog.endpoint)
        .order_by(func.avg(RequestLog.duration_ms).desc())
        .all()
    )

    by_endpoint = [
        {
            "endpoint": row.endpoint,
            "count":    row.count,
            "avg_ms":   round(float(row.avg_ms or 0), 1),
            "max_ms":   round(float(row.max_ms or 0), 1),
        }
        for row in endpoint_rows
    ]

    return {
        "status":         "success",
        "window_hours":    hours,
        "total_requests":  total_requests,
        "avg_duration_ms": round(float(avg_duration or 0), 1),
        "error_count":     error_count,
        "error_rate_pct":  round((error_count / total_requests * 100), 1) if total_requests > 0 else 0.0,
        "by_endpoint":     by_endpoint,
    }