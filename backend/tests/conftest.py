"""Ortak fikstürler. Hiçbir test model indirmez ya da gerçek VLM'e bağlanmaz."""

from __future__ import annotations

import io

import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from core.config import Settings
from main import create_app
from services.container import Services, session_factory
from services.detection import Detection
from services.tracking import SessionStore
from services.vlm_service import VlmService

API_KEY = "test-anahtari"


class FakeDepth:
    name = "fake"

    def estimate(self, bgr: np.ndarray) -> np.ndarray:
        h, w = bgr.shape[:2]
        # Kare aşağı indikçe yakınlaşır (büyük ters derinlik = yakın).
        return np.tile(np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None], (1, w))


class FakeDetector:
    name = "fake"

    def __init__(self, detections: list[Detection] | None = None) -> None:
        self.detections = detections or []

    def detect(self, bgr: np.ndarray) -> list[Detection]:
        return list(self.detections)


def vlm_ok(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/health":
        return httpx.Response(200, json={"status": "ok"})
    return httpx.Response(
        200, json={"choices": [{"message": {"role": "assistant", "content": " Önünüzde bir kapı var. "}}]}
    )


def make_services(settings: Settings, detector, handler=vlm_ok) -> Services:
    client = httpx.AsyncClient(base_url="http://vlm.test", transport=httpx.MockTransport(handler))
    return Services(
        settings=settings,
        depth=FakeDepth(),
        detector=detector,
        vlm=VlmService(settings, client=client),
        sessions=SessionStore(session_factory(settings), settings.session_ttl_s, settings.max_sessions),
    )


def make_settings(**overrides) -> Settings:
    values = {
        "api_key": API_KEY,
        "debug": False,
        "rate_limit_per_minute": 0,
        "max_upload_bytes": 200_000,
        "max_image_pixels": 1_000_000,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def detector() -> FakeDetector:
    return FakeDetector([Detection("person", 0.9, (280.0, 100.0, 360.0, 400.0), "center")])


@pytest.fixture
def client(settings: Settings, detector: FakeDetector):
    app = create_app(settings, service_factory=lambda s: make_services(s, detector))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth() -> dict[str, str]:
    return {"X-API-Key": API_KEY, "X-Session-Id": "test-oturum"}


def jpeg_bytes(width: int = 640, height: int = 480) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), (120, 120, 120)).save(buf, format="JPEG", quality=80)
    return buf.getvalue()


@pytest.fixture
def jpeg() -> bytes:
    return jpeg_bytes()
