"""`/api/analyze` ve `/health` uç testleri (sahte servislerle)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import create_app
from tests.conftest import FakeDetector, jpeg_bytes, make_services, make_settings


def post_frame(client, headers, data=None, image=None):
    files = {"image": ("kare.jpg", image or jpeg_bytes(), "image/jpeg")}
    return client.post("/api/analyze", headers=headers, files=files, data=data or {})


def test_schema_contains_distance_and_ttc(client, auth):
    response = post_frame(client, auth, data={"focal_px": "500"})
    assert response.status_code == 200
    body = response.json()
    obj = body["data"]["objects"][0]
    assert {"distance_m", "ttc_s", "track_id", "name_tr"} <= obj.keys()
    # 500 px odak, 1.70 m insan, 300 px kutu → 2.83 m.
    assert obj["distance_m"] == 2.83
    assert obj["name_tr"] == "insan"
    assert body["data"]["alert_level"] in {"CLEAR", "INFO", "NEAR", "DANGER"}


def test_distance_is_null_without_focal_length(client, auth):
    obj = post_frame(client, auth).json()["data"]["objects"][0]
    assert obj["distance_m"] is None


def test_missing_api_key_returns_401(client):
    response = post_frame(client, {})
    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "error": {"code": "UNAUTHORIZED", "message": "Geçersiz ya da eksik API anahtarı."},
    }


def test_wrong_api_key_returns_401(client):
    assert post_frame(client, {"X-API-Key": "yanlis"}).status_code == 401


def test_oversized_upload_returns_413(client, auth):
    big = b"\xff" * 250_000
    response = post_frame(client, auth, image=big)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "IMAGE_TOO_LARGE"


def test_pixel_limit_returns_413(client, auth):
    response = post_frame(client, auth, image=jpeg_bytes(1600, 1200))
    assert response.status_code == 413


def test_invalid_image_returns_400(client, auth):
    response = post_frame(client, auth, image=b"jpeg degil")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_IMAGE"


def test_regions_appear_after_warmup(client, auth):
    bodies = [post_frame(client, auth).json()["data"] for _ in range(10)]
    assert bodies[0]["regions"] is None
    assert set(bodies[-1]["regions"]) == {"left", "center", "right"}


def test_sessions_are_isolated(client, auth):
    first = post_frame(client, auth).json()["data"]["objects"][0]["track_id"]
    other = post_frame(client, {**auth, "X-Session-Id": "baska"}).json()["data"]["objects"][0]["track_id"]
    again = post_frame(client, auth).json()["data"]["objects"][0]["track_id"]
    assert first == again
    assert client.get("/health").json()["active_sessions"] == 2
    assert other  # ikinci oturum kendi izini açar


def test_health_reports_state_without_loading(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["depth_loaded"] and body["detector_loaded"]
    assert body["vlm_ready"] is True
    assert body["vlm_model"]


def test_no_models_returns_503(auth):
    settings = make_settings()

    def factory(s):
        services = make_services(s, FakeDetector())
        services.depth = None
        services.detector = None
        return services

    with TestClient(create_app(settings, service_factory=factory)) as c:
        response = post_frame(c, auth)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODELS_UNAVAILABLE"


def test_depth_only_server_never_says_clear_path(auth):
    """Detector yüklenemezse sunucu derinlikle çalışır ama "Yol açık" demez."""
    settings = make_settings()

    def factory(s):
        services = make_services(s, FakeDetector())
        services.detector = None
        return services

    with TestClient(create_app(settings, service_factory=factory)) as c:
        bodies = [post_frame(c, auth).json()["data"] for _ in range(12)]
    assert bodies[-1]["regions"] is not None
    assert all(b["detector_ok"] is False for b in bodies)
    assert all(b["message"] != "Yol açık." for b in bodies)


def test_detector_ok_is_true_with_detector(client, auth):
    assert post_frame(client, auth).json()["data"]["detector_ok"] is True


def test_session_store_is_bounded(auth):
    """Her istekte yeni X-Session-Id: sözlük sınırı aşmaz."""
    settings = make_settings(max_sessions=3)
    with TestClient(create_app(settings, service_factory=lambda s: make_services(s, FakeDetector()))) as c:
        for i in range(6):
            assert post_frame(c, {**auth, "X-Session-Id": f"oturum-{i}"}).status_code == 200
        assert c.get("/health").json()["active_sessions"] == 3


def test_rate_limit_ignores_session_id(auth):
    """Anahtarsız istemci oturum kimliğini değiştirerek sınırı atlayamaz."""
    settings = make_settings(api_key="", debug=True, rate_limit_per_minute=2)
    app = create_app(settings, service_factory=lambda s: make_services(s, FakeDetector()))
    with TestClient(app) as c:
        codes = [post_frame(c, {"X-Session-Id": f"s-{i}"}).status_code for i in range(3)]
    app.state.limiter.reset()
    assert codes == [200, 200, 429]


def test_missing_key_config_rejects_in_production(auth):
    settings = make_settings(api_key="", debug=False)
    with TestClient(create_app(settings, service_factory=lambda s: make_services(s, FakeDetector()))) as c:
        response = post_frame(c, {})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "API_KEY_NOT_CONFIGURED"


def test_rate_limit_returns_429(auth):
    settings = make_settings(rate_limit_per_minute=2)
    app = create_app(settings, service_factory=lambda s: make_services(s, FakeDetector()))
    with TestClient(app) as c:
        codes = [post_frame(c, {**auth, "X-API-Key": settings.api_key}).status_code for _ in range(3)]
    # Diğer testler sınırı kapatır; sayaç bu uygulamaya özgü değil, sıfırla.
    app.state.limiter.reset()
    assert codes[:2] == [200, 200]
    assert codes[2] == 429
