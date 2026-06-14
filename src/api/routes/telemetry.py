"""
GET /api/telemetry              — live hardware snapshot
GET /api/telemetry/diagnostics  — snapshot + AI bottleneck detection
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()

# ── Lazy singletons ──────────────────────────────────────────────────────────
_collector        = None
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


# ── Endpoints ────────────────────────────────────────────────────────────────
@router.get(
    "/telemetry",
    summary="Get Live Hardware Telemetry",
    description=(
        "Returns a real-time hardware snapshot.\n\n"
        "Includes: GPU utilization, VRAM used/total/%, GPU temp, clock, power — "
        "CPU utilization (overall + per-core), frequency, temp — "
        "RAM used/total/%, page file — top background processes, disk usage."
    ),
)
def get_telemetry():
    try:
        collector = get_collector()
        metrics   = collector.collect_all()
        return {"status": "success", "data": metrics}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Telemetry collection failed: {str(e)}"
        )


@router.get(
    "/telemetry/diagnostics",
    summary="Get Telemetry + AI Diagnostics",
    description=(
        "Returns live hardware snapshot **plus** AI bottleneck detection.\n\n"
        "Detects: CPU_BOTTLENECK, GPU_BOTTLENECK, VRAM_PRESSURE, "
        "GPU_THERMAL_THROTTLING, CPU_THERMAL_THROTTLING, RAM_PRESSURE, PAGE_FILE_OVERUSE.\n\n"
        "Each issue includes: issue_type, severity (CRITICAL/HIGH/MEDIUM/NONE), "
        "confidence (0–1), description.\n\n"
        "Thresholds tuned for RTX 3050 Ti + i7-12650H + 16 GB RAM."
    ),
)
def get_telemetry_with_diagnostics():
    try:
        collector = get_collector()
        engine    = get_diagnostics_engine()
        metrics   = collector.collect_all()

        # Call DiagnosticsEngine — check src/diagnostics/engine.py for
        # exact method name (likely: analyze, diagnose, or run_diagnostics)
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
            detail=(
                f"DiagnosticsEngine method not found: {e}. "
                "Open src/diagnostics/engine.py and find the public method "
                "that takes metrics and returns a list of issues. "
                "Update engine.analyze(metrics) in this file."
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostics failed: {str(e)}")