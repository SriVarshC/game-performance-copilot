"""
GET /api/telemetry              — live hardware snapshot (saves to PostgreSQL)
GET /api/telemetry/diagnostics  — snapshot + AI bottleneck detection
GET /api/telemetry/history      — historical readings from PostgreSQL
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import Telemetry as TelemetryModel

router = APIRouter()

# ── Lazy singletons ──────────────────────────────────────────────────────────
_collector          = None
_diagnostics_engine = None


def get_collector():
    global _collector
    if _collector is None:
        from src.telemetry.collector import TelemetryCollector
        _collector = TelemetryCollector()
    return _collector


def get_diagnostics_engine():
    global _diagnostics_engine
    if _diagnostics_engine is None:
        from src.diagnostics.engine import DiagnosticsEngine
        _diagnostics_engine = DiagnosticsEngine()
    return _diagnostics_engine


# ── Helper — save snapshot to PostgreSQL ─────────────────────────────────────
def _save_telemetry(metrics: dict, db: Session) -> None:
    """Silently saves a telemetry snapshot to PostgreSQL."""
    try:
        row = TelemetryModel(
            gpu_usage     = metrics.get("gpu_utilization"),
            vram_used_gb  = (metrics.get("vram_used_mb") or 0) / 1024,
            gpu_temp      = metrics.get("gpu_temperature"),
            gpu_clock_mhz = metrics.get("gpu_clock_mhz"),
            gpu_power_w   = metrics.get("gpu_power_watts"),
            cpu_usage     = metrics.get("cpu_utilization"),
            ram_usage     = metrics.get("ram_utilization"),
        )
        db.add(row)
        db.commit()
    except Exception:
        db.rollback()


# ── GET /api/telemetry ────────────────────────────────────────────────────────
@router.get(
    "/telemetry",
    summary="Get Live Hardware Telemetry",
    description=(
        "Returns a real-time hardware snapshot and saves it to PostgreSQL.\n\n"
        "Includes: GPU utilization, VRAM used/total/%, GPU temp, clock, power — "
        "CPU utilization (overall + per-core), frequency — "
        "RAM used/total/%, top background processes."
    ),
)
def get_telemetry(db: Session = Depends(get_db)):
    try:
        collector = get_collector()
        metrics   = collector.collect_all()
        _save_telemetry(metrics, db)
        return {"status": "success", "data": metrics}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Telemetry collection failed: {str(e)}"
        )


# ── GET /api/telemetry/diagnostics ────────────────────────────────────────────
@router.get(
    "/telemetry/diagnostics",
    summary="Get Telemetry + AI Diagnostics",
    description=(
        "Returns live hardware snapshot plus AI bottleneck detection.\n\n"
        "Detects: CPU_BOTTLENECK, GPU_BOTTLENECK, VRAM_PRESSURE, "
        "GPU_THERMAL_THROTTLING, RAM_PRESSURE.\n\n"
        "Each issue includes: issue_type, severity, confidence, description."
    ),
)
def get_telemetry_with_diagnostics(db: Session = Depends(get_db)):
    try:
        collector = get_collector()
        engine    = get_diagnostics_engine()
        metrics   = collector.collect_all()
        _save_telemetry(metrics, db)
        issues = engine.analyze(metrics)
        return {
            "status":       "success",
            "metrics":      metrics,
            "issues_count": len(issues),
            "issues":       issues,
        }
    except AttributeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"DiagnosticsEngine method not found: {e}.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Diagnostics failed: {str(e)}"
        )


# ── GET /api/telemetry/history ────────────────────────────────────────────────
@router.get(
    "/telemetry/history",
    summary="Get Telemetry History",
    description=(
        "Returns historical telemetry readings from PostgreSQL.\n\n"
        "Use 'hours' to control the time window (1-24).\n"
        "Use 'limit' to control max records returned (1-1000)."
    ),
)
def get_telemetry_history(
    hours: int = Query(1,   ge=1,  le=24,   description="Hours of history"),
    limit: int = Query(500, ge=1,  le=1000, description="Max records"),
    db: Session = Depends(get_db),
):
    try:
        since = datetime.utcnow() - timedelta(hours=hours)

        records = (
            db.query(TelemetryModel)
            .filter(TelemetryModel.timestamp >= since)
            .order_by(TelemetryModel.timestamp.asc())
            .limit(limit)
            .all()
        )

        history = [
            {
                "id":            r.id,
                "timestamp":     r.timestamp.isoformat() if r.timestamp else None,
                "gpu_usage":     r.gpu_usage,
                "cpu_usage":     r.cpu_usage,
                "ram_usage":     r.ram_usage,
                "vram_used_gb":  r.vram_used_gb,
                "gpu_temp":      r.gpu_temp,
                "gpu_clock_mhz": r.gpu_clock_mhz,
                "gpu_power_w":   r.gpu_power_w,
            }
            for r in records
        ]

        return {
            "status":  "success",
            "hours":   hours,
            "count":   len(history),
            "history": history,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Telemetry history failed: {str(e)}"
        )