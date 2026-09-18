
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import COMMODITIES, PROVINCES  # noqa: E402
from app.services.data_provider import init_data_provider  # noqa: E402
from app.services.model_trainer import train_all  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Memuat data historis...")
    data_provider = init_data_provider()

    logger.info(
        "Mulai training untuk %d komoditas x %d provinsi (%d kombinasi)...",
        len(COMMODITIES), len(PROVINCES), len(COMMODITIES) * len(PROVINCES),
    )
    results = train_all(data_provider, COMMODITIES, PROVINCES)

    trained = sum(1 for r in results.values() if r.get("status") == "trained")
    failed = sum(1 for r in results.values() if r.get("status") == "failed")
    skipped = sum(1 for r in results.values() if r.get("status") == "skipped")

    print("\n=== RINGKASAN TRAINING ===")
    print(f"Berhasil : {trained}")
    print(f"Gagal    : {failed}")
    print(f"Dilewati : {skipped}")
    print("\nDetail MAPE per pasangan (semakin kecil semakin akurat):")
    for key, r in results.items():
        if r.get("status") == "trained":
            print(f"  {key:40s} MAPE={r.get('mape')}%")
    print("\nLihat artifacts/training_report.json untuk detail lengkap.")


if __name__ == "__main__":
    main()
