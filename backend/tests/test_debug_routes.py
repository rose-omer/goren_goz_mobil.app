"""Debug uçları yalnız `DEBUG=true` iken var olmalı (plan G1, G2, G10)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import create_app
from tests.conftest import FakeDetector, jpeg_bytes, make_services, make_settings

DEBUG_PATHS = [
    "/api/stream/video_feed",
    "/api/stream/depth_feed",
    "/monitor",
    "/api/ask_context_history",
    "/docs",
]


@pytest.mark.parametrize("path", DEBUG_PATHS)
def test_debug_routes_absent_in_production(client, path):
    assert client.get(path).status_code == 404


def test_debug_mode_serves_monitor_and_text_only_history(auth):
    settings = make_settings(debug=True)
    with TestClient(create_app(settings, service_factory=lambda s: make_services(s, FakeDetector()))) as c:
        assert c.get("/monitor").status_code == 200
        c.post(
            "/api/ask_context",
            headers=auth,
            files={"image": ("kare.jpg", jpeg_bytes(), "image/jpeg")},
            data={"question": "Önümde ne var?"},
        )
        history = c.get("/api/ask_context_history").json()["history"]
    assert history, "debug modunda geçmiş dolmalı"
    assert "image_base64" not in history[-1]
    assert set(history[-1]) == {"timestamp", "question", "answer", "processing_time_ms"}
    assert history[-1]["question"] == "Önümde ne var?"


def test_debug_history_masks_free_text_question(auth):
    settings = make_settings(debug=True)
    with TestClient(create_app(settings, service_factory=lambda s: make_services(s, FakeDetector()))) as c:
        c.post(
            "/api/ask_context",
            headers=auth,
            files={"image": ("kare.jpg", jpeg_bytes(), "image/jpeg")},
            data={"question": "Adım Ayşe, ilacım nerede?"},
        )
        history = c.get("/api/ask_context_history").json()["history"]
    assert history[-1]["question"] == "[serbest soru, 25 karakter]"
