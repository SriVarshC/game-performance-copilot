"""
FPS Predictor — Phase 5 Upgrade
Loads all 4 trained models and returns complete performance analysis.
  Model 1 — predicted_fps        (LightGBM best)
  Model 2 — low_1pct_fps         (worst-case FPS)
  Model 3 — bottleneck_class     (GPU/CPU/THERMAL/MEMORY/BALANCED)
  Model 4 — health_score         (0-100)
"""

import joblib
import json
import os
import numpy as np


class FPSPredictor:
    MODEL_DIR = "models"

    def __init__(self):
        self.model              = None   # Model 1 — FPS
        self.low_fps_model      = None   # Model 2 — 1% low FPS
        self.bottleneck_model   = None   # Model 3 — classifier
        self.health_model       = None   # Model 4 — health score
        self.bottleneck_encoder = None   # LabelEncoder for bottleneck
        self.feature_engineer   = None
        self.model_name         = None
        self.bottleneck_classes = []
        self.is_loaded          = False
        self._load()

    def _load(self):
        try:
            meta_path = f"{self.MODEL_DIR}/model_meta.json"
            if not os.path.exists(meta_path):
                print("[WARNING] No trained model found. Run trainer.py first.")
                return

            with open(meta_path) as f:
                meta = json.load(f)

            self.model_name         = meta.get("best_model", "LightGBM")
            self.bottleneck_classes = meta.get("bottleneck_classes", [])

            # Model 1 — FPS (always required)
            self.model = joblib.load(f"{self.MODEL_DIR}/best_model.pkl")

            # Feature engineer
            from src.ml.feature_engineer import FeatureEngineer
            self.feature_engineer = FeatureEngineer.load()

            # Model 2 — 1% Low FPS (optional — only if trained)
            low_path = f"{self.MODEL_DIR}/low_fps_model.pkl"
            if os.path.exists(low_path):
                self.low_fps_model = joblib.load(low_path)

            # Model 3 — Bottleneck Classifier (optional)
            bt_path  = f"{self.MODEL_DIR}/bottleneck_model.pkl"
            enc_path = f"{self.MODEL_DIR}/bottleneck_encoder.pkl"
            if os.path.exists(bt_path) and os.path.exists(enc_path):
                self.bottleneck_model   = joblib.load(bt_path)
                self.bottleneck_encoder = joblib.load(enc_path)

            # Model 4 — Health Score (optional)
            hs_path = f"{self.MODEL_DIR}/health_model.pkl"
            if os.path.exists(hs_path):
                self.health_model = joblib.load(hs_path)

            self.is_loaded = True
            print(f"[INFO] Feature engineer loaded from: models/feature_engineer.pkl")
            print(f"[INFO] FPS Predictor loaded. Model: {self.model_name}")
            if self.low_fps_model:
                print("[INFO] 1% Low FPS model loaded.")
            if self.bottleneck_model:
                print(f"[INFO] Bottleneck classifier loaded. "
                      f"Classes: {self.bottleneck_classes}")
            if self.health_model:
                print("[INFO] Health score model loaded.")

        except Exception as e:
            print(f"[WARNING] Could not load model: {e}")

    def _build_input(self, live_metrics: dict, game_genre: str,
                     resolution: str, preset: str,
                     ray_tracing: bool, upscaling: str):
        """Build and return aligned feature array."""
        X = self.feature_engineer.build_prediction_input(
            live_metrics, game_genre, resolution,
            preset, ray_tracing, upscaling
        )
        from src.ml.feature_engineer import FeatureEngineer
        available = [c for c in FeatureEngineer.FEATURE_COLS if c in X.columns]
        return X[available].fillna(0)

    def predict(self, live_metrics: dict, game_genre: str,
                resolution: str, preset: str,
                ray_tracing: bool, upscaling: str) -> dict:
        """
        Run all 4 models and return complete performance prediction.
        """
        if not self.is_loaded:
            return {
                "predicted_fps":    None,
                "low_1pct_fps":     None,
                "bottleneck_class": None,
                "health_score":     None,
                "frame_time_ms":    None,
                "performance_tier": None,
                "model_name":       None,
                "error": "Model not loaded. Run trainer.py first."
            }

        try:
            X_input = self._build_input(
                live_metrics, game_genre, resolution,
                preset, ray_tracing, upscaling
            )

            # ── Model 1 — FPS ─────────────────────────────────────────────────
            fps_pred   = float(self.model.predict(X_input)[0])
            fps_pred   = max(1.0, round(fps_pred, 1))
            frame_time = round(1000.0 / fps_pred, 2)

            # Performance tier
            if fps_pred >= 144:
                tier = "🟢 Excellent (144+ FPS)"
            elif fps_pred >= 60:
                tier = "🟡 Playable (60+ FPS)"
            elif fps_pred >= 30:
                tier = "🟠 Acceptable (30-60 FPS)"
            else:
                tier = "🔴 Poor (<30 FPS)"

            # ── Model 2 — 1% Low FPS ──────────────────────────────────────────
            low_fps = None
            if self.low_fps_model is not None:
                low_fps = float(self.low_fps_model.predict(X_input)[0])
                low_fps = max(1.0, round(low_fps, 1))

            # ── Model 3 — Bottleneck Class ────────────────────────────────────
            bottleneck = None
            if self.bottleneck_model is not None and self.bottleneck_encoder is not None:
                bt_enc     = int(self.bottleneck_model.predict(X_input)[0])
                bottleneck = self.bottleneck_encoder.inverse_transform([bt_enc])[0]

            # ── Model 4 — Health Score ────────────────────────────────────────
            health = None
            if self.health_model is not None:
                health = float(self.health_model.predict(X_input)[0])
                health = round(min(100.0, max(0.0, health)), 1)

            return {
                "predicted_fps":    fps_pred,
                "low_1pct_fps":     low_fps,
                "bottleneck_class": bottleneck,
                "health_score":     health,
                "frame_time_ms":    frame_time,
                "performance_tier": tier,
                "model_name":       self.model_name,
                "error":            None,
            }

        except Exception as e:
            return {
                "predicted_fps":    None,
                "low_1pct_fps":     None,
                "bottleneck_class": None,
                "health_score":     None,
                "frame_time_ms":    None,
                "performance_tier": None,
                "model_name":       self.model_name,
                "error":            str(e),
            }

    def predict_settings_comparison(self, live_metrics: dict,
                                     game_genre: str,
                                     current_resolution: str,
                                     current_preset: str) -> list:
        """Predict FPS across all resolution × preset combos."""
        if not self.is_loaded:
            return []

        from src.ml.dataset_generator import PRESET_CONFIG, RESOLUTION_CONFIG
        comparisons = []

        for resolution in RESOLUTION_CONFIG.keys():
            for preset in PRESET_CONFIG.keys():
                result = self.predict(
                    live_metrics, game_genre,
                    resolution, preset,
                    ray_tracing=False, upscaling="none"
                )
                if result["predicted_fps"]:
                    comparisons.append({
                        "resolution":   resolution,
                        "preset":       preset,
                        "predicted_fps": result["predicted_fps"],
                        "is_current": (
                            resolution == current_resolution and
                            preset     == current_preset
                        ),
                    })

        comparisons.sort(key=lambda x: x["predicted_fps"], reverse=True)
        return comparisons