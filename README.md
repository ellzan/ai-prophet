# Pangan Pintar — AI Service

Layanan prediksi harga komoditas pangan **14 hari ke depan** menggunakan
[Prophet](https://facebook.github.io/prophet/), dibangun oleh Tim
WUKWUK untuk APTIKOM Hackathon 2026

## Fitur

- Prediksi harga harian untuk 14 hari ke depan 
- Confidence interval di setiap titik prediksi
- Insight tren otomatis dalam bahasa Indonesia
- Model terpisah per pasangan (komoditas, provinsi) 
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

.venv\Scripts\Activate.ps1

pip install -r requirements.txt

# 1. Siapkan data. Untuk development, generate data sampel dulu:
python scripts/generate_sample_data.py

# 2. Latih model 
python scripts/train.py

# 3. Jalankan API
uvicorn main:app --reload --port 8000
```

Dokumentasi interaktif otomatis tersedia di `http://localhost:8000/docs`.


`data/harga_historis.csv` yang ada sekarang adalah **data sintetis/sampel**,
dibuat oleh `scripts/generate_sample_data.py` supaya pipeline bisa diuji
end-to-end sejak awal.


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


Buka PowerShell di folder `d:\ai-service`, lalu jalankan:

```powershell
git init
git branch -M main
git status
```


Ganti `USERNAME` dan `NAMA-REPOSITORY` sesuai akun GitHub Anda:

```powershell
git add .
git status
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/NAMA-REPOSITORY.git
git push -u origin main
```

Jika GitHub meminta autentikasi melalui HTTPS, gunakan Personal Access Token
sebagai pengganti password akun GitHub. Alternatifnya, gunakan URL SSH:

```powershell
git remote set-url origin git@github.com:USERNAME/NAMA-REPOSITORY.git
git push -u origin main
```

### Push perubahan berikutnya

Setelah mengubah kode atau dokumentasi, jalankan:

```powershell
git status
git add .
git commit -m "Jelaskan perubahan secara singkat"
git push
```

Untuk bekerja dengan branch fitur:

```powershell
git switch -c nama-fitur
# lakukan perubahan, lalu commit
git push -u origin nama-fitur
```

Setelah itu, buat Pull Request di GitHub menuju branch `main`.


## Retraining Berkala

Untuk menjaga model tetap relevan, jadwalkan `scripts/train.py` berjalan
otomatis
setiap kali ada data harga baru masuk ke `data/harga_historis.csv`.
