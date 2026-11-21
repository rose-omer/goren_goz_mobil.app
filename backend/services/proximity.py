"""Göreli derinliği kayan pencereyle 0–1 yakınlığa çevirir.

MiDaS metre vermez. Kare başı min-max her karede en yakın pikseli "çok yakın" yapar (plan D1).
Bu modül son N karenin yüzdelikleriyle ölçekler ve yalnız sıralama/etiket üretir.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

REGIONS = ("left", "center", "right")


@dataclass(frozen=True, slots=True)
class RegionProximity:
    proximity: float  # 0 uzak, 1 yakın (pencereye göre)
    close_area: float  # "çok yakın" piksel oranı
    label: str  # "çok yakın" | "yakın" | "uzak"


class ProximityNormalizer:
    """Oturum başına bir örnek. Isınmadan (warmup) önce etiket vermez."""

    def __init__(self, window: int = 30, warmup: int = 10) -> None:
        self._lows: deque[float] = deque(maxlen=window)
        self._highs: deque[float] = deque(maxlen=window)
        self.warmup = warmup

    @property
    def is_warm(self) -> bool:
        return len(self._lows) >= self.warmup

    def normalize(self, inverse_depth: np.ndarray) -> np.ndarray:
        valid = inverse_depth[np.isfinite(inverse_depth)]
        if valid.size == 0:
            return np.zeros_like(inverse_depth, dtype=np.float32)
        low, high = np.percentile(valid, (5, 95))
        self._lows.append(float(low))
        self._highs.append(float(high))
        lo, hi = min(self._lows), max(self._highs)
        if hi - lo < 1e-6:
            return np.zeros_like(inverse_depth, dtype=np.float32)
        return np.clip((inverse_depth - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def label_for(proximity: float, danger: float, near: float) -> str:
    if proximity >= danger:
        return "çok yakın"
    if proximity >= near:
        return "yakın"
    return "uzak"


def analyze_regions(proximity: np.ndarray, danger: float, near: float) -> dict[str, RegionProximity]:
    """Kareyi sol/orta/sağ üç dikey banda böler. Alt %70'e bakar (zemin ve gövde hizası)."""
    height, width = proximity.shape
    body = proximity[int(height * 0.3) :, :]
    thirds = np.array_split(body, 3, axis=1)
    result: dict[str, RegionProximity] = {}
    for name, band in zip(REGIONS, thirds, strict=True):
        score = float(np.percentile(band, 90)) if band.size else 0.0
        close_area = float(np.mean(band >= danger)) if band.size else 0.0
        result[name] = RegionProximity(score, close_area, label_for(score, danger, near))
    return result


def box_proximity(proximity: np.ndarray, bbox: tuple[float, float, float, float]) -> float:
    """Kutunun iç %50'sinde yakınlığın 80. yüzdeliği (plan D6).

    Ters derinlikte büyük = yakın; bu, metrik derinliğin 20. yüzdeliğine denk gelir.
    """
    x1, y1, x2, y2 = bbox
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    half_w, half_h = (x2 - x1) / 4, (y2 - y1) / 4
    h, w = proximity.shape
    xa, xb = int(max(0, cx - half_w)), int(min(w, cx + half_w + 1))
    ya, yb = int(max(0, cy - half_h)), int(min(h, cy + half_h + 1))
    patch = proximity[ya:yb, xa:xb]
    return float(np.percentile(patch, 80)) if patch.size else 0.0
