"""
GET /api/errors — paginated list of logged application errors.
Any logged-in user can view (no per-user filtering — this is an
operational/debugging view, not personal data).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import ErrorLog, User
from src.api.dependencies import get_current_user

router = APIRouter()


@router.get("/errors", summary="Get Recent Application Errors")
def get_errors(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(ErrorLog).count()

    rows = (
        db.query(ErrorLog)
        .order_by(ErrorLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    errors = [
        {
            "id":            r.id,
            "user_id":       r.user_id,
            "endpoint":      r.endpoint,
            "method":        r.method,
            "status_code":   r.status_code,
            "error_type":    r.error_type,
            "error_message": r.error_message,
            "created_at":    r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

    return {
        "status": "success",
        "total":  total,
        "count":  len(errors),
        "errors": errors,
    }