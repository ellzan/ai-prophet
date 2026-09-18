from typing import List, Optional

from pydantic import BaseModel, Field


class PredictionQuery(BaseModel):
    commodity: str = Field(..., examples=["Cabai Rawit"])
    province: str = Field(..., examples=["Jawa Timur"])


class DailyForecast(BaseModel):
    date: str
    predicted_price: float
    confidence_low: float
    confidence_high: float


class PredictionResponse(BaseModel):
    commodity: str
    province: str
    current_price: float
    current_price_date: str
    forecast_horizon_days: int
    forecast: List[DailyForecast]
    change_14d_percent: float
    status: str
    insight: str
    model: str
    predicted_at: str


class ErrorDetail(BaseModel):
    error: str
    message: str


class CommoditiesResponse(BaseModel):
    commodities: List[str]


class ProvincesResponse(BaseModel):
    provinces: List[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    models_loaded: Optional[int] = None
