"""
Feedback routes — PostgreSQL backed.
POST /api/feedback/{id}      — submit thumbs up/down
GET  /api/feedback/summary   — aggregated feedback stats
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from src.database.connection import get_db
from src.database.models import Recommendation as RecommendationModel, User
from src.api.dependencies import get_current_user

router = APIRouter()


# ── Request model ─────────────────────────────────────────────────────────────
class FeedbackRequest(BaseModel):
    was_helpful: bool


# ── POST /feedback/{recommendation_id} ───────────────────────────────────────
@router.post(
    "/feedback/{recommendation_id}",
    summary="Submit Recommendation Feedback",
)
def submit_feedback(
    recommendation_id: int,
    body: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        rec = (
            db.query(RecommendationModel)
            .filter(RecommendationModel.recommendation_id == recommendation_id)
            .first()
        )

        if not rec:
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation {recommendation_id} not found"
            )

        rec.was_helpful = body.was_helpful
        db.commit()

        return {
            "status":      "success",
            "message":     "Feedback recorded — thank you!",
            "id":          recommendation_id,
            "was_helpful": body.was_helpful,
        }
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /feedback/summary ─────────────────────────────────────────────────────
@router.get(
    "/feedback/summary",
    summary="Get Feedback Analytics Summary",
)
def get_feedback_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        total = db.query(
            func.count(RecommendationModel.recommendation_id)
        ).scalar() or 0

        feedback_given = db.query(
            func.count(RecommendationModel.recommendation_id)
        ).filter(
            RecommendationModel.was_helpful.isnot(None)
        ).scalar() or 0

        helpful = db.query(
            func.count(RecommendationModel.recommendation_id)
        ).filter(
            RecommendationModel.was_helpful == True
        ).scalar() or 0

        not_helpful = db.query(
            func.count(RecommendationModel.recommendation_id)
        ).filter(
            RecommendationModel.was_helpful == False
        ).scalar() or 0

        helpful_pct = round(
            (helpful / feedback_given * 100) if feedback_given > 0 else 0, 1
        )

        # Per-category breakdown — SQLAlchemy 2.0 case() syntax
        category_rows = db.query(
            RecommendationModel.category,
            func.count(RecommendationModel.recommendation_id).label("total"),
            func.sum(
                case(
                    (RecommendationModel.was_helpful == True, 1),
                    else_=0
                )
            ).label("helpful_count"),
        ).group_by(RecommendationModel.category).all()

        by_category = [
            {
                "category": row.category or "general",
                "total":    row.total,
                "helpful":  int(row.helpful_count or 0),
            }
            for row in category_rows
        ]

        return {
            "status":                "success",
            "total_recommendations": total,
            "feedback_given":        feedback_given,
            "helpful":               helpful,
            "not_helpful":           not_helpful,
            "helpful_percentage":    helpful_pct,
            "by_category":           by_category,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))