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
# memperluas cakupan — tinggal pastikan data historisnya juga tersedia.
COMMODITIES = [
    "Cabai Rawit",
    "Bawang Merah",
    "Beras",
    "Minyak Goreng",
    "Telur Ayam",
]

# Wilayah yang didukung untuk versi awal. Bisa ditambah setelah data per
# provinsi lain tersedia.
PROVINCES = [
    "DKI Jakarta",
    "Jawa Barat",
    "Jawa Timur",
    "Sumatera Utara",
]

# Berapa hari ke depan yang diprediksi setiap kali endpoint /predict dipanggil.
FORECAST_HORIZON_DAYS = 14

# Minimal berapa hari histori yang dibutuhkan sebelum model dianggap layak
# dilatih/dipakai untuk satu pasangan (komoditas, provinsi).
MIN_HISTORY_DAYS = 180

MODEL_FILENAME_TEMPLATE = "prophet_{commodity}_{province}.json"
