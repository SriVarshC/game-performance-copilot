"""
Feedback routes — POST /api/feedback/{id}  and  GET /api/feedback/summary
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.database.db_manager import DatabaseManager

router = APIRouter()

# ── Lazy singleton ────────────────────────────────────────────────────────────
_db: DatabaseManager | None = None

def get_db() -> DatabaseManager:
    global _db
    if _db is None:
        _db = DatabaseManager()
    return _db


# ── Request model ─────────────────────────────────────────────────────────────
class FeedbackRequest(BaseModel):
    was_helpful: bool


# ── POST /api/feedback/{recommendation_id} ────────────────────────────────────
@router.post("/api/feedback/{recommendation_id}")
def submit_feedback(recommendation_id: int, body: FeedbackRequest):
    """
    Record whether a recommendation was helpful.
    was_helpful: true = 👍  |  false = 👎
    """
    try:
        db = get_db()
        db.update_recommendation_feedback(recommendation_id, body.was_helpful)
        return {
            "status":      "success",
            "message":     "Feedback recorded — thank you!",
            "id":          recommendation_id,
            "was_helpful": body.was_helpful
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/feedback/summary ─────────────────────────────────────────────────
@router.get("/api/feedback/summary")
def get_feedback_summary():
    """
    Return aggregated feedback statistics.
    Includes overall counts, helpful %, and per-category breakdown.
    """
    try:
        db = get_db()
        summary = db.get_feedback_summary()
        return {"status": "success", **summary}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))