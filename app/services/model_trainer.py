"""Melatih satu model Prophet per pasangan (komoditas, provinsi).

Kenapa satu model per pasangan, bukan satu model besar untuk semua?
Karena pola harga tiap komoditas & wilayah berbeda-beda (cabai jauh lebih
bergejolak daripada beras, misalnya) — mencampur semuanya ke satu model
akan membuat model rata-rata dan tidak akurat untuk komoditas yang volatil.

Dijalankan lewat scripts/train.py, bukan saat runtime API, supaya endpoint
/predict selalu cepat (tinggal load model yang sudah jadi, bukan training
ulang tiap request).
"""

import json
import logging
import os

import pandas as pd
from prophet import Prophet
from prophet.serialize import model_to_json

from app.config import ARTIFACTS_DIR, MIN_HISTORY_DAYS, MODEL_FILENAME_TEMPLATE

logger = logging.getLogger(__name__)

# Tanggal hari raya nasional — dipakai sebagai "holidays" custom di Prophet
# supaya model tahu bahwa harga pangan cenderung naik menjelang Lebaran/Idul
# Adha, pola yang sangat khas di Indonesia dan tidak akan tertangkap oleh
# seasonality mingguan/tahunan biasa.
INDONESIAN_FOOD_HOLIDAYS = pd.DataFrame({
    "holiday": "hari_raya",
    "ds": pd.to_datetime([
        "2024-04-10", "2024-06-17",
        "2025-03-31", "2025-06-06",
        "2026-03-20", "2026-05-27",
    ]),
    "lower_window": -14,  # efek mulai terasa 14 hari sebelum hari-H
    "upper_window": 3,    # dan mereda 3 hari setelahnya
})


def train_one(series: pd.DataFrame, commodity: str, province: str) -> Prophet:
    """Latih satu model Prophet untuk satu pasangan (commodity, province).

    Args:
        series: DataFrame dengan kolom ds, y (lihat DataProvider.get_series).
    """
    if len(series) < MIN_HISTORY_DAYS:
        raise ValueError(
            f"Data terlalu sedikit untuk {commodity}/{province}: "
            f"{len(series)} baris (minimal {MIN_HISTORY_DAYS})"
        )

    model = Prophet(
        holidays=INDONESIAN_FOOD_HOLIDAYS,
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.1,  # sedikit lebih fleksibel dari default
        interval_width=0.8,           # untuk confidence interval di response
    )
    model.fit(series)
    return model


def save_model(model: Prophet, commodity: str, province: str) -> str:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    safe_commodity = commodity.lower().replace(" ", "_")
    safe_province = province.lower().replace(" ", "_")
    filename = MODEL_FILENAME_TEMPLATE.format(commodity=safe_commodity, province=safe_province)
    path = os.path.join(ARTIFACTS_DIR, filename)
    with open(path, "w") as f:
        f.write(model_to_json(model))
    return path


def evaluate(model: Prophet, series: pd.DataFrame, test_days: int = 30) -> dict:
    """Evaluasi sederhana: latih ulang tanpa N hari terakhir, lalu bandingkan
    prediksi vs harga aktual pada N hari tersebut. Mengembalikan MAPE (%).
    """
    if len(series) <= test_days + MIN_HISTORY_DAYS:
        return {"mape": None, "note": "Data tidak cukup untuk holdout evaluation"}

    train_part = series.iloc[:-test_days]
    test_part = series.iloc[-test_days:]

    eval_model = Prophet(
        holidays=INDONESIAN_FOOD_HOLIDAYS,
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.1,
    )
    eval_model.fit(train_part)

    future = eval_model.make_future_dataframe(periods=test_days)
    forecast = eval_model.predict(future)
    forecast_tail = forecast.tail(test_days).reset_index(drop=True)

    actual = test_part["y"].reset_index(drop=True)
    predicted = forecast_tail["yhat"]

    ape = ((actual - predicted).abs() / actual) * 100
    mape = float(ape.mean())
    return {"mape": round(mape, 2), "test_days": test_days}


def train_all(data_provider, commodities: list, provinces: list) -> dict:
    """Latih model untuk semua kombinasi komoditas x provinsi yang punya
    cukup data. Mengembalikan ringkasan hasil (termasuk MAPE) untuk dicatat
    ke metadata.json.
    """
    results = {}
    for commodity in commodities:
        for province in provinces:
            key = f"{commodity} / {province}"
            try:
                series = data_provider.get_series(commodity, province)
                if len(series) < MIN_HISTORY_DAYS:
                    logger.warning("Lewati %s: data kurang dari %d hari", key, MIN_HISTORY_DAYS)
                    results[key] = {"status": "skipped", "reason": "insufficient_data"}
                    continue

                metrics = evaluate(None, series)
                model = train_one(series, commodity, province)
                path = save_model(model, commodity, province)

                results[key] = {
                    "status": "trained",
                    "rows": len(series),
                    "mape": metrics.get("mape"),
                    "artifact": os.path.basename(path),
                }
                logger.info("Selesai: %s -> MAPE=%s%%", key, metrics.get("mape"))
            except Exception as exc:  # noqa: BLE001 - kita mau log semua kegagalan per pair
                logger.exception("Gagal melatih %s", key)
                results[key] = {"status": "failed", "error": str(exc)}

    metadata_path = os.path.join(ARTIFACTS_DIR, "training_report.json")
    with open(metadata_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info("Laporan training ditulis ke %s", metadata_path)
    return results
