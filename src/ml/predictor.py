"""
FPS Predictor — loads trained model and makes predictions.
Used by the dashboard to show predicted FPS in real time.
"""

import joblib
import json
import os
import pandas as pd
import numpy as np


class FPSPredictor:
    """
    Loads the best trained FPS prediction model
    and provides prediction interface for the dashboard.
    """

    MODEL_DIR = "models"

    def __init__(self):
        self.model = None
        self.feature_engineer = None
        self.model_name = None
        self.is_loaded = False
        self._load()

    def _load(self):
        """Load best model and feature engineer from disk."""
        try:
            # Load model metadata
            meta_path = f"{self.MODEL_DIR}/model_meta.json"
            if not os.path.exists(meta_path):
                print("[WARNING] No trained model found. Run trainer.py first.")
                return

            with open(meta_path) as f:
                meta = json.load(f)

            self.model_name = meta["best_model"]

            # Load model
            model_path = f"{self.MODEL_DIR}/best_model.pkl"
            self.model = joblib.load(model_path)

            # Load feature engineer
            from src.ml.feature_engineer import FeatureEngineer
            self.feature_engineer = FeatureEngineer.load()

            self.is_loaded = True
            print(f"[INFO] FPS Predictor loaded. Model: {self.model_name}")

        except Exception as e:
            print(f"[WARNING] Could not load model: {e}")

    def predict(self, live_metrics: dict, game_genre: str,
                resolution: str, preset: str,
                ray_tracing: bool, upscaling: str) -> dict:
        """
        Predict FPS for given metrics and settings.
        Returns predicted FPS and confidence interval.
        """
        if not self.is_loaded:
            return {
                "predicted_fps": None,
                "frame_time_ms": None,
                "model_name": None,
                "error": "Model not loaded. Run trainer.py first."
            }

        try:
            # Build input features
            X = self.feature_engineer.build_prediction_input(
                live_metrics, game_genre, resolution,
                preset, ray_tracing, upscaling
            )

            # Get feature columns used during training
            from src.ml.feature_engineer import FeatureEngineer
            available = [c for c in FeatureEngineer.FEATURE_COLS if c in X.columns]
            X_input = X[available].fillna(0)

            # Predict
            fps_pred = float(self.model.predict(X_input)[0])
            fps_pred = max(1.0, round(fps_pred, 1))
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

            return {
                "predicted_fps":  fps_pred,
                "frame_time_ms":  frame_time,
                "performance_tier": tier,
                "model_name":     self.model_name,
                "error":          None
            }

        except Exception as e:
            return {
                "predicted_fps": None,
                "frame_time_ms": None,
                "model_name": self.model_name,
                "error": str(e)
            }

    def predict_settings_comparison(self, live_metrics: dict,
                                     game_genre: str,
                                     current_resolution: str,
                                     current_preset: str) -> list:
        """
        Predict FPS across different settings combinations.
        Used by recommendation engine to show potential gains.
        """
        if not self.is_loaded:
            return []

        from src.ml.dataset_generator import PRESET_CONFIG, RESOLUTION_CONFIG

        comparisons = []

        for resolution in RESOLUTION_CONFIG.keys():
            for preset in PRESET_CONFIG.keys():
                result = self.predict(
                    live_metrics, game_genre,
                    resolution, preset,
                    ray_tracing=False,
                    upscaling="none"
                )
                if result["predicted_fps"]:
                    comparisons.append({
                        "resolution": resolution,
                        "preset": preset,
                        "predicted_fps": result["predicted_fps"],
                        "is_current": (
                            resolution == current_resolution and
                            preset == current_preset
                        )
                    })

        # Sort by FPS descending
        comparisons.sort(key=lambda x: x["predicted_fps"], reverse=True)
        return comparisons