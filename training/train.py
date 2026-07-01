"""
train.py
========
Melatih ulang model SDCI Drought Early Warning System dari dataset mentah.

Ini adalah versi "production" dari notebook riset (godzila-el-nino.ipynb):
- Feature engineering (lags, rolling stats, EMA, kinematika ONI) direplikasi
  jadi fungsi reusable.
- Hyperparameter tuning pakai Optuna (versi ringkas, 40 trial, dibanding versi
  notebook yang lebih berat).
- Melatih 1 model utama (untuk SHAP & feature importance) + 3 model kuantil
  (10%, 50%, 90%) untuk uncertainty band.
- Menyimpan semua artefak yang dibutuhkan backend FastAPI ke folder
  backend/data/ sebagai file JSON/native XGBoost format (bukan pickle,
  supaya aman & portable).

Cara jalanin:
    python train.py
"""

import json
import warnings
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

HERE = Path(__file__).parent
CSV_PATH = HERE / "master_dataset_godzilla_elnino_2000_2025.csv"
OUT_DIR = HERE.parent / "backend" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_COL = "SDCI_Indo"
CRITICAL_THRESHOLD = 0.3
ISLANDS = [
    "Indo", "Sumatera", "Jawa", "Kalimantan",
    "Sulawesi", "NusaTenggara", "Maluku", "Papua",
]


# ---------------------------------------------------------------------------
# 1. FEATURE ENGINEERING (sama seperti Cell 32 notebook)
# ---------------------------------------------------------------------------
def create_advanced_temporal_features(df: pd.DataFrame, columns_to_engineer=("ONI",)) -> pd.DataFrame:
    """Ekstraksi lag, rolling stats, EMA, dan kinematika (momentum/akselerasi)."""
    df_feat = df.copy()

    for col in columns_to_engineer:
        if col not in df_feat.columns:
            continue

        # Lags jangka pendek (1-6 bulan) + musiman (12 bulan)
        for lag in [1, 2, 3, 4, 5, 6, 12]:
            df_feat[f"{col}_lag_{lag}"] = df_feat[col].shift(lag)

        # Rolling window statistics
        for w in [3, 6]:
            df_feat[f"{col}_roll_mean_{w}"] = df_feat[col].rolling(window=w).mean()
            df_feat[f"{col}_roll_std_{w}"] = df_feat[col].rolling(window=w).std()
            df_feat[f"{col}_roll_max_{w}"] = df_feat[col].rolling(window=w).max()
            df_feat[f"{col}_roll_min_{w}"] = df_feat[col].rolling(window=w).min()

        # Exponential Moving Average
        for e in [3, 6]:
            df_feat[f"{col}_ema_{e}"] = df_feat[col].ewm(span=e, adjust=False).mean()

        # Kinematika iklim: momentum (turunan-1) & akselerasi (turunan-2)
        df_feat[f"{col}_momentum_1"] = df_feat[col] - df_feat[f"{col}_lag_1"]
        df_feat[f"{col}_momentum_3"] = df_feat[col] - df_feat[f"{col}_lag_3"]
        df_feat[f"{col}_accel_1"] = df_feat[f"{col}_momentum_1"] - df_feat[f"{col}_momentum_1"].shift(1)

    return df_feat


