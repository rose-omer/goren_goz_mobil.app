"""Gören Göz backend: isteğe bağlı sunucu analizi ve Türkçe VLM sorusu.

Çalıştırma (bu makinede 8000 yasak; 8110 kullan):
    uvicorn main:app --host 127.0.0.1 --port 8110
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.config import Settings, get_settings
from core.errors import install_error_handlers
from core.limiter import configure_limiter, limiter
from core.logger import setup_logging
from models.response import HealthResponse
from routers import analyze, assistant, debug
from services.container import Services, build_services

VERSION = "2.0.0"
logger = logging.getLogger(__name__)

ServiceFactory = Callable[[Settings], Services]


def create_app(settings: Settings | None = None, service_factory: ServiceFactory = build_services) -> FastAPI:
    """Uygulama fabrikası. Testler sahte `service_factory` verir; model yüklenmez."""
    settings = settings or get_settings()
    configure_limiter(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        services = service_factory(settings)
        app.state.services = services
        await services.vlm.check_ready()
        logger.info(
            "Hazır: derinlik=%s tespit=%s vlm=%s debug=%s",
            services.depth is not None,
            services.detector is not None,
            services.vlm.last_ready,
            settings.debug,
        )
        if not settings.api_key:
            logger.warning("API_KEY tanımlı değil. Yalnız DEBUG=true iken istek kabul edilir.")
        yield
        await services.vlm.aclose()

    app = FastAPI(
        title="Gören Göz API",
        version=VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.debug else None,
    )
    app.state.settings = settings
    app.state.limiter = limiter
    install_error_handlers(app)

    if settings.cors_origins:
        # Mobil istemci CORS'a ihtiyaç duymaz; liste yalnız tarayıcıdaki debug sayfası için.
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["X-API-Key", "X-Session-Id", "Content-Type"],
        )

    @app.middleware("http")
    async def timing_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - start) * 1000:.1f}"
        return response

    app.include_router(analyze.router, prefix="/api", tags=["Analiz"])
    app.include_router(assistant.router, prefix="/api", tags=["Soru"])
    if settings.debug:
        app.include_router(debug.router)

    @app.get("/health", response_model=HealthResponse, tags=["Sağlık"])
    async def health(request: Request) -> HealthResponse:
        """Yalnız durum okur; model yüklemez, VLM'e bağlanmaz (plan E7)."""
        services: Services = request.app.state.services
        loaded = services.depth is not None or services.detector is not None
        return HealthResponse(
            status="ok" if loaded else "degraded",
            version=VERSION,
            depth_loaded=services.depth is not None,
            detector_loaded=services.detector is not None,
            vlm_ready=services.vlm.last_ready,
            vlm_model=services.vlm.model,
            active_sessions=len(services.sessions),
        )

    return app


def _build_default_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    return create_app(settings)


app = _build_default_app()


if __name__ == "__main__":
    import uvicorn

    s = get_settings()
    uvicorn.run("main:app", host=s.host, port=s.port, log_level=s.log_level.lower())
