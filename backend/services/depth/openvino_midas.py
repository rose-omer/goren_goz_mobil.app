"""MiDaS_small OpenVINO IR arka ucu. Model dosyası önceden indirilmiş olmalı."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import cv2
import numpy as np

from services.depth.base import crop_letterbox, preprocess_midas

logger = logging.getLogger(__name__)


class ModelFileMissingError(FileNotFoundError):
    """Model dosyası yok. `scripts/download_models.py` ile indir."""


class OpenVinoMidas:
    """Göreli ters derinlik veren OpenVINO IR modeli. Girdi kenarı IR'nin sabit şeklinden okunur."""

    name = "openvino_midas"
    default_input_size = 256

    def __init__(self, xml_path: Path, device: str = "AUTO") -> None:
        if not xml_path.exists() or not xml_path.with_suffix(".bin").exists():
            raise ModelFileMissingError(f"{self.name} IR yok: {xml_path}")
        import openvino as ov  # ağır içe aktarım; yalnız gerçek kullanımda

        core = ov.Core()
        self._compiled = core.compile_model(core.read_model(str(xml_path)), device)
        self._request = self._compiled.create_infer_request()
        self._output = self._compiled.output(0)
        self._input_size = self._static_input_size()
        # Tek InferRequest eşzamanlı çağrıda güvenli değil (plan E2).
        self._lock = threading.Lock()
        logger.info("%s OpenVINO hazır (%s, girdi %d px)", self.name, device, self._input_size)

    def _static_input_size(self) -> int:
        """IR girdisi [1, 3, H, W] ve sabitse H; dinamikse sınıf varsayılanı."""
        try:
            return int(self._compiled.input(0).shape[2])
        except (RuntimeError, TypeError, IndexError):
            return self.default_input_size

    def estimate(self, bgr: np.ndarray) -> np.ndarray:
        tensor, box = preprocess_midas(bgr, self._input_size)
        with self._lock:
            result = self._request.infer({0: tensor})[self._output]
        prediction = crop_letterbox(np.asarray(result, dtype=np.float32).squeeze(), box)
        height, width = bgr.shape[:2]
        return cv2.resize(prediction, (width, height), interpolation=cv2.INTER_LINEAR)
