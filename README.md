# Pangan Pintar — AI Service

Layanan prediksi harga komoditas pangan **14 hari ke depan** menggunakan
[Prophet](https://facebook.github.io/prophet/), dibangun sendiri oleh Tim
WUKWUK untuk APTIKOM Hackathon 2026 (menggantikan API pihak lain yang
sebelumnya dipakai sementara).

## Fitur

- Prediksi harga harian untuk 14 hari ke depan (bukan cuma 1 titik/minggu)
- Confidence interval (batas atas/bawah) di setiap titik prediksi
- Insight tren otomatis dalam bahasa Indonesia
- Model terpisah per pasangan (komoditas, provinsi) — akurasi lebih baik
  daripada satu model besar untuk semua data
- Sudah memperhitungkan efek Lebaran/Idul Adha lewat custom holidays Prophet

## Struktur Proyek

```
ai-service/
├── app/
│   ├── config.py                 # daftar komoditas, provinsi, path artefak
│   ├── api/predict.py            # endpoint FastAPI
│   ├── schemas/prediction.py     # skema request/response (Pydantic)
│   └── services/
│       ├── data_provider.py      # akses data historis
│       ├── model_trainer.py      # training Prophet + evaluasi MAPE
│       ├── model_loader.py       # load model terlatih untuk inferensi
│       └── prediction_service.py # orkestrasi -> hasil 14 hari + insight
├── data/harga_historis.csv       # data historis (GANTI dengan data asli!)
├── artifacts/                    # model terlatih (.json) + training_report.json
├── scripts/
│   ├── generate_sample_data.py   # generator data SAMPLE untuk development
│   └── train.py                  # jalankan ini untuk melatih model
├── main.py                       # entry point FastAPI
├── requirements.txt
└── Dockerfile
```

## Menjalankan Secara Lokal

```bash
pip install -r requirements.txt

# 1. Siapkan data. Untuk development, generate data sampel dulu:
python scripts/generate_sample_data.py

# 2. Latih model (wajib sebelum menjalankan API)
python scripts/train.py

# 3. Jalankan API
uvicorn main:app --reload --port 8000
```

Dokumentasi interaktif otomatis tersedia di `http://localhost:8000/docs`.

## ⚠️ WAJIB Sebelum Demo Final: Ganti ke Data Asli

`data/harga_historis.csv` yang ada sekarang adalah **data sintetis/sampel**,
dibuat oleh `scripts/generate_sample_data.py` supaya pipeline bisa diuji
end-to-end sejak awal. **Ini bukan data asli** dan tidak boleh dipakai untuk
demo final ke juri.

Sebelum demo, ganti isi CSV tersebut dengan data historis asli dari:

- **Panel Harga Pangan Bapanas**: https://panelharga.badanpangan.go.id
- **PIHPS Nasional (Bank Indonesia)**: https://www.bi.go.id/hargapangan

Format kolom yang dibutuhkan (header wajib persis seperti ini):

```csv
date,commodity,province,price
2024-01-01,Cabai Rawit,Jawa Timur,52000
2024-01-02,Cabai Rawit,Jawa Timur,53200
...
```

Setelah data asli siap, jalankan ulang `python scripts/train.py` untuk
melatih ulang semua model dari data yang baru.

## Menambah Komoditas / Provinsi

Edit `app/config.py`, tambahkan nama komoditas/provinsi baru ke list
`COMMODITIES` / `PROVINCES`, pastikan datanya juga ada di CSV, lalu jalankan
ulang `scripts/train.py`.

## Endpoint

| Method | Path | Deskripsi |
|---|---|---|
| GET | `/` | Info dasar service |
| GET | `/health` | Health check, termasuk jumlah model yang berhasil dimuat |
| GET | `/api/v1/commodities` | Daftar komoditas yang didukung |
| GET | `/api/v1/provinces` | Daftar provinsi yang didukung |
| GET | `/api/v1/predict?commodity=...&province=...` | Prediksi 14 hari ke depan |

Contoh:

```bash
curl "http://localhost:8000/api/v1/predict?commodity=Cabai%20Rawit&province=Jawa%20Timur"
```

## Deploy ke Railway / Render

1. Push folder ini ke repository GitHub tersendiri (atau sebagai folder
   `ai-service/` di monorepo utama).
2. Buat service baru di Railway/Render, pilih "Deploy from Dockerfile".
3. Set port ke `8000` (sudah di-`EXPOSE` di Dockerfile).
4. Setelah data asli tersedia, commit perubahan `data/harga_historis.csv`
   sebelum deploy — `Dockerfile` akan otomatis melatih ulang model saat
   image dibangun (`RUN python scripts/train.py`).
5. Update `allow_origins` di `main.py` dengan domain frontend production
   (Vercel) kalian sebelum deploy final, supaya CORS tidak diblokir browser.

## Retraining Berkala

Untuk menjaga model tetap relevan, jadwalkan `scripts/train.py` berjalan
otomatis (misalnya lewat cron job mingguan di backend Node.js kalian yang
memanggil ulang proses training, atau scheduled job di platform hosting)
setiap kali ada data harga baru masuk ke `data/harga_historis.csv`.

## Evaluasi Akurasi

Setiap kali `scripts/train.py` dijalankan, akurasi tiap model (MAPE / Mean
Absolute Percentage Error, dihitung dari 30 hari terakhir sebagai holdout)
tersimpan di `artifacts/training_report.json`. Gunakan angka ini untuk slide
presentasi ("model kami mencapai MAPE X% untuk komoditas Y").
