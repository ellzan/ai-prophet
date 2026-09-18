"""Memuat model Prophet yang sudah dilatih (artefak .json) untuk inferensi.

Terpisah dari model_trainer.py karena proses training (berat, jarang
dijalankan) dan proses loading-untuk-serving (ringan, dijalankan tiap
startup API) punya siklus hidup yang berbeda.
"""

import logging
import os
from typing import Dict, Optional, Tuple

from prophet import Prophet
from prophet.serialize import model_from_json

from app.config import ARTIFACTS_DIR, MODEL_FILENAME_TEMPLATE

logger = logging.getLogger(__name__)


class ModelLoader:
    """Registry in-memory untuk semua model Prophet yang sudah dilatih."""

    def __init__(self, artifacts_dir: str = ARTIFACTS_DIR) -> None:
        self.artifacts_dir = artifacts_dir
        self._models: Dict[Tuple[str, str], Prophet] = {}

    def load_all(self, commodities: list, provinces: list) -> None:
        """Coba muat semua kombinasi; lewati yang artefaknya belum ada
        (misalnya karena datanya belum cukup saat training)."""
        loaded, missing = 0, 0
        for commodity in commodities:
            for province in provinces:
                path = self._path_for(commodity, province)
                if not os.path.exists(path):
                    missing += 1
                    continue
                with open(path, "r") as f:
                    model = model_from_json(f.read())
                self._models[(commodity, province)] = model
                loaded += 1
        logger.info("ModelLoader: %d model dimuat, %d belum tersedia", loaded, missing)

    def _path_for(self, commodity: str, province: str) -> str:
        safe_commodity = commodity.lower().replace(" ", "_")
        safe_province = province.lower().replace(" ", "_")
        filename = MODEL_FILENAME_TEMPLATE.format(commodity=safe_commodity, province=safe_province)
        return os.path.join(self.artifacts_dir, filename)

    def get_model(self, commodity: str, province: str) -> Prophet:
        model = self._models.get((commodity, province))
        if model is None:
            raise KeyError(
                f"Model untuk komoditas='{commodity}', provinsi='{province}' "
                f"belum dilatih. Jalankan scripts/train.py terlebih dulu."
            )
        return model

    def is_available(self, commodity: str, province: str) -> bool:
        return (commodity, province) in self._models

    def loaded_pairs(self) -> list:
        return [{"commodity": c, "province": p} for c, p in self._models.keys()]


_model_loader: Optional[ModelLoader] = None


def init_model_loader(commodities: list, provinces: list) -> ModelLoader:
    global _model_loader
    _model_loader = ModelLoader()
    _model_loader.load_all(commodities, provinces)
    return _model_loader


def get_model_loader() -> ModelLoader:
    if _model_loader is None:
        raise RuntimeError("ModelLoader belum diinisialisasi. Panggil init_model_loader().")
    return _model_loader
