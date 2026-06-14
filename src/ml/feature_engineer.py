"""
Feature Engineering Pipeline for FPS Prediction
Transforms raw telemetry + game settings into ML-ready features.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib
import os


class FeatureEngineer:
    """
    Handles all feature engineering for FPS prediction.
    Encodes categorical variables, scales numerics,
    and creates derived features.
    """

    # Categorical columns to encode
    CATEGORICAL_COLS = ["game_genre", "resolution", "preset", "upscaling"]

    # Numeric feature columns used for training
    NUMERIC_FEATURES = [
        "gpu_utilization",
        "vram_used_mb",
        "vram_utilization",
        "cpu_utilization",
        "ram_utilization",
        "gpu_temperature",
        "gpu_clock_mhz",
        "gpu_power_watts",
        "cpu_gpu_ratio",
        "vram_pressure",
        "thermal_throttle",
        "resolution_width",
        "resolution_height",
        "total_pixels",
        "preset_ordinal",
        "ray_tracing",
    ]

    # Final feature list (numeric + encoded categoricals)
    FEATURE_COLS = NUMERIC_FEATURES + [
        "game_genre_enc",
        "resolution_enc",
        "preset_enc",
        "upscaling_enc",
    ]

    TARGET_COL = "fps"

    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.is_fitted = False

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit encoders on training data and transform."""
        df = df.copy()

        # Encode categorical columns
        for col in self.CATEGORICAL_COLS:
            le = LabelEncoder()
            df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))
            self.label_encoders[col] = le

        self.is_fitted = True
        print(f"[INFO] Feature engineering complete.")
        print(f"[INFO] Feature columns: {len(self.FEATURE_COLS)}")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform new data using fitted encoders."""
        if not self.is_fitted:
            raise ValueError("FeatureEngineer must be fitted first. Call fit_transform().")

        df = df.copy()

        for col in self.CATEGORICAL_COLS:
            le = self.label_encoders[col]
            # Handle unseen categories gracefully
            df[f"{col}_enc"] = df[col].astype(str).apply(
                lambda x: le.transform([x])[0]
                if x in le.classes_
                else -1
            )

        return df

    def get_X_y(self, df: pd.DataFrame):
        """Extract feature matrix X and target vector y."""
        available_cols = [c for c in self.FEATURE_COLS if c in df.columns]
        X = df[available_cols].fillna(0)
        y = df[self.TARGET_COL]
        return X, y

    def save(self, path: str = "models/feature_engineer.pkl"):
        """Save the fitted feature engineer to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self, path)
        print(f"[INFO] Feature engineer saved to: {path}")

    @classmethod
    def load(cls, path: str = "models/feature_engineer.pkl"):
        """Load a saved feature engineer from disk."""
        obj = joblib.load(path)
        print(f"[INFO] Feature engineer loaded from: {path}")
        return obj

    def build_prediction_input(self, live_metrics: dict,
                                game_genre: str,
                                resolution: str,
                                preset: str,
                                ray_tracing: bool,
                                upscaling: str) -> pd.DataFrame:
        """
        Build a single prediction input row from live telemetry + user settings.
        Used by the dashboard to predict FPS in real time.
        """
        gpu = live_metrics.get("gpu", {})
        cpu = live_metrics.get("cpu", {})
        mem = live_metrics.get("memory", {})

        gpu_util  = gpu.get("gpu_utilization") or 0
        vram_used = gpu.get("vram_used_mb") or 0
        vram_util = gpu.get("vram_utilization") or 0
        cpu_util  = cpu.get("cpu_utilization") or 0
        ram_util  = mem.get("ram_utilization") or 0
        gpu_temp  = gpu.get("gpu_temperature") or 0
        gpu_clock = gpu.get("gpu_clock_mhz") or 0
        gpu_power = gpu.get("gpu_power_watts") or 0

        from src.ml.dataset_generator import GAME_PROFILES, PRESET_CONFIG

        res_w, res_h = map(int, resolution.split("x"))
        preset_ord   = list(PRESET_CONFIG.keys()).index(preset)

        row = {
            "game_genre":      game_genre,
            "resolution":      resolution,
            "preset":          preset,
            "ray_tracing":     int(ray_tracing),
            "upscaling":       upscaling,
            "gpu_utilization": gpu_util,
            "vram_used_mb":    vram_used,
            "vram_utilization":vram_util,
            "cpu_utilization": cpu_util,
            "ram_utilization": ram_util,
            "gpu_temperature": gpu_temp,
            "gpu_clock_mhz":   gpu_clock,
            "gpu_power_watts": gpu_power,
            "cpu_gpu_ratio":   round(cpu_util / max(gpu_util, 1), 4),
            "vram_pressure":   int(vram_used > 3000),
            "thermal_throttle":int(gpu_temp > 85),
            "resolution_width": res_w,
            "resolution_height":res_h,
            "total_pixels":    res_w * res_h,
            "preset_ordinal":  preset_ord,
        }

        df = pd.DataFrame([row])
        df = self.transform(df)
        return df