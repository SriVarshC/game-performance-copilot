"""
ML Model Trainer for FPS Prediction
Trains and compares XGBoost, LightGBM, and Random Forest.
Saves the best model automatically.
"""

import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
import xgboost as xgb
import lightgbm as lgb

from src.ml.dataset_generator import generate_dataset
from src.ml.feature_engineer import FeatureEngineer


class FPSModelTrainer:
    """
    Trains multiple ML models to predict FPS from hardware
    telemetry and game settings. Selects and saves the best one.
    """

    MODEL_DIR = "models"
    RESULTS_PATH = "models/training_results.json"

    def __init__(self):
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        self.feature_engineer = FeatureEngineer()
        self.models = {}
        self.results = {}
        self.best_model_name = None
        self.best_model = None

    def load_or_generate_data(self, n_samples: int = 5000) -> pd.DataFrame:
        """Load existing dataset or generate a new one."""
        dataset_path = "data/fps_dataset.csv"

        if os.path.exists(dataset_path):
            print(f"[INFO] Loading existing dataset from {dataset_path}")
            df = pd.read_csv(dataset_path)
            print(f"[INFO] Loaded {len(df)} records.")
        else:
            print("[INFO] No dataset found. Generating new dataset...")
            df = generate_dataset(n_samples=n_samples)

        return df

    def prepare_data(self, df: pd.DataFrame):
        """Feature engineer and split data into train/test sets."""
        print("\n[INFO] Preparing features...")

        # Fit and transform
        df_engineered = self.feature_engineer.fit_transform(df)
        X, y = self.feature_engineer.get_X_y(df_engineered)

        print(f"[INFO] Features shape: {X.shape}")
        print(f"[INFO] Target range: {y.min():.1f} - {y.max():.1f} FPS")

        # 80/20 split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"[INFO] Train: {len(X_train)} samples | Test: {len(X_test)} samples")
        return X_train, X_test, y_train, y_test

    def evaluate_model(self, model, X_test, y_test, model_name: str) -> dict:
        """Evaluate a trained model and return metrics."""
        y_pred = model.predict(X_test)

        mae  = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2   = r2_score(y_test, y_pred)

        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((y_test - y_pred) / np.maximum(y_test, 1))) * 100

        results = {
            "model":    model_name,
            "MAE":      round(mae, 3),
            "RMSE":     round(rmse, 3),
            "R2":       round(r2, 4),
            "MAPE_pct": round(mape, 2),
            "accuracy_pct": round((1 - mape / 100) * 100, 2)
        }

        print(f"\n  📊 {model_name} Results:")
        print(f"     R²       : {r2:.4f}  ({r2*100:.1f}% variance explained)")
        print(f"     MAE      : {mae:.2f} FPS")
        print(f"     RMSE     : {rmse:.2f} FPS")
        print(f"     MAPE     : {mape:.1f}%")
        print(f"     Accuracy : {results['accuracy_pct']}%")

        return results

    def train_all_models(self, n_samples: int = 5000):
        """Train all models and pick the best one."""
        print("=" * 60)
        print("   🎮 Game Performance Copilot — FPS Model Trainer")
        print("=" * 60)

        # Load data
        df = self.load_or_generate_data(n_samples)
        X_train, X_test, y_train, y_test = self.prepare_data(df)

        print("\n" + "=" * 60)
        print("   Training Models...")
        print("=" * 60)

        # ── 1. XGBoost ────────────────────────────────────────
        print("\n[1/3] Training XGBoost...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=7,
            subsample=0.85,
            colsample_bytree=0.85,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbosity=0
        )
        xgb_model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        self.models["XGBoost"] = xgb_model
        self.results["XGBoost"] = self.evaluate_model(
            xgb_model, X_test, y_test, "XGBoost"
        )

        # ── 2. LightGBM ───────────────────────────────────────
        print("\n[2/3] Training LightGBM...")
        lgb_model = lgb.LGBMRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=7,
            num_leaves=63,
            subsample=0.85,
            colsample_bytree=0.85,
            min_child_samples=20,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        lgb_model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            callbacks=[lgb.early_stopping(50, verbose=False),
                       lgb.log_evaluation(period=-1)]
        )
        self.models["LightGBM"] = lgb_model
        self.results["LightGBM"] = self.evaluate_model(
            lgb_model, X_test, y_test, "LightGBM"
        )

        # ── 3. Random Forest ──────────────────────────────────
        print("\n[3/3] Training Random Forest...")
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=3,
            max_features="sqrt",
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        self.models["RandomForest"] = rf_model
        self.results["RandomForest"] = self.evaluate_model(
            rf_model, X_test, y_test, "RandomForest"
        )

        # ── Select Best Model ─────────────────────────────────
        print("\n" + "=" * 60)
        print("   📊 Model Comparison")
        print("=" * 60)
        print(f"\n  {'Model':<15} {'R²':>8} {'MAE':>8} {'RMSE':>8} {'Accuracy':>10}")
        print(f"  {'-'*51}")

        best_r2 = -999
        for name, result in self.results.items():
            print(f"  {name:<15} {result['R2']:>8.4f} "
                  f"{result['MAE']:>7.2f}f "
                  f"{result['RMSE']:>7.2f}f "
                  f"{result['accuracy_pct']:>9.1f}%")
            if result["R2"] > best_r2:
                best_r2 = result["R2"]
                self.best_model_name = name
                self.best_model = self.models[name]

        print(f"\n  🏆 Best Model: {self.best_model_name} (R² = {best_r2:.4f})")

        # ── Save Everything ───────────────────────────────────
        self._save_models()
        self._save_results()
        self._print_feature_importance(X_train)

        print("\n[INFO] Training complete! ✅")
        return self.results

    def _save_models(self):
        """Save all trained models and the feature engineer."""
        for name, model in self.models.items():
            path = f"{self.MODEL_DIR}/{name.lower()}_model.pkl"
            joblib.dump(model, path)
            print(f"[INFO] Saved {name} → {path}")

        # Save best model separately for quick loading
        best_path = f"{self.MODEL_DIR}/best_model.pkl"
        joblib.dump(self.best_model, best_path)
        print(f"[INFO] Best model ({self.best_model_name}) saved → {best_path}")

        # Save feature engineer
        self.feature_engineer.save()

        # Save best model name
        meta = {
            "best_model": self.best_model_name,
            "trained_at": datetime.now().isoformat(),
            "model_file": "best_model.pkl"
        }
        with open(f"{self.MODEL_DIR}/model_meta.json", "w") as f:
            json.dump(meta, f, indent=2)

    def _save_results(self):
        """Save training results to JSON."""
        with open(self.RESULTS_PATH, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"[INFO] Results saved → {self.RESULTS_PATH}")

    def _print_feature_importance(self, X_train):
        """Print top 10 most important features."""
        print("\n  📌 Top 10 Feature Importances (Best Model):")
        try:
            importances = self.best_model.feature_importances_
            feat_imp = pd.Series(importances, index=X_train.columns)
            top10 = feat_imp.nlargest(10)
            for feat, imp in top10.items():
                bar = "█" * int(imp * 50)
                print(f"     {feat:<25} {imp:.4f}  {bar}")
        except Exception:
            pass


if __name__ == "__main__":
    trainer = FPSModelTrainer()
    trainer.train_all_models(n_samples=5000)