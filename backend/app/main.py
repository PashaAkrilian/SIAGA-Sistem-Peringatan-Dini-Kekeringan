"""
main.py
=======
Aplikasi FastAPI — "otak" backend yang menyajikan model ke dunia luar lewat
REST API. Frontend React akan memanggil endpoint-endpoint di sini.

Jalankan dev server:
    uvicorn app.main:app --reload --port 8000

Dokumentasi interaktif otomatis tersedia di:
    http://localhost:8000/docs
"""
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .auth import db as auth_db
from .auth.router import router as auth_router
from .auth.security import get_current_admin_user
from .model_service import service
from .schemas import (
    FeatureImportanceResponse,
    ForecastResponse,
    IslandSummary,
    MetricsResponse,
    SimulationResponse,
)

app = FastAPI(
    title="SDCI Drought Early Warning System API",
    description=(
        "REST API untuk sistem peringatan dini kekeringan nasional Indonesia "
        "berbasis XGBoost Quantile Regression. Menyajikan data historis SDCI, "
        "proyeksi 2026, feature importance (SHAP), dan simulasi what-if."
    ),
    version="1.0.0",
)

# CORS: izinkan frontend (Vite dev server & production) memanggil API ini.
# Origin production diatur lewat env var CORS_ALLOWED_ORIGINS (dipisah koma),
# supaya tidak perlu mencampur wildcard "*" dengan allow_credentials=True.
_default_origins = [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
]
_env_origins = [o.strip() for o in config.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_env_origins or _default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])


@app.on_event("startup")
def _startup():
    auth_db.init_db()


@app.get("/")
def root():
    return {
        "name": "SDCI Drought Early Warning System API",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/metrics", response_model=MetricsResponse, tags=["Model"])
def get_metrics():
    """Metrik performa model (RMSE, MAE, R²) pada data train & test."""
    return service.metrics


@app.get("/api/historical", tags=["Data"])
def get_historical(
    island: str = Query("Indo", description="Nama pulau: Indo, Jawa, Sumatera, dll"),
):
    """Deret waktu SDCI historis (2000-2025) untuk satu pulau, plus ONI."""
    valid = ["Indo", "Sumatera", "Jawa", "Kalimantan", "Sulawesi",
             "NusaTenggara", "Maluku", "Papua"]
    if island not in valid:
        raise HTTPException(400, f"Pulau tidak valid. Pilih dari: {valid}")
    series = []
    for row in service.historical:
        if island in row:
            series.append({
                "date": row["date"],
                "sdci": row[island],
                "oni": row["ONI"],
                "sst_anomaly": row["sst_anomaly"],
            })
    return {"island": island, "data": series}


@app.get("/api/historical-fit", tags=["Data"])
def get_historical_fit():
    """Garis prediksi model pada data historis (median + uncertainty band).
    Dipakai untuk overlay 'actual vs predicted' di chart."""
    return {"data": service.historical_fit}


@app.get("/api/forecast", response_model=ForecastResponse, tags=["Forecast"])
def get_forecast():
    """Proyeksi kekeringan 2026 (skenario default dari training)."""
    return service.forecast


@app.get("/api/feature-importance", response_model=FeatureImportanceResponse, tags=["Model"])
def get_feature_importance():
    """15-20 fitur paling berpengaruh menurut SHAP & gain XGBoost."""
    return service.feature_importance


@app.get("/api/islands", response_model=list[IslandSummary], tags=["Data"])
def get_islands():
    """Ringkasan tiap pulau: korelasi dengan ONI, skor terkini, status kekeringan."""
    return service.get_island_summary()


@app.get("/api/simulate", response_model=SimulationResponse, tags=["Forecast"])
def simulate(
    oni_increment: float = Query(
        0.15, ge=0.0, le=1.0,
        description="Kenaikan ONI per bulan (skenario pemanasan Pasifik)",
    ),
    start_oni: float | None = Query(
        None, description="Nilai ONI awal (default: nilai terakhir historis)",
    ),
):
    """Simulasi what-if real-time: ubah skenario kenaikan ONI, dapatkan
    proyeksi 2026 baru. Model kuantil dihitung ulang secara live."""
    return service.simulate(oni_increment=oni_increment, start_oni=start_oni)


@app.get("/api/admin/stats", tags=["Admin"])
def admin_stats(_admin=Depends(get_current_admin_user)):
    """Statistik singkat, khusus admin (butuh JWT dengan is_admin=true)."""
    return {"total_registered_users": auth_db.count_users(), "server_status": "ok"}
