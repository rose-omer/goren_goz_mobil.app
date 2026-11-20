"""Uygulama hata türleri ve tek hata zarfı: {"success": false, "error": {code, message}}."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """İstemciye sabit kodla dönen hata. Mesaj iç ayrıntı içermez."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def error_body(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}


def install_error_handlers(app: FastAPI) -> None:
    """Bütün hata yollarını tek zarfa bağlar."""

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message))

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limited(_: Request, __: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429, content=error_body("RATE_LIMITED", "Çok fazla istek. Biraz bekleyin.")
        )

    @app.exception_handler(RequestValidationError)
    async def _invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = ", ".join(".".join(str(p) for p in err["loc"]) for err in exc.errors())
        return JSONResponse(
            status_code=422, content=error_body("VALIDATION_ERROR", f"Geçersiz alan: {fields}")
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND"}.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else code
        return JSONResponse(status_code=exc.status_code, content=error_body(code, message))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Beklenmeyen hata", exc_info=exc)
        return JSONResponse(
            status_code=500, content=error_body("INTERNAL_ERROR", "Sunucu hatası. Tekrar deneyin.")
        )
