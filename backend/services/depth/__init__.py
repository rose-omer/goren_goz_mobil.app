"""Göreli derinlik tahmincileri. Seçim `DEPTH_BACKEND` ayarından."""

from __future__ import annotations

from core.config import Settings
from services.depth.base import DepthEstimator


def build_depth_estimator(settings: Settings) -> DepthEstimator | None:
    """Ayardaki arka ucu kurar. `none` derinliği kapatır."""
    if settings.depth_backend == "none":
        return None
    if settings.depth_backend == "depth_anything":
        from services.depth.depth_anything import OpenVinoDepthAnything

        return OpenVinoDepthAnything(settings.depth_anything_xml, device=settings.openvino_device)
    from services.depth.openvino_midas import OpenVinoMidas

    return OpenVinoMidas(settings.midas_xml, device=settings.openvino_device)
