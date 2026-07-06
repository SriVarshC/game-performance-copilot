import pickle
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional

from src.ml.feature_engineer import FeatureEngineer

# ─── Model paths ─────────────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
META_PATH   = MODEL_DIR / "model_meta.json"

# ─── Lazy-loaded singletons (loaded once, reused forever) ────────────────────
_best_model         = None
_low_fps_model      = None
_bottleneck_model   = None
_health_model       = None
_feature_engineer   = None
_bottleneck_encoder = None
_model_name         = "LightGBM"



def _load_pkl(path: Path):
    """Load a pickle file; return None if missing or corrupted.

    Uses joblib.load() instead of plain pickle.load() because trainer.py
    saves everything with joblib.dump(), which uses its own internal
    serialization format for numpy-array-bearing objects (LabelEncoder,
    FeatureEngineer, etc). Plain pickle.load() can't parse that framing
    correctly, which was producing false "corrupted" errors.
    """
    if not path.exists():
        print(f"[predictor] WARNING: {path} not found — skipping")
        return None
    try:
        return joblib.load(path)
    except Exception as e:
        print(f"[predictor] WARNING: {path} corrupted ({e}) — skipping, using fallback")
        return None


def _ensure_models_loaded():
    """Load all models on first call."""
    global _best_model, _low_fps_model, _bottleneck_model
    global _health_model, _feature_engineer, _bottleneck_encoder, _model_name

    if _best_model is not None:
        return  # already loaded

    # Read meta for best-model path
    # NOTE: "best_model" in model_meta.json is a LABEL (e.g. "LightGBM"),
    # not a filename. The actual filename is under "model_file".
    if META_PATH.exists():
        with open(META_PATH) as f:
            meta = json.load(f)
        best_path = MODEL_DIR / Path(meta.get("model_file", "best_model.pkl")).name
    else:
        best_path = MODEL_DIR / "best_model.pkl"

    _best_model         = _load_pkl(best_path)
    _low_fps_model      = _load_pkl(MODEL_DIR / "low_fps_model.pkl")
    _bottleneck_model   = _load_pkl(MODEL_DIR / "bottleneck_model.pkl")
    _health_model       = _load_pkl(MODEL_DIR / "health_model.pkl")
    _feature_engineer   = _load_pkl(MODEL_DIR / "feature_engineer.pkl")
    _bottleneck_encoder = _load_pkl(MODEL_DIR / "bottleneck_encoder.pkl")

    if _best_model is not None:
        cls = type(_best_model).__name__
        if "LightGBM" in cls or "lgb" in cls.lower():
            _model_name = "LightGBM"
        elif "XGB" in cls:
            _model_name = "XGBoost"
        elif "RandomForest" in cls:
            _model_name = "RandomForest"
        else:
            _model_name = cls


# ─── Reference tables (mirrors dataset_generator.py) ────────────────────────
# These MUST match the keys used in src/ml/dataset_generator.py exactly,
# since the LabelEncoders inside feature_engineer.pkl were fit on these
# exact string values. If the API sends a value not in these tables,
# it is treated as an "unseen" category (encoded as -1) rather than crashing.

_VRAM_TOTAL_MB = 4096  # RTX 3050 Ti Laptop VRAM

# genre -> vram_threshold_mb, used only to compute the vram_pressure flag.
# Falls back to a generic 3000 MB threshold for any genre string the
# frontend sends that doesn't match one of the training profiles below.
_GENRE_VRAM_THRESHOLD = {
    "fps_competitive": 2048,
    "fps_aaa":         3500,
    "rpg_open_world":  3200,
    "moba":            2048,
    "battle_royale":   3000,
    "racing":          3000,
    "strategy":        2500,
}
_DEFAULT_VRAM_THRESHOLD = 3000

_PRESET_ORDER = ["low", "medium", "high", "ultra", "epic"]


def _estimate_gpu_clock(gpu_temp: float) -> float:
    """Mirrors the deterministic part of dataset_generator's clock formula
    (drops the random noise term since this is inference, not simulation)."""
    base_clock = 1695.0
    if gpu_temp > 85:
        base_clock -= (gpu_temp - 85) * 15
    return float(np.clip(base_clock, 400, 1695))


