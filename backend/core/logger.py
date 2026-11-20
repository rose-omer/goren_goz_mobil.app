"""Log yapılandırması. Handler'ları bir kez ekler."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_configured = False


def setup_logging(log_level: str = "INFO", *, to_file: bool = True) -> None:
    """Kök logger'ı yapılandırır. İkinci çağrı yalnız seviyeyi günceller."""
    global _configured
    root = logging.getLogger()
    root.setLevel(log_level.upper())
    if _configured:
        return

    formatter = logging.Formatter(_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    if to_file:
        LOG_DIR.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_DIR / "backend.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # Erişim logu IP yazar; uyarı seviyesine çek.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    _configured = True
