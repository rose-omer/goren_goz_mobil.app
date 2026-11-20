"""YOLO nesne tespiti. Model yolu ayardan gelir; dosya yoksa açık hata verir (plan G6)."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from services.labels import priority_of, turkish_name

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Detection:
    name: str
    confidence: float
    bbox: tuple[float, float, float, float]
    region: str

    @property
    def name_tr(self) -> str:
        return turkish_name(self.name)

    @property
    def priority(self) -> int:
        return priority_of(self.name)

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @property
    def height_px(self) -> float:
        return self.bbox[3] - self.bbox[1]


class Detector(Protocol):
    name: str

    def detect(self, bgr: np.ndarray) -> list[Detection]: ...


def region_of(center_x: float, width: int) -> str:
    if center_x < width / 3:
        return "left"
    if center_x < 2 * width / 3:
        return "center"
    return "right"


def rank(detections: list[Detection], limit: int) -> list[Detection]:
    """Önce öncelik, sonra güven; en fazla `limit` nesne."""
    ordered = sorted(detections, key=lambda d: (d.priority, d.confidence), reverse=True)
    return ordered[:limit]


class YoloDetector:
    def __init__(self, model_path: Path, confidence: float, max_objects: int) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"YOLO ağırlığı yok: {model_path}")
        from ultralytics import YOLO  # ağır içe aktarım; yalnız gerçek kullanımda

        self._model = YOLO(str(model_path))
        self._confidence = confidence
        self._max_objects = max_objects
        self._lock = threading.Lock()
        self.name = model_path.stem
        logger.info("YOLO hazır: %s", self.name)

    def detect(self, bgr: np.ndarray) -> list[Detection]:
        with self._lock:
            results = self._model(bgr, verbose=False, conf=self._confidence)
        if not results:
            return []
        width = bgr.shape[1]
        names = self._model.names
        found: list[Detection] = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
            name = names[int(box.cls[0])]
            found.append(
                Detection(
                    name, round(float(box.conf[0]), 3), (x1, y1, x2, y2), region_of((x1 + x2) / 2, width)
                )
            )
        return rank(found, self._max_objects)
