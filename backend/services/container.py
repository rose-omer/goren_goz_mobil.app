"""Servis kabı: lifespan'da bir kez kurulur, `app.state.services` üzerinde durur."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from core.config import Settings
from services.alert_service import LevelHysteresis
from services.depth import DepthEstimator, build_depth_estimator
from services.detection import Detector, YoloDetector
from services.proximity import ProximityNormalizer
from services.tracking import SessionState, SessionStore, Tracker
from services.vlm_service import VlmService

logger = logging.getLogger(__name__)


@dataclass
class Services:
    settings: Settings
    depth: DepthEstimator | None
    detector: Detector | None
    vlm: VlmService
    sessions: SessionStore
    load_errors: dict[str, str] = field(default_factory=dict)


def session_factory(settings: Settings):
    def make() -> SessionState:
        return SessionState(
            tracker=Tracker(),
            proximity=ProximityNormalizer(),
            hysteresis=LevelHysteresis(settings.raise_after_frames, settings.lower_after_frames),
        )

    return make


def build_services(settings: Settings) -> Services:
    """Gerçek modelleri yükler. Yüklenemeyen model `None` kalır; hata kodu saklanır."""
    errors: dict[str, str] = {}
    depth: DepthEstimator | None = None
    detector: Detector | None = None
    try:
        depth = build_depth_estimator(settings)
    except Exception as exc:  # model yoksa sunucu yine açılır; /health durumu gösterir
        logger.error("Derinlik modeli yüklenemedi: %s", exc)
        errors["depth"] = type(exc).__name__
    try:
        detector = YoloDetector(settings.yolo_path, settings.detection_confidence, settings.max_objects)
    except Exception as exc:
        logger.error("YOLO yüklenemedi: %s", exc)
        errors["detector"] = type(exc).__name__
    return Services(
        settings=settings,
        depth=depth,
        detector=detector,
        vlm=VlmService(settings),
        sessions=SessionStore(session_factory(settings), settings.session_ttl_s, settings.max_sessions),
        load_errors=errors,
    )
