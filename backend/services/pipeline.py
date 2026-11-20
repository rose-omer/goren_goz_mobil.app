"""Tek karenin analizi: derinlik + tespit + takip + uyarı. Senkron; thread havuzunda koşar."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from services.alert_service import AlertLevel, ObjectHazard, assess, build_message
from services.container import Services
from services.detection import Detection
from services.image_service import enhance_if_dark, proximity_to_jpeg_base64
from services.labels import REAL_HEIGHT_M
from services.proximity import RegionProximity, analyze_regions, box_proximity, label_for
from services.tracking import SessionState, TrackInfo

EDGE_MARGIN_PX = 2.0


@dataclass(frozen=True, slots=True)
class ObjectResult:
    detection: Detection
    track: TrackInfo
    distance_m: float | None
    proximity_label: str | None


@dataclass(frozen=True, slots=True)
class FrameResult:
    detector_ok: bool
    level: AlertLevel
    raw_level: AlertLevel
    message: str
    objects: list[ObjectResult]
    regions: dict[str, RegionProximity] | None
    depth_image_base64: str | None
    timings_ms: dict[str, float]


def size_distance(det: Detection, focal_px: float | None, image_height: int) -> float | None:
    """d = f_px · H_gerçek / h_px. Kutu kare kenarına değiyorsa nesne kesiktir; mesafe verme."""
    real = REAL_HEIGHT_M.get(det.name)
    if focal_px is None or real is None or det.height_px < 8:
        return None
    if det.bbox[1] <= EDGE_MARGIN_PX or det.bbox[3] >= image_height - EDGE_MARGIN_PX:
        return None
    return round(focal_px * real / det.height_px, 2)


def analyze_frame(
    services: Services,
    session: SessionState,
    image: np.ndarray,
    *,
    focal_px: float | None = None,
    include_depth_image: bool = False,
) -> FrameResult:
    settings = services.settings
    timings: dict[str, float] = {}
    work = enhance_if_dark(image)

    proximity: np.ndarray | None = None
    if services.depth is not None:
        t0 = time.perf_counter()
        inverse_depth = services.depth.estimate(work)
        timings["depth"] = (time.perf_counter() - t0) * 1000
    detections: list[Detection] = []
    detector_ok = services.detector is not None
    if services.detector is not None:
        t0 = time.perf_counter()
        detections = services.detector.detect(work)
        timings["detect"] = (time.perf_counter() - t0) * 1000

    with session.lock:
        regions = None
        if services.depth is not None:
            proximity = session.proximity.normalize(inverse_depth)
            if session.proximity.is_warm:
                regions = analyze_regions(proximity, settings.proximity_danger, settings.proximity_near)
        tracks = session.tracker.update(detections, time.monotonic())

        results: list[ObjectResult] = []
        hazards: list[ObjectHazard] = []
        for det, track in zip(detections, tracks, strict=True):
            distance = size_distance(det, focal_px, image.shape[0])
            label = None
            if proximity is not None and regions is not None:
                label = label_for(
                    box_proximity(proximity, det.bbox), settings.proximity_danger, settings.proximity_near
                )
            results.append(ObjectResult(det, track, distance, label))
            hazards.append(ObjectHazard(det.name_tr, det.region, det.priority, track.ttc_s, distance))

        raw = assess(hazards, regions, settings, detector_ok=detector_ok)
        stable = session.hysteresis.update(raw.level)

    message = build_message(stable, raw.top, regions, raw.depth_close, detector_ok=detector_ok)
    depth_b64 = None
    if include_depth_image and proximity is not None:
        depth_b64 = proximity_to_jpeg_base64(proximity)
    return FrameResult(detector_ok, stable, raw.level, message, results, regions, depth_b64, timings)
