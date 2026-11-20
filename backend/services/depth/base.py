"""Derinlik arayüzü ve ortak ön işleme."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import cv2
import numpy as np

# MiDaS small_transform: ImageNet ortalama/std ile normalize, 256 px girdi.
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class DepthEstimator(Protocol):
    """Göreli ters derinlik üretir: büyük değer = yakın. Birim metre değildir."""

    name: str

    def estimate(self, bgr: np.ndarray) -> np.ndarray:
        """Girdi boyutunda float32 göreli ters derinlik döner."""
        ...


@dataclass(frozen=True, slots=True)
class Letterbox:
    """Kare girdide görüntünün kapladığı alan (piksel, `size` ölçeğinde)."""

    top: int
    left: int
    height: int
    width: int
    size: int


def preprocess_midas(bgr: np.ndarray, size: int = 256) -> tuple[np.ndarray, Letterbox]:
    """BGR kareyi MiDaS girdisine çevirir: NCHW, float32, ImageNet normu.

    En-boy oranı korunur: uzun kenar `size` olur, kalan alan ImageNet ortalamasıyla
    (normalize sonrası 0) doldurulur. IR modelin sabit 256x256 girdisi değişmez.
    Bütün arka uçlar bu tek fonksiyonu kullanır (plan D3).
    """
    height, width = bgr.shape[:2]
    scale = size / max(height, width)
    new_h = max(1, min(size, round(height * scale)))
    new_w = max(1, min(size, round(width * scale)))
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    normalized = (resized.astype(np.float32) / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
    box = Letterbox((size - new_h) // 2, (size - new_w) // 2, new_h, new_w, size)
    canvas = np.zeros((size, size, 3), dtype=np.float32)
    canvas[box.top : box.top + new_h, box.left : box.left + new_w] = normalized
    return np.ascontiguousarray(canvas.transpose(2, 0, 1)[np.newaxis, ...]), box


def crop_letterbox(prediction: np.ndarray, box: Letterbox) -> np.ndarray:
    """Model çıktısından dolgu alanını atar. Çıktı boyutu girdiden farklıysa orantılar."""
    sy = prediction.shape[0] / box.size
    sx = prediction.shape[1] / box.size
    top, left = round(box.top * sy), round(box.left * sx)
    bottom = max(top + 1, round((box.top + box.height) * sy))
    right = max(left + 1, round((box.left + box.width) * sx))
    return prediction[top:bottom, left:right]