def main():
    print("=" * 70)
    print("STEP 1: LOAD & FEATURE ENGINEERING")
    print("=" * 70)

    df_master = pd.read_csv(CSV_PATH)
    df_master["date_key"] = pd.to_datetime(df_master["date_key"])
    df_master = df_master.sort_values("date_key").reset_index(drop=True)

    df_engineered = create_advanced_temporal_features(df_master, columns_to_engineer=["ONI"])
    df_engineered = df_engineered.dropna().reset_index(drop=True)
    print(f"Dataset setelah feature engineering: {df_engineered.shape}")

    # -----------------------------------------------------------------
    # 2. FEATURE / TARGET SPLIT (audit anti data-leakage, sama seperti notebook)
    # -----------------------------------------------------------------
    exclude_patterns = ["SDCI", "date", "Periode", "index", "Unnamed"]
    feature_cols = [c for c in df_engineered.columns if not any(p in c for p in exclude_patterns)]
    X_all = df_engineered[feature_cols].select_dtypes(include=[np.number])
    y_all = df_engineered[TARGET_COL]

    split_idx = int(len(df_engineered) * 0.8)
    X_train, X_test = X_all.iloc[:split_idx], X_all.iloc[split_idx:]
    y_train, y_test = y_all.iloc[:split_idx], y_all.iloc[split_idx:]
    dates_all = df_engineered["date_key"]

    print(f"Fitur terpakai: {len(X_all.columns)} kolom")
    print(f"Train: {len(X_train)} baris | Test: {len(X_test)} baris")

    # -----------------------------------------------------------------
    # 3. BAYESIAN HYPERPARAMETER TUNING (Optuna, versi ringkas)
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 2: BAYESIAN OPTIMIZATION (Optuna, 40 trials)")
    print("=" * 70)

    def objective(trial):
        param = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 500),
            "max_depth": trial.suggest_int("max_depth", 3, 9),
            "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.1, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 0.9),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 0.9),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            "gamma": trial.suggest_float("gamma", 1e-3, 1.0, log=True),
            "random_state": 42,
            "objective": "reg:squarederror",
            "n_jobs": -1,
        }
        tscv = TimeSeriesSplit(n_splits=5)
        scores = []
        for fold, (tr_idx, val_idx) in enumerate(tscv.split(X_train)):
            X_tr, X_val = X_train.iloc[tr_idx], X_train.iloc[val_idx]
            y_tr, y_val = y_train.iloc[tr_idx], y_train.iloc[val_idx]
            model = xgb.XGBRegressor(**param)
            model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
            preds = model.predict(X_val)
            rmse = np.sqrt(mean_squared_error(y_val, preds))
            scores.append(rmse)
            trial.report(rmse, fold)
            if trial.should_prune():
                raise optuna.exceptions.TrialPruned()
        return float(np.mean(scores))

    study = optuna.create_study(direction="minimize", pruner=optuna.pruners.MedianPruner())
    study.optimize(objective, n_trials=40, show_progress_bar=False)
    best_params = study.best_params.copy()
    print(f"Best CV RMSE: {study.best_value:.5f}")
    print(f"Best params: {best_params}")

    # -----------------------------------------------------------------
    # 4. FINAL MODEL FIT (untuk SHAP & feature importance)
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 3: FINAL MODEL FIT")
    print("=" * 70)

    final_params = best_params.copy()
    final_params.update({
        "random_state": 42,
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "n_jobs": -1,
    })
    final_model = xgb.XGBRegressor(**final_params, early_stopping_rounds=50)
    final_model.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)], verbose=False)

    preds_test = final_model.predict(X_test)
    preds_train = final_model.predict(X_train)
    metrics = {
        "train": {
            "rmse": float(np.sqrt(mean_squared_error(y_train, preds_train))),
            "mae": float(mean_absolute_error(y_train, preds_train)),
            "r2": float(r2_score(y_train, preds_train)),
        },
        "test": {
            "rmse": float(np.sqrt(mean_squared_error(y_test, preds_test))),
            "mae": float(mean_absolute_error(y_test, preds_test)),
            "r2": float(r2_score(y_test, preds_test)),
        },
    }
    print(f"Test R2: {metrics['test']['r2']:.4f} | Test RMSE: {metrics['test']['rmse']:.4f}")

    # -----------------------------------------------------------------
    # 5. SHAP EXPLAINABILITY
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 4: SHAP FEATURE IMPORTANCE")
    print("=" * 70)
    explainer = shap.TreeExplainer(final_model)
    shap_values = explainer.shap_values(X_test)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    shap_importance = (
        pd.Series(mean_abs_shap, index=X_test.columns)
        .sort_values(ascending=False)
        .head(20)
    )

    feat_importance = (
        pd.Series(final_model.feature_importances_, index=X_train.columns)
        .sort_values(ascending=False)
        .head(20)
    )

    # -----------------------------------------------------------------
    # 6. QUANTILE MODELS (pakai fitur ONI saja, konsisten sama notebook)
    #    Ini yang dipakai untuk proyeksi masa depan + uncertainty band.
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 5: QUANTILE REGRESSION (10% / 50% / 90%)")
    print("=" * 70)
    oni_features = [c for c in X_train.columns if "ONI" in c]
    print(f"Fitur ONI dipakai untuk forecasting: {len(oni_features)}")

    def train_quantile_model(alpha):
        params = best_params.copy()
        params.update({
            "objective": "reg:quantileerror",
            "quantile_alpha": alpha,
            "learning_rate": 0.05,
            "random_state": 42,
        })
        model = xgb.XGBRegressor(**params)
        model.fit(X_train[oni_features], y_train)
        return model

    model_lower = train_quantile_model(0.1)
    model_med = train_quantile_model(0.5)
    model_upper = train_quantile_model(0.9)

    # -----------------------------------------------------------------
    # 7. SIMULASI MASA DEPAN 2026 (Self-Simulated Escalation Scenario)
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 6: FUTURE PROJECTION (2026)")
    print("=" * 70)

    last_date = df_master["date_key"].iloc[-1]
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=12, freq="MS")
    start_oni = df_master["ONI"].iloc[-1]
    simulated_oni = [start_oni + (0.15 * i) for i in range(1, 13)]
    df_sim = pd.DataFrame({"date_key": future_dates, "ONI": simulated_oni})

    hist_tail = df_master[["date_key", "ONI"]].tail(12).copy()
    concat_sim = pd.concat([hist_tail, df_sim], ignore_index=True)
    full_feat_sim = create_advanced_temporal_features(concat_sim, columns_to_engineer=["ONI"])
    df_future = full_feat_sim.iloc[12:].reset_index(drop=True)

    y_hist_med = model_med.predict(X_all[oni_features])
    y_hist_low = model_lower.predict(X_all[oni_features])
    y_hist_high = model_upper.predict(X_all[oni_features])

    y_fut_med = model_med.predict(df_future[oni_features])
    y_fut_low = model_lower.predict(df_future[oni_features])
    y_fut_high = model_upper.predict(df_future[oni_features])

    peak_idx = int(np.argmin(y_fut_med))
    print(f"Bulan puncak proyeksi kekeringan: {future_dates[peak_idx].strftime('%B %Y')}")
    print(f"Skor SDCI median terendah: {y_fut_med[peak_idx]:.4f}")

    # -----------------------------------------------------------------
    # 8. SIMPAN SEMUA ARTEFAK UNTUK BACKEND
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 7: SAVE ARTIFACTS")
    print("=" * 70)

    # Model files (native XGBoost json format, bukan pickle)
    final_model.save_model(str(OUT_DIR / "model_main.json"))
    model_lower.save_model(str(OUT_DIR / "model_q10.json"))
    model_med.save_model(str(OUT_DIR / "model_q50.json"))
    model_upper.save_model(str(OUT_DIR / "model_q90.json"))

    # Feature lists (urutan kolom penting untuk inference nanti)
    with open(OUT_DIR / "features.json", "w") as f:
        json.dump({
            "main_features": list(X_train.columns),
            "oni_features": oni_features,
        }, f, indent=2)

    # Metrics
    with open(OUT_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # Feature importance & SHAP
    with open(OUT_DIR / "feature_importance.json", "w") as f:
        json.dump({
            "shap": [{"feature": k, "value": float(v)} for k, v in shap_importance.items()],
            "gain": [{"feature": k, "value": float(v)} for k, v in feat_importance.items()],
        }, f, indent=2)

    # Historical data per island (buat chart & tabel di frontend)
    hist_records = []
    for _, row in df_master.iterrows():
        rec = {"date": row["date_key"].strftime("%Y-%m-%d")}
        for isl in ISLANDS:
            col = f"SDCI_{isl}"
            if col in df_master.columns:
                rec[isl] = float(row[col])
        rec["ONI"] = float(row["ONI"])
        rec["sst_anomaly"] = float(row["sst_anomaly"])
        hist_records.append(rec)
    with open(OUT_DIR / "historical.json", "w") as f:
        json.dump(hist_records, f, indent=2)

    # Model fit line on historical (median + band) for chart overlay
    fit_records = []
    for d, m, lo, hi in zip(dates_all, y_hist_med, y_hist_low, y_hist_high):
        fit_records.append({
            "date": pd.Timestamp(d).strftime("%Y-%m-%d"),
            "median": float(m),
            "lower": float(lo),
            "upper": float(hi),
        })
    with open(OUT_DIR / "historical_fit.json", "w") as f:
        json.dump(fit_records, f, indent=2)

    # Future forecast (2026)
    forecast_records = []
    for d, m, lo, hi in zip(future_dates, y_fut_med, y_fut_low, y_fut_high):
        forecast_records.append({
            "date": pd.Timestamp(d).strftime("%Y-%m-%d"),
            "median": float(m),
            "lower": float(lo),
            "upper": float(hi),
            "below_critical": bool(m < CRITICAL_THRESHOLD),
        })
    with open(OUT_DIR / "forecast.json", "w") as f:
        json.dump({
            "critical_threshold": CRITICAL_THRESHOLD,
            "peak_month": future_dates[peak_idx].strftime("%Y-%m-%d"),
            "peak_score_median": float(y_fut_med[peak_idx]),
            "peak_score_lower": float(y_fut_low[peak_idx]),
            "peak_score_upper": float(y_fut_high[peak_idx]),
            "data": forecast_records,
        }, f, indent=2)

    # Spatial correlation table (island vs ONI)
    corr_records = []
    for isl in ISLANDS:
        col = f"SDCI_{isl}"
        if col in df_master.columns:
            corr_records.append({
                "island": isl,
                "correlation_with_oni": float(df_master[col].corr(df_master["ONI"])),
                "current_score": float(df_master[col].iloc[-1]),
            })
    with open(OUT_DIR / "island_summary.json", "w") as f:
        json.dump(corr_records, f, indent=2)

    print(f"\nSemua artefak tersimpan di: {OUT_DIR}")
    print("Selesai! Backend sekarang bisa membaca folder backend/data/")


if __name__ == "__main__":
    main()
