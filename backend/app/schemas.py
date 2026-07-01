"""Pydantic schemas untuk validasi & dokumentasi otomatis API."""
from pydantic import BaseModel


class MetricSet(BaseModel):
    rmse: float
    mae: float
    r2: float


class MetricsResponse(BaseModel):
    train: MetricSet
    test: MetricSet


class HistoricalPoint(BaseModel):
    date: str
    Indo: float | None = None
    Sumatera: float | None = None
    Jawa: float | None = None
    Kalimantan: float | None = None
    Sulawesi: float | None = None
    NusaTenggara: float | None = None
    Maluku: float | None = None
    Papua: float | None = None
    ONI: float
    sst_anomaly: float


class FitPoint(BaseModel):
    date: str
    median: float
    lower: float
    upper: float


class ForecastPoint(FitPoint):
    below_critical: bool


class ForecastResponse(BaseModel):
    critical_threshold: float
    peak_month: str
    peak_score_median: float
    peak_score_lower: float
    peak_score_upper: float
    data: list[ForecastPoint]


class FeatureImportanceItem(BaseModel):
    feature: str
    value: float


class FeatureImportanceResponse(BaseModel):
    shap: list[FeatureImportanceItem]
    gain: list[FeatureImportanceItem]


class IslandSummary(BaseModel):
    island: str
    correlation_with_oni: float
    current_score: float
    status: str


class SimulationRequest(BaseModel):
    oni_monthly_increment: float = 0.15
    start_oni: float | None = None


class SimulationResponse(BaseModel):
    critical_threshold: float
    peak_month: str
    peak_score_median: float
    data: list[ForecastPoint]
