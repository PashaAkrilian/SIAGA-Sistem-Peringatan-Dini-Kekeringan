"""
model_service.py
================
Layer yang membungkus model & data. Bertanggung jawab:
- Load semua artefak sekali saat startup (bukan tiap request → lebih cepat).
- Menyediakan data historis, forecast, metrics, dll ke endpoint.
- Menjalankan simulasi "what-if" real-time: user mengubah skenario kenaikan
  ONI, backend menghitung ulang proyeksi 2026 pakai model kuantil.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from .features import create_advanced_temporal_features

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = Path(__file__).parent.parent / "data" / "master_dataset.csv"
CRITICAL_THRESHOLD = 0.3


def _classify(score: float) -> str:
    if score < CRITICAL_THRESHOLD:
        return "extreme"
    if score < 0.45:
        return "warning"
    return "normal"


class ModelService:
    def __init__(self):
        self._load()

    def _load(self):
        # Static JSON artifacts
        self.metrics = self._read_json("metrics.json")
        self.historical = self._read_json("historical.json")
        self.historical_fit = self._read_json("historical_fit.json")
        self.forecast = self._read_json("forecast.json")
        self.feature_importance = self._read_json("feature_importance.json")
        self.island_summary = self._read_json("island_summary.json")
        self.features = self._read_json("features.json")
        self.oni_features = self.features["oni_features"]

        # Quantile models for live simulation
        self.model_lower = self._load_model("model_q10.json")
        self.model_med = self._load_model("model_q50.json")
        self.model_upper = self._load_model("model_q90.json")

        # Master data (for simulation feature engineering) — try CSV, else rebuild
        self.oni_history = pd.DataFrame(
            [{"date_key": h["date"], "ONI": h["ONI"]} for h in self.historical]
        )
        self.oni_history["date_key"] = pd.to_datetime(self.oni_history["date_key"])
        self.last_oni = float(self.oni_history["ONI"].iloc[-1])
        self.last_date = self.oni_history["date_key"].iloc[-1]

    def _read_json(self, name):
        with open(DATA_DIR / name) as f:
            return json.load(f)

    def _load_model(self, name):
        model = xgb.XGBRegressor()
        model.load_model(str(DATA_DIR / name))
        return model

    # -- island summary with status label --
    def get_island_summary(self):
        out = []
        for row in self.island_summary:
            out.append({**row, "status": _classify(row["current_score"])})
        return out

    # -- live what-if simulation --
    def simulate(self, oni_increment: float = 0.15, start_oni: float | None = None):
        start = self.last_oni if start_oni is None else start_oni
        future_dates = pd.date_range(
            start=self.last_date + pd.DateOffset(months=1), periods=12, freq="MS"
        )
        simulated_oni = [start + (oni_increment * i) for i in range(1, 13)]
        df_sim = pd.DataFrame({"date_key": future_dates, "ONI": simulated_oni})

        hist_tail = self.oni_history.tail(12).copy()
        concat_sim = pd.concat([hist_tail, df_sim], ignore_index=True)
        full_feat = create_advanced_temporal_features(concat_sim, columns_to_engineer=["ONI"])
        df_future = full_feat.iloc[12:].reset_index(drop=True)

        X = df_future[self.oni_features]
        med = self.model_med.predict(X)
        low = self.model_lower.predict(X)
        high = self.model_upper.predict(X)

        data = []
        for d, m, lo, hi in zip(future_dates, med, low, high):
            data.append({
                "date": d.strftime("%Y-%m-%d"),
                "median": float(m),
                "lower": float(lo),
                "upper": float(hi),
                "below_critical": bool(m < CRITICAL_THRESHOLD),
            })

        peak_idx = int(np.argmin(med))
        return {
            "critical_threshold": CRITICAL_THRESHOLD,
            "peak_month": future_dates[peak_idx].strftime("%Y-%m-%d"),
            "peak_score_median": float(med[peak_idx]),
            "data": data,
        }


# Singleton
service = ModelService()
