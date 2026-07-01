"""
features.py
===========
Modul feature engineering yang dipakai backend saat inference real-time.
Identik dengan yang ada di training/train.py — ini prinsip penting dalam
ML engineering: pipeline fitur harus SAMA persis antara training & serving,
kalau beda dikit hasilnya bisa ngaco (namanya "training-serving skew").
"""
import pandas as pd


def create_advanced_temporal_features(df: pd.DataFrame, columns_to_engineer=("ONI",)) -> pd.DataFrame:
    """Ekstraksi lag, rolling stats, EMA, dan kinematika (momentum/akselerasi)."""
    df_feat = df.copy()

    for col in columns_to_engineer:
        if col not in df_feat.columns:
            continue

        for lag in [1, 2, 3, 4, 5, 6, 12]:
            df_feat[f"{col}_lag_{lag}"] = df_feat[col].shift(lag)

        for w in [3, 6]:
            df_feat[f"{col}_roll_mean_{w}"] = df_feat[col].rolling(window=w).mean()
            df_feat[f"{col}_roll_std_{w}"] = df_feat[col].rolling(window=w).std()
            df_feat[f"{col}_roll_max_{w}"] = df_feat[col].rolling(window=w).max()
            df_feat[f"{col}_roll_min_{w}"] = df_feat[col].rolling(window=w).min()

        for e in [3, 6]:
            df_feat[f"{col}_ema_{e}"] = df_feat[col].ewm(span=e, adjust=False).mean()

        df_feat[f"{col}_momentum_1"] = df_feat[col] - df_feat[f"{col}_lag_1"]
        df_feat[f"{col}_momentum_3"] = df_feat[col] - df_feat[f"{col}_lag_3"]
        df_feat[f"{col}_accel_1"] = df_feat[f"{col}_momentum_1"] - df_feat[f"{col}_momentum_1"].shift(1)

    return df_feat