def _estimate_gpu_power(gpu_util: float) -> float:
    """Mirrors dataset_generator's power formula (noise term dropped)."""
    return float(np.clip(45 + gpu_util * 0.35, 12, 80))


def _build_feature_vector(raw: dict) -> pd.DataFrame:
    """
    Build a one-row DataFrame with the exact raw columns FeatureEngineer
    expects, deriving anything the simple API payload doesn't provide
    directly (gpu_clock_mhz, gpu_power_watts, vram_used_mb, cpu_gpu_ratio,
    vram_pressure, thermal_throttle, resolution_width/height, total_pixels,
    preset_ordinal) using the same formulas dataset_generator.py used when
    training data was created.
    """
    _ensure_models_loaded()

    # ── Pull raw API fields (with safe defaults) ─────────────────────────
    cpu_util   = float(raw.get("cpu_usage",  50.0))
    gpu_util   = float(raw.get("gpu_usage",  70.0))
    ram_util   = float(raw.get("ram_usage",  60.0))
    vram_util  = float(raw.get("vram_usage", 50.0))   # percent, 0-100
    gpu_temp   = float(raw.get("gpu_temp",   75.0))
    resolution = str(raw.get("resolution",   "1920x1080"))
    genre      = str(raw.get("game_genre",   "fps_aaa"))
    preset     = str(raw.get("preset",       "high")).lower()
    upscaling  = str(raw.get("upscaling",    "none"))
    ray_tracing = bool(raw.get("ray_tracing", False))

    # ── Derived numeric features (mirror dataset_generator.py) ───────────
    vram_used_mb = (vram_util / 100.0) * _VRAM_TOTAL_MB
    gpu_clock_mhz = _estimate_gpu_clock(gpu_temp)
    gpu_power_watts = _estimate_gpu_power(gpu_util)
    cpu_gpu_ratio = round(cpu_util / max(gpu_util, 1), 4)
    thermal_throttle = int(gpu_temp > 85)

    vram_threshold = _GENRE_VRAM_THRESHOLD.get(genre, _DEFAULT_VRAM_THRESHOLD)
    vram_pressure = int(vram_used_mb > vram_threshold)

    try:
        res_w, res_h = resolution.split("x")
        res_w, res_h = int(res_w), int(res_h)
    except Exception:
        res_w, res_h = 1920, 1080
    total_pixels = res_w * res_h

    preset_ordinal = _PRESET_ORDER.index(preset) if preset in _PRESET_ORDER else 2

    row = {
        # raw categoricals — encoded inside FeatureEngineer.transform()
        "game_genre":  genre,
        "resolution":  resolution,
        "preset":      preset,
        "upscaling":   upscaling,

        # numeric features expected by FeatureEngineer.FEATURE_COLS
        "gpu_utilization":   gpu_util,
        "vram_used_mb":      vram_used_mb,
        "vram_utilization":  vram_util,
        "cpu_utilization":   cpu_util,
        "ram_utilization":   ram_util,
        "gpu_temperature":   gpu_temp,
        "gpu_clock_mhz":     gpu_clock_mhz,
        "gpu_power_watts":   gpu_power_watts,
        "cpu_gpu_ratio":     cpu_gpu_ratio,
        "vram_pressure":     vram_pressure,
        "thermal_throttle":  thermal_throttle,
        "resolution_width":  res_w,
        "resolution_height": res_h,
        "total_pixels":      total_pixels,
        "preset_ordinal":    preset_ordinal,
        "ray_tracing":       int(ray_tracing),
    }

    df = pd.DataFrame([row])

    if _feature_engineer is not None:
        try:
            engineered = _feature_engineer.transform(df)
            X = engineered[FeatureEngineer.FEATURE_COLS].fillna(0)
            return X
        except Exception as e:
            print(f"[predictor] FeatureEngineer.transform failed ({e}), using raw numeric fallback")

    # ── Fallback: if feature_engineer failed to load/transform, build the
    # 20-column vector manually with naive integer-encoded categoricals.
    # This will NOT match training encodings exactly, so predictions in
    # this path are a rough estimate only.
    fallback_cols = FeatureEngineer.NUMERIC_FEATURES + [
        "game_genre_enc", "resolution_enc", "preset_enc", "upscaling_enc"
    ]
    row["game_genre_enc"] = 0
    row["resolution_enc"] = 0
    row["preset_enc"]     = preset_ordinal
    row["upscaling_enc"]  = 0
    return pd.DataFrame([row])[fallback_cols].fillna(0)


