"""Generate SAMPLE (bukan data asli) harga historis harian.

PENTING: Data yang dihasilkan skrip ini adalah data sintetis untuk keperluan
pengembangan & pengujian pipeline saja. SEBELUM dipakai untuk demo final,
GANTI file `data/harga_historis.csv` dengan data asli hasil unduhan dari:
  - Panel Harga Pangan Bapanas: https://panelharga.badanpangan.go.id
  - PIHPS Nasional: https://www.bi.go.id/hargapangan

Format CSV yang harus dihasilkan/disediakan (kolom wajib):
    date, commodity, province, price

Jalankan:
    python scripts/generate_sample_data.py
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import COMMODITIES, PROVINCES, RAW_DATA_PATH  # noqa: E402

np.random.seed(42)

START_DATE = "2024-01-01"
END_DATE = "2026-09-30"  # "hari ini" sesuai skenario proyek

# Harga dasar (baseline) per komoditas dalam Rupiah/kg, dan volatilitas relatif
# (dipakai supaya cabai/bawang lebih bergejolak daripada beras/minyak, sesuai
# karakteristik harga pangan riil di Indonesia).
BASE_PRICE = {
    "Cabai Rawit": 55000,
    "Bawang Merah": 35000,
    "Beras": 14000,
    "Minyak Goreng": 18000,
    "Telur Ayam": 28000,
}
VOLATILITY = {
    "Cabai Rawit": 0.35,
    "Bawang Merah": 0.20,
    "Beras": 0.05,
    "Minyak Goreng": 0.06,
    "Telur Ayam": 0.10,
}
# Faktor penyesuaian ringan antar provinsi (distribusi/ongkos logistik).
PROVINCE_FACTOR = {
    "DKI Jakarta": 1.00,
    "Jawa Barat": 0.97,
    "Jawa Timur": 0.95,
    "Sumatera Utara": 1.05,
}

# Tanggal hari raya (mendekati pola lonjakan permintaan pangan di Indonesia).
HOLIDAY_DATES = pd.to_datetime([
    "2024-04-10",  # Lebaran 2024
    "2024-06-17",  # Idul Adha 2024
    "2025-03-31",  # Lebaran 2025
    "2025-06-06",  # Idul Adha 2025
    "2026-03-20",  # Lebaran 2026
])


def holiday_effect(dates: pd.DatetimeIndex) -> np.ndarray:
    """Efek lonjakan harga menjelang hari raya (naik ~2 minggu sebelumnya)."""
    effect = np.zeros(len(dates))
    for h in HOLIDAY_DATES:
        days_to_holiday = (h - dates).days
        window = (days_to_holiday >= 0) & (days_to_holiday <= 14)
        # Lonjakan makin besar makin dekat ke hari-H, lalu turun setelahnya.
        effect[window] += (14 - days_to_holiday[window]) / 14 * 0.15
    return effect


def generate_series(commodity: str, province: str, dates: pd.DatetimeIndex) -> np.ndarray:
    n = len(dates)
    base = BASE_PRICE[commodity] * PROVINCE_FACTOR[province]
    vol = VOLATILITY[commodity]

    t = np.arange(n)
    trend = base * (1 + 0.00008 * t)  # tren naik perlahan (inflasi ringan)
    weekly_season = 1 + 0.01 * np.sin(2 * np.pi * t / 7)
    yearly_season = 1 + 0.05 * np.sin(2 * np.pi * t / 365)
    holiday = holiday_effect(dates)

    noise = np.random.normal(0, vol * 0.15, n)
    # Random walk ringan supaya ada momentum kenaikan/penurunan beruntun,
    # bukan cuma noise independen tiap hari (lebih realistis).
    walk = np.cumsum(np.random.normal(0, vol * 0.02, n))
    walk = walk - np.linspace(walk[0], walk[-1], n)  # netralkan drift jangka panjang

    price = trend * weekly_season * yearly_season * (1 + holiday + noise + walk)
    price = np.clip(price, base * 0.5, base * 2.5)
    return np.round(price, -2)  # bulatkan ke ratusan rupiah


def main():
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    rows = []
    for commodity in COMMODITIES:
        for province in PROVINCES:
            prices = generate_series(commodity, province, dates)
            for d, p in zip(dates, prices):
                rows.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "commodity": commodity,
                    "province": province,
                    "price": float(p),
                })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
    df.to_csv(RAW_DATA_PATH, index=False)
    print(f"[SAMPLE DATA] {len(df)} baris ditulis ke {RAW_DATA_PATH}")
    print("INGAT: ganti dengan data asli PIHPS/Bapanas sebelum demo final.")


if __name__ == "__main__":
    main()
