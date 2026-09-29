"""Entry point Pangan Pintar AI Service (FastAPI + Prophet).

Jalankan lokal:
    uvicorn main:app --reload --port 8000

Dokumentasi interaktif otomatis tersedia di /docs setelah service jalan.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.predict import health_router, router as predict_router
from app.config import COMMODITIES, PROVINCES
from app.services.data_provider import init_data_provider
from app.services.model_loader import init_model_loader
from app.services.prediction_service import init_prediction_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pangan Pintar AI Service",
    description="Prediksi harga komoditas pangan 14 hari ke depan menggunakan Prophet.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(health_router)


@app.on_event("startup")
def on_startup():
    logger.info("Memulai Pangan Pintar AI Service...")
    data_provider = init_data_provider()
    model_loader = init_model_loader(COMMODITIES, PROVINCES)
    init_prediction_service(model_loader=model_loader, data_provider=data_provider)
    logger.info("Service siap menerima request.")


@app.get("/")
def root():
    return {
        "message": "Welcome to Pangan Pintar AI Service",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
