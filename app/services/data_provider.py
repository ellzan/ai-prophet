"""Menyediakan akses ke data harga historis untuk training & inferensi.

Dirancang supaya sumber data mudah diganti nanti (CSV lokal sekarang,
bisa diganti koneksi database/PIHPS API tanpa mengubah pemanggil).
"""

import logging
from typing import Optional

import pandas as pd

from app.config import MIN_HISTORY_DAYS, RAW_DATA_PATH

logger = logging.getLogger(__name__)


class DataProvider:
    """Memuat dan menyajikan data harga historis dari CSV."""

    def __init__(self, csv_path: str = RAW_DATA_PATH) -> None:
        self.csv_path = csv_path
        self._df: Optional[pd.DataFrame] = None

    def load(self) -> None:
        """Muat CSV ke memori. Dipanggil sekali saat startup service."""
        df = pd.read_csv(self.csv_path)
        required_cols = {"date", "commodity", "province", "price"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(
                f"Kolom wajib hilang di {self.csv_path}: {missing}. "
                f"Format yang diharapkan: date, commodity, province, price"
            )
        df["date"] = pd.to_datetime(df["date"], errors="raise")
        df = df.sort_values("date").reset_index(drop=True)
        self._df = df
        logger.info(
            "DataProvider loaded: %d baris, %d komoditas, %d provinsi (%s s/d %s)",
            len(df),
            df["commodity"].nunique(),
            df["province"].nunique(),
            df["date"].min().date(),
            df["date"].max().date(),
        )

    def _ensure_loaded(self) -> pd.DataFrame:
        if self._df is None:
            raise RuntimeError("DataProvider belum di-load. Panggil .load() dulu.")
        return self._df

    def get_series(self, commodity: str, province: str) -> pd.DataFrame:
        """Ambil seluruh deret waktu untuk satu pasangan (commodity, province).

        Returns:
            DataFrame dengan kolom ds (tanggal) dan y (harga), format yang
            dibutuhkan Prophet.
        """
        df = self._ensure_loaded()
        subset = df[(df["commodity"] == commodity) & (df["province"] == province)]
        if subset.empty:
            raise KeyError(
                f"Tidak ada data untuk komoditas='{commodity}', provinsi='{province}'"
            )
        series = subset[["date", "price"]].rename(columns={"date": "ds", "price": "y"})
        return series.reset_index(drop=True)

    def latest_price(self, commodity: str, province: str) -> dict:
        """Harga terbaru + tanggalnya untuk ditampilkan sebagai 'harga hari ini'."""
        series = self.get_series(commodity, province)
        last_row = series.iloc[-1]
        return {"date": last_row["ds"].strftime("%Y-%m-%d"), "price": float(last_row["y"])}

    def has_enough_history(self, commodity: str, province: str) -> bool:
        try:
            series = self.get_series(commodity, province)
        except KeyError:
            return False
        return len(series) >= MIN_HISTORY_DAYS

    def available_commodities(self) -> list:
        df = self._ensure_loaded()
        return sorted(df["commodity"].unique().tolist())

    def available_provinces(self) -> list:
        df = self._ensure_loaded()
        return sorted(df["province"].unique().tolist())


# Singleton sederhana, mengikuti pola yang dipakai di seluruh service lain
# supaya FastAPI cukup punya satu instance yang di-load sekali saat startup.
_data_provider: Optional[DataProvider] = None


def init_data_provider(csv_path: str = RAW_DATA_PATH) -> DataProvider:
    global _data_provider
    _data_provider = DataProvider(csv_path=csv_path)
    _data_provider.load()
    return _data_provider


def get_data_provider() -> DataProvider:
    if _data_provider is None:
        raise RuntimeError("DataProvider belum diinisialisasi. Panggil init_data_provider().")
    return _data_provider
