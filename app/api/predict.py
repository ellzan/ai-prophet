import logging

from fastapi import APIRouter, HTTPException, Query

from app.config import COMMODITIES, PROVINCES
from app.schemas.prediction import (
    CommoditiesResponse,
    HealthResponse,
    PredictionResponse,
    ProvincesResponse,
)
from app.services.data_provider import get_data_provider
from app.services.model_loader import get_model_loader
from app.services.prediction_service import get_prediction_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["prediction"])


@router.get("/commodities", response_model=CommoditiesResponse)
def list_commodities():
    """Daftar komoditas yang didukung — dipakai untuk mengisi dropdown UI."""
    return {"commodities": COMMODITIES}


@router.get("/provinces", response_model=ProvincesResponse)
def list_provinces():
    """Daftar provinsi yang didukung — dipakai untuk mengisi dropdown UI."""
    return {"provinces": PROVINCES}


@router.get("/predict", response_model=PredictionResponse)
def predict(
    commodity: str = Query(..., description="Nama komoditas, mis. 'Cabai Rawit'"),
    province: str = Query(..., description="Nama provinsi, mis. 'Jawa Timur'"),
):
    """Prediksi harga 14 hari ke depan untuk satu pasangan komoditas+provinsi.

    Mengembalikan kurva harian (bukan satu titik harga saja), lengkap dengan
    confidence interval dan insight tren otomatis.
    """
    if commodity not in COMMODITIES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "InvalidCommodity",
                "message": f"Komoditas '{commodity}' tidak didukung. Pilihan: {COMMODITIES}",
            },
        )
    if province not in PROVINCES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "InvalidProvince",
                "message": f"Provinsi '{province}' tidak didukung. Pilihan: {PROVINCES}",
            },
        )

    service = get_prediction_service()
    try:
        result = service.predict(commodity, province)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": "ModelNotFound", "message": str(exc)},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Prediction gagal untuk %s/%s", commodity, province)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "Terjadi kesalahan saat memprediksi."},
        ) from exc

    return result


health_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
def health():
    try:
        loader = get_model_loader()
        models_loaded = len(loader.loaded_pairs())
    except RuntimeError:
        models_loaded = None
    return {"status": "healthy", "service": "Pangan Pintar AI Service", "models_loaded": models_loaded}
