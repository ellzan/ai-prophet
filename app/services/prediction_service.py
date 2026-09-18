"""Orkestrasi prediksi harga 14 hari ke depan.

Beda penting dengan pendekatan single-target-week: Prophet secara alami
menghasilkan proyeksi untuk banyak hari sekaligus dalam satu kali predict(),
jadi endpoint /predict di sini langsung mengembalikan KURVA 14 hari, sesuai
janji fitur "AI Price Prediction (Prediksi Harga 14 Hari)" di proposal —
bukan satu titik harga per request seperti pendekatan mingguan.
"""

import logging
from datetime import datetime

import pandas as pd

from app.config import FORECAST_HORIZON_DAYS
from app.services.data_provider import DataProvider
from app.services.model_loader import ModelLoader

logger = logging.getLogger(__name__)


def _build_insight(current_price: float, day7: float, day14: float) -> str:
    """Insight otomatis bahasa manusia, sesuai fitur 'Insight tren otomatis'
    di proposal (mis. 'Cabai diprediksi naik 12% dalam 3 hari')."""
    change_14 = (day14 - current_price) / current_price * 100

    if abs(change_14) < 2:
        return "Harga diproyeksikan relatif stabil dalam 14 hari ke depan."

    arah = "naik" if change_14 > 0 else "turun"
    return (
        f"Harga diproyeksikan {arah} sekitar {abs(round(change_14, 1))}% "
        f"dalam 14 hari ke depan."
    )


def _status_label(change_percent: float) -> str:
    """Label status konsisten dengan yang dipakai di UI (Naik Drastis, Naik,
    Stabil, Turun, Turun Drastis) — samakan ambang batas dengan frontend."""
    if change_percent >= 15:
        return "Naik Drastis"
    if change_percent >= 3:
        return "Naik"
    if change_percent <= -15:
        return "Turun Drastis"
    if change_percent <= -3:
        return "Turun"
    return "Stabil"


class PredictionService:
    def __init__(self, model_loader: ModelLoader, data_provider: DataProvider) -> None:
        self.model_loader = model_loader
        self.data_provider = data_provider

    def predict(self, commodity: str, province: str) -> dict:
        if not self.model_loader.is_available(commodity, province):
            raise KeyError(
                f"Model untuk '{commodity}' di '{province}' belum tersedia."
            )

        model = self.model_loader.get_model(commodity, province)
        latest = self.data_provider.latest_price(commodity, province)
        current_price = latest["price"]
        current_date = latest["date"]

        future = model.make_future_dataframe(periods=FORECAST_HORIZON_DAYS)
        forecast = model.predict(future)
        forecast_tail = forecast.tail(FORECAST_HORIZON_DAYS).reset_index(drop=True)

        daily_forecast = []
        for _, row in forecast_tail.iterrows():
            daily_forecast.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "predicted_price": round(float(row["yhat"]), 2),
                "confidence_low": round(float(row["yhat_lower"]), 2),
                "confidence_high": round(float(row["yhat_upper"]), 2),
            })

        day7_price = daily_forecast[6]["predicted_price"] if len(daily_forecast) >= 7 else daily_forecast[-1]["predicted_price"]
        day14_price = daily_forecast[-1]["predicted_price"]
        change_14_percent = round((day14_price - current_price) / current_price * 100, 2)

        return {
            "commodity": commodity,
            "province": province,
            "current_price": current_price,
            "current_price_date": current_date,
            "forecast_horizon_days": FORECAST_HORIZON_DAYS,
            "forecast": daily_forecast,
            "change_14d_percent": change_14_percent,
            "status": _status_label(change_14_percent),
            "insight": _build_insight(current_price, day7_price, day14_price),
            "model": "Prophet",
            "predicted_at": datetime.now().isoformat(),
        }


_prediction_service: "PredictionService | None" = None


def init_prediction_service(model_loader: ModelLoader, data_provider: DataProvider) -> PredictionService:
    global _prediction_service
    _prediction_service = PredictionService(model_loader=model_loader, data_provider=data_provider)
    return _prediction_service


def get_prediction_service() -> PredictionService:
    if _prediction_service is None:
        raise RuntimeError("PredictionService belum diinisialisasi.")
    return _prediction_service
