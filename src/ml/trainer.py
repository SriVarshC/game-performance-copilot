"""
ML Model Trainer for FPS Prediction — Phase 5 Upgrade
Trains 4 models:
  Model 1 — FPS Predictor         (LightGBM regressor)
  Model 2 — 1% Low FPS Predictor  (LightGBM regressor)
  Model 3 — Bottleneck Classifier (LightGBM classifier)
  Model 4 — Health Score Predictor(LightGBM regressor)
"""

import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    classification_report,
)
from sklearn.preprocessing import LabelEncoder

import xgboost as xgb
import lightgbm as lgb

from src.ml.dataset_generator import generate_dataset
from src.ml.feature_engineer import FeatureEngineer


class FPSModelTrainer:
    MODEL_DIR    = "models"
    RESULTS_PATH = "models/training_results.json"

    def __init__(self):
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        self.feature_engineer     = FeatureEngineer()
        self.bottleneck_encoder   = LabelEncoder()
        self.models               = {}
        self.results              = {}
        self.best_model_name      = None
        self.best_model           = None

    # ── Data ──────────────────────────────────────────────────────────────────
    def load_or_generate_data(self, n_samples: int = 5000) -> pd.DataFrame:
        dataset_path     = "data/fps_dataset.csv"
        required_columns = ["low_1pct_fps", "bottleneck_class", "health_score"]

        if os.path.exists(dataset_path):
            df = pd.read_csv(dataset_path)
            if all(col in df.columns for col in required_columns):
                print(f"[INFO] Loading existing dataset from {dataset_path}")
                print(f"[INFO] Loaded {len(df)} records.")
                return df
            else:
                print("[INFO] Dataset missing new target columns — regenerating...")
        else:
            print("[INFO] No dataset found — generating new dataset...")

        return generate_dataset(n_samples=n_samples)

    def prepare_data(self, df: pd.DataFrame):
        """Feature-engineer and split. Returns all targets together."""
        print("\n[INFO] Preparing features...")

        # ── Extract new targets BEFORE feature engineering ────────────────────
        y_low_fps    = df["low_1pct_fps"].values
        y_bottleneck = df["bottleneck_class"].values
        y_health     = df["health_score"].values

        # Encode bottleneck labels to integers
        y_bottleneck_enc = self.bottleneck_encoder.fit_transform(y_bottleneck)
        print(f"[INFO] Bottleneck classes: {list(self.bottleneck_encoder.classes_)}")

        # ── Feature engineer ──────────────────────────────────────────────────
        df_engineered = self.feature_engineer.fit_transform(df)
        X, y          = self.feature_engineer.get_X_y(df_engineered)

        print(f"[INFO] Features shape : {X.shape}")
        print(f"[INFO] FPS range      : {y.min():.1f} – {y.max():.1f}")
        print(f"[INFO] Health range   : {y_health.min():.1f} – {y_health.max():.1f}")

        # ── Single split — all targets share same indices ─────────────────────
        (X_train, X_test,
         y_train,    y_test,
         y_low_tr,   y_low_te,
         y_bt_tr,    y_bt_te,
         y_hs_tr,    y_hs_te) = train_test_split(
            X, y,
            y_low_fps, y_bottleneck_enc,
            y_health,
            test_size=0.2, random_state=42
        )

        print(f"[INFO] Train: {len(X_train)} | Test: {len(X_test)}")
        return (X_train, X_test,
                y_train,  y_test,
                y_low_tr, y_low_te,
                y_bt_tr,  y_bt_te,
                y_hs_tr,  y_hs_te)

    # ── Evaluation ────────────────────────────────────────────────────────────
    def _eval_regressor(self, model, X_test, y_test, name: str) -> dict:
        y_pred = model.predict(X_test)
        mae    = mean_absolute_error(y_test, y_pred)
        rmse   = np.sqrt(mean_squared_error(y_test, y_pred))
        r2     = r2_score(y_test, y_pred)
        mape   = np.mean(np.abs((y_test - y_pred) / np.maximum(y_test, 1))) * 100

        results = {
            "model":        name,
            "MAE":          round(mae, 3),
            "RMSE":         round(rmse, 3),
            "R2":           round(r2, 4),
            "MAPE_pct":     round(mape, 2),
            "accuracy_pct": round((1 - mape / 100) * 100, 2),
        }
        print(f"\n  {name} Results:")
        print(f"     R²       : {r2:.4f}")
        print(f"     MAE      : {mae:.2f}")
        print(f"     RMSE     : {rmse:.2f}")
        print(f"     Accuracy : {results['accuracy_pct']}%")
        return results

    def _eval_classifier(self, model, X_test, y_test, name: str) -> dict:
        y_pred   = model.predict(X_test)
        acc      = accuracy_score(y_test, y_pred)
        results  = {"model": name, "accuracy_pct": round(acc * 100, 2)}
        print(f"\n  {name} Results:")
        print(f"     Accuracy : {acc*100:.2f}%")
        print(classification_report(
            y_test, y_pred,
            target_names=self.bottleneck_encoder.classes_,
            zero_division=0
        ))
        return results

    # ── Training ──────────────────────────────────────────────────────────────
    def train_all_models(self, n_samples: int = 5000):
        print("=" * 60)
        print("   Game Performance Copilot — Phase 5 Model Trainer")
        print("=" * 60)

        df = self.load_or_generate_data(n_samples)
        (X_train, X_test,
         y_train,  y_test,
         y_low_tr, y_low_te,
         y_bt_tr,  y_bt_te,
         y_hs_tr,  y_hs_te) = self.prepare_data(df)

        print("\n" + "=" * 60)
        print("   Training Models...")
        print("=" * 60)

        # ── Model 1: XGBoost FPS ──────────────────────────────────────────────
        print("\n[1/6] Training XGBoost (FPS)...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=400, learning_rate=0.05,
            max_depth=7, subsample=0.85,
            colsample_bytree=0.85, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0,
            random_state=42, n_jobs=-1, verbosity=0
        )
        xgb_model.fit(X_train, y_train,
                      eval_set=[(X_test, y_test)], verbose=False)
        self.models["XGBoost"] = xgb_model
        self.results["XGBoost"] = self._eval_regressor(
            xgb_model, X_test, y_test, "XGBoost FPS")

        # ── Model 1 (winner): LightGBM FPS ───────────────────────────────────
        print("\n[2/6] Training LightGBM (FPS)...")
        lgb_fps = lgb.LGBMRegressor(
            n_estimators=400, learning_rate=0.05,
            max_depth=7, num_leaves=63,
            subsample=0.85, colsample_bytree=0.85,
            min_child_samples=20, reg_alpha=0.1, reg_lambda=1.0,
            random_state=42, n_jobs=-1, verbose=-1
        )
        lgb_fps.fit(X_train, y_train,
                    eval_set=[(X_test, y_test)],
                    callbacks=[lgb.early_stopping(50, verbose=False),
                               lgb.log_evaluation(period=-1)])
        self.models["LightGBM"] = lgb_fps
        self.results["LightGBM"] = self._eval_regressor(
            lgb_fps, X_test, y_test, "LightGBM FPS")

        # ── Model 2: LightGBM 1% Low FPS ─────────────────────────────────────
        print("\n[3/6] Training LightGBM (1% Low FPS)...")
        lgb_low = lgb.LGBMRegressor(
            n_estimators=300, learning_rate=0.05,
            max_depth=6, num_leaves=47,
            subsample=0.85, colsample_bytree=0.85,
            min_child_samples=20, random_state=42,
            n_jobs=-1, verbose=-1
        )
        lgb_low.fit(X_train, y_low_tr,
                    eval_set=[(X_test, y_low_te)],
                    callbacks=[lgb.early_stopping(50, verbose=False),
                               lgb.log_evaluation(period=-1)])
        self.models["LowFPS"] = lgb_low
        self.results["LowFPS"] = self._eval_regressor(
            lgb_low, X_test, y_low_te, "LightGBM 1% Low FPS")

        # ── Model 3: Bottleneck Classifier ────────────────────────────────────
        print("\n[4/6] Training LightGBM Bottleneck Classifier...")
        lgb_bt = lgb.LGBMClassifier(
            n_estimators=300, learning_rate=0.05,
            max_depth=6, num_leaves=47,
            subsample=0.85, colsample_bytree=0.85,
            min_child_samples=20, random_state=42,
            n_jobs=-1, verbose=-1
        )
        lgb_bt.fit(X_train, y_bt_tr,
                   eval_set=[(X_test, y_bt_te)],
                   callbacks=[lgb.early_stopping(50, verbose=False),
                               lgb.log_evaluation(period=-1)])
        self.models["Bottleneck"] = lgb_bt
        self.results["Bottleneck"] = self._eval_classifier(
            lgb_bt, X_test, y_bt_te, "Bottleneck Classifier")

        # ── Model 4: Health Score ─────────────────────────────────────────────
        print("\n[5/6] Training LightGBM (Health Score)...")
        lgb_hs = lgb.LGBMRegressor(
            n_estimators=300, learning_rate=0.05,
            max_depth=6, num_leaves=47,
            subsample=0.85, colsample_bytree=0.85,
            min_child_samples=20, random_state=42,
            n_jobs=-1, verbose=-1
        )
        lgb_hs.fit(X_train, y_hs_tr,
                   eval_set=[(X_test, y_hs_te)],
                   callbacks=[lgb.early_stopping(50, verbose=False),
                               lgb.log_evaluation(period=-1)])
        self.models["HealthScore"] = lgb_hs
        self.results["HealthScore"] = self._eval_regressor(
            lgb_hs, X_test, y_hs_te, "Health Score")

        # ── Model 5: Random Forest (FPS — kept for comparison) ────────────────
        print("\n[6/6] Training Random Forest (FPS)...")
        rf_model = RandomForestRegressor(
            n_estimators=200, max_depth=15,
            min_samples_split=5, min_samples_leaf=3,
            max_features="sqrt", random_state=42, n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        self.models["RandomForest"] = rf_model
        self.results["RandomForest"] = self._eval_regressor(
            rf_model, X_test, y_test, "Random Forest FPS")

        # ── Select Best FPS Model ─────────────────────────────────────────────
        fps_models = ["XGBoost", "LightGBM", "RandomForest"]
        best_r2    = -999
        for name in fps_models:
            if self.results[name]["R2"] > best_r2:
                best_r2              = self.results[name]["R2"]
                self.best_model_name = name
                self.best_model      = self.models[name]

        print(f"\n  Best FPS Model: {self.best_model_name} (R2={best_r2:.4f})")

        self._save_models()
        self._save_results()
        print("\n[INFO] Training complete! All 4 models saved.")
        return self.results

    # ── Save ──────────────────────────────────────────────────────────────────
    def _save_models(self):
        # FPS comparison models
        for name in ["XGBoost", "LightGBM", "RandomForest"]:
            path = f"{self.MODEL_DIR}/{name.lower()}_model.pkl"
            joblib.dump(self.models[name], path)
            print(f"[INFO] Saved {name} → {path}")

        # Best FPS model
        joblib.dump(self.best_model,
                    f"{self.MODEL_DIR}/best_model.pkl")
        print(f"[INFO] Best model ({self.best_model_name}) → models/best_model.pkl")

        # New models
        joblib.dump(self.models["LowFPS"],
                    f"{self.MODEL_DIR}/low_fps_model.pkl")
        joblib.dump(self.models["Bottleneck"],
                    f"{self.MODEL_DIR}/bottleneck_model.pkl")
        joblib.dump(self.models["HealthScore"],
                    f"{self.MODEL_DIR}/health_model.pkl")
        joblib.dump(self.bottleneck_encoder,
                    f"{self.MODEL_DIR}/bottleneck_encoder.pkl")
        print("[INFO] Saved low_fps_model, bottleneck_model, health_model, bottleneck_encoder")

        # Feature engineer
        self.feature_engineer.save()

        # Meta
        meta = {
            "best_model":        self.best_model_name,
            "trained_at":        datetime.now().isoformat(),
            "model_file":        "best_model.pkl",
            "low_fps_model":     "low_fps_model.pkl",
            "bottleneck_model":  "bottleneck_model.pkl",
            "health_model":      "health_model.pkl",
            "bottleneck_classes": list(self.bottleneck_encoder.classes_),
        }
        with open(f"{self.MODEL_DIR}/model_meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        print("[INFO] model_meta.json updated with all 4 model paths")

    def _save_results(self):
        with open(self.RESULTS_PATH, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"[INFO] Results → {self.RESULTS_PATH}")


if __name__ == "__main__":
    trainer = FPSModelTrainer()
    trainer.train_all_models(n_samples=5000)