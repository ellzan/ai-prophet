"""Konfigurasi terpusat untuk Pangan Pintar AI Service.

Semua nilai yang bisa berubah (daftar komoditas, provinsi, path artefak)
diletakkan di sini supaya tidak tersebar di banyak file.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")

RAW_DATA_PATH = os.path.join(DATA_DIR, "harga_historis.csv")

# 5 komoditas prioritas sesuai proposal (MVP). Tambah di sini kalau mau
COMMODITIES = [
    "Cabai Rawit",
    "Bawang Merah",
    "Beras",
    "Minyak Goreng",
    "Telur Ayam",
]

# 38 provinsi Indonesia yang didukung oleh data dummy dan endpoint.
PROVINCES = [
    "Aceh",
    "Sumatera Utara",
    "Sumatera Barat",
    "Riau",
    "Jambi",
    "Sumatera Selatan",
    "Bengkulu",
    "Lampung",
    "Kepulauan Bangka Belitung",
    "Kepulauan Riau",
    "DKI Jakarta",
    "Jawa Barat",
    "Jawa Tengah",
    "DI Yogyakarta",
    "Jawa Timur",
    "Banten",
    "Bali",
    "Nusa Tenggara Barat",
    "Nusa Tenggara Timur",
    "Kalimantan Barat",
    "Kalimantan Tengah",
    "Kalimantan Selatan",
    "Kalimantan Timur",
    "Kalimantan Utara",
    "Sulawesi Utara",
    "Sulawesi Tengah",
    "Sulawesi Selatan",
    "Sulawesi Tenggara",
    "Gorontalo",
    "Sulawesi Barat",
    "Maluku",
    "Maluku Utara",
    "Papua Barat",
    "Papua Barat Daya",
    "Papua",
    "Papua Tengah",
    "Papua Pegunungan",
    "Papua Selatan",
]

# Berapa hari ke depan yang diprediksi setiap kali endpoint /predict dipanggil.
FORECAST_HORIZON_DAYS = 14

# Minimal berapa hari histori yang dibutuhkan sebelum model dianggap layak
# dilatih/dipakai untuk satu pasangan (komoditas, provinsi).
MIN_HISTORY_DAYS = 180

MODEL_FILENAME_TEMPLATE = "prophet_{commodity}_{province}.json"
