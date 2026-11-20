"""VLM isteği: `httpx.MockTransport` ile gövde ve hata yolları (gerçek çağrı yok)."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from main import create_app
from services.vlm_service import VlmService, VlmUnavailableError
from tests.conftest import FakeDetector, jpeg_bytes, make_services, make_settings


def run(coro):
    return asyncio.run(coro)


def service_with(handler, **settings_overrides) -> VlmService:
    settings = make_settings(**settings_overrides)
    client = httpx.AsyncClient(base_url="http://vlm.test", transport=httpx.MockTransport(handler))
    return VlmService(settings, client=client)


def test_request_uses_chat_completions_with_image_url():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "Önde bir masa var."}}]})

    settings = make_settings(vlm_model="Qwen3.5-0.8B", vlm_api_key="gizli")
    client = httpx.AsyncClient(
        base_url="http://vlm.test",
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer gizli"},
    )
    answer = run(VlmService(settings, client=client).ask(jpeg_bytes(), "Önümde ne var?", "masa önde"))

    assert seen["path"] == "/v1/chat/completions"
    body = seen["body"]
    assert body["model"] == "Qwen3.5-0.8B"
    assert body["max_tokens"] == 48
    user_content = body["messages"][1]["content"]
    image_part = next(p for p in user_content if p["type"] == "image_url")
    assert image_part["image_url"]["url"].startswith("data:image/jpeg;base64,")
    text_part = next(p for p in user_content if p["type"] == "text")
    assert "Önümde ne var?" in text_part["text"]
    assert "Türkçe" in body["messages"][0]["content"]
    assert answer.answer == "Önde bir masa var."


def test_default_model_comes_from_settings():
    assert make_settings().vlm_model == "SmolVLM2-500M-Video-Instruct"


def test_retries_once_then_fails():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ConnectTimeout("zaman aşımı", request=request)

    with pytest.raises(VlmUnavailableError):
        run(service_with(handler).ask(jpeg_bytes(), "Soru?", ""))
    assert calls["n"] == 2


def test_client_error_is_not_retried():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401, json={"error": "anahtar"})

    with pytest.raises(VlmUnavailableError):
        run(service_with(handler).ask(jpeg_bytes(), "Soru?", ""))
    assert calls["n"] == 1


def test_endpoint_returns_turkish_503_when_vlm_down(auth):
    def down(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    settings = make_settings()
    app = create_app(settings, service_factory=lambda s: make_services(s, FakeDetector(), handler=down))
    with TestClient(app) as c:
        response = c.post(
            "/api/ask_context",
            headers=auth,
            files={"image": ("kare.jpg", jpeg_bytes(), "image/jpeg")},
            data={"question": "Önümde ne var?"},
        )
    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "VLM_UNAVAILABLE",
        "message": "Soru sorma şu an kullanılamıyor.",
    }


def test_endpoint_answers_and_preset_questions_are_turkish(client, auth):
    response = client.post(
        "/api/ask_context",
        headers=auth,
        files={"image": ("kare.jpg", jpeg_bytes(), "image/jpeg")},
        data={"question": "Önümde ne var?"},
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "Önünüzde bir kapı var."
    assert response.json()["detections_count"] == 1

    presets = client.get("/api/preset_questions", headers=auth).json()["preset_questions"]
    assert "Önümde ne var?" in presets.values()
    assert all("güvenli mi" not in q for q in presets.values())