# ─── Performance tier helper ─────────────────────────────────────────────────
def _get_tier(fps: float) -> str:
    if fps >= 144: return "🟢 Excellent (144+ FPS)"
    if fps >= 60:  return "🟡 Good (60–144 FPS)"
    if fps >= 30:  return "🟠 Playable (30–60 FPS)"
    if fps >= 15:  return "🔴 Poor (15–30 FPS)"
    return "💀 Unplayable (<15 FPS)"


# ─── PUBLIC API ──────────────────────────────────────────────────────────────
def predict(features: dict) -> dict:
    """
    Run all 4 models and return a unified result dict.

    Returns:
        predicted_fps     float
        low_1pct_fps      float | None
        bottleneck_class  str   | None
        health_score      float | None
        frame_time_ms     float
        performance_tier  str
        model_name        str
        error             str | None
    """
    _ensure_models_loaded()

    if _best_model is None:
        return {
            "predicted_fps":    0.0,
            "low_1pct_fps":     None,
            "bottleneck_class": None,
            "health_score":     None,
            "frame_time_ms":    0.0,
            "performance_tier": "❓ No model loaded",
            "model_name":       "none",
            "error":            "best_model.pkl not found in models/",
        }

    try:
        X = _build_feature_vector(features)

        # ── FPS (primary) ────────────────────────────────────────────────────
        predicted_fps   = float(_best_model.predict(X)[0])
        predicted_fps   = max(0.0, round(predicted_fps, 1))
        frame_time_ms   = round(1000.0 / predicted_fps, 2) if predicted_fps > 0 else 0.0

        # ── 1% Low FPS ───────────────────────────────────────────────────────
        low_1pct_fps: Optional[float] = None
        if _low_fps_model is not None:
            try:
                low_1pct_fps = float(_low_fps_model.predict(X)[0])
                low_1pct_fps = max(0.0, round(low_1pct_fps, 1))
            except Exception as e:
                print(f"[predictor] low_fps_model warning: {e}")

        # ── Bottleneck classifier ────────────────────────────────────────────
        bottleneck_class: Optional[str] = None
        if _bottleneck_model is not None:
            try:
                pred_enc = _bottleneck_model.predict(X)[0]
                if _bottleneck_encoder is not None:
                    bottleneck_class = str(_bottleneck_encoder.inverse_transform([pred_enc])[0])
                else:
                    bottleneck_class = str(pred_enc)
            except Exception as e:
                print(f"[predictor] bottleneck_model warning: {e}")

        # ── Health score ─────────────────────────────────────────────────────
        health_score: Optional[float] = None
        if _health_model is not None:
            try:
                health_score = float(_health_model.predict(X)[0])
                health_score = round(min(100.0, max(0.0, health_score)), 1)
            except Exception as e:
                print(f"[predictor] health_model warning: {e}")

        return {
            "predicted_fps":    predicted_fps,
            "low_1pct_fps":     low_1pct_fps,
            "bottleneck_class": bottleneck_class,
            "health_score":     health_score,
            "frame_time_ms":    frame_time_ms,
            "performance_tier": _get_tier(predicted_fps),
            "model_name":       _model_name,
            "error":            None,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "predicted_fps":    0.0,
            "low_1pct_fps":     None,
            "bottleneck_class": None,
            "health_score":     None,
            "frame_time_ms":    0.0,
            "performance_tier": "❓ Prediction error",
            "model_name":       _model_name,
            "error":            str(e),
        }