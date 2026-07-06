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

# ── Lazy singletons ──────────────────────────────────────────
_collector = None
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


# ── Helper — save snapshot to PostgreSQL ─────────────────────
def _save_telemetry(metrics: dict, db: Session) -> None:
    """Silently saves a telemetry snapshot to PostgreSQL."""
    try:
        gpu = metrics.get("gpu", {})
        cpu = metrics.get("cpu", {})
        memory = metrics.get("memory", {})

        row = TelemetryModel(
            gpu_usage=gpu.get("gpu_utilization"),
            vram_used_gb=(gpu.get("vram_used_mb", 0) or 0) / 1024,
            gpu_temp=gpu.get("gpu_temperature"),
            gpu_clock_mhz=gpu.get("gpu_clock_mhz"),
            gpu_power_w=gpu.get("gpu_power_watts"),
            cpu_usage=cpu.get("cpu_utilization"),
            ram_usage=memory.get("ram_utilization"),
        )

        db.add(row)
        db.commit()

    except Exception:
        db.rollback()


# ── GET /api/telemetry ───────────────────────────────────────
@router.get(
    "/telemetry",
    summary="Get Live Hardware Telemetry",
    description="Returns telemetry in frontend-compatible format.",
)
def get_telemetry(db: Session = Depends(get_db)):
    try:
        collector = get_collector()
        metrics = collector.collect_all()

        _save_telemetry(metrics, db)

        gpu = metrics.get("gpu", {})
        cpu = metrics.get("cpu", {})
        memory = metrics.get("memory", {})

        return {
            "fps": 0,
            "cpu_usage": cpu.get("cpu_utilization", 0),
            "gpu_usage": gpu.get("gpu_utilization", 0),
            "ram_usage": memory.get("ram_utilization", 0),
            "vram_usage": gpu.get("vram_utilization", 0),
            "cpu_temp": cpu.get("cpu_temperature"),
            "gpu_temp": gpu.get("gpu_temperature"),
            "timestamp": metrics.get("timestamp"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Telemetry collection failed: {str(e)}",
        )


# ── GET /api/telemetry/diagnostics ───────────────────────────
@router.get(
    "/telemetry/diagnostics",
    summary="Get Telemetry + AI Diagnostics",
)
def get_telemetry_with_diagnostics(db: Session = Depends(get_db)):
    try:
        collector = get_collector()
        engine = get_diagnostics_engine()

        metrics = collector.collect_all()
        _save_telemetry(metrics, db)

        issues = engine.analyze(metrics)

        return {
            "status": "success",
            "metrics": metrics,
            "issues_count": len(issues),
            "issues": issues,
        }

    except AttributeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"DiagnosticsEngine method not found: {e}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Diagnostics failed: {str(e)}",
        )


# ── GET /api/telemetry/history ───────────────────────────────
@router.get(
    "/telemetry/history",
    summary="Get Telemetry History",
)
def get_telemetry_history(
    hours: int = Query(1, ge=1, le=24),
    limit: int = Query(500, ge=1, le=1000),
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
                "fps": 0,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "cpu_usage": r.cpu_usage or 0,
                "gpu_usage": r.gpu_usage or 0,
                "ram_usage": r.ram_usage or 0,
                "vram_usage": 0,
                "cpu_temp": None,
                "gpu_temp": r.gpu_temp,
            }
            for r in records
        ]

        return {
            "history": history,
            "count": len(history),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Telemetry history failed: {str(e)}",
        )