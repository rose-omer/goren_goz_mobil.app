"""`X-API-Key` doğrulaması ve yalnız-yerel bağımlılığı."""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, Header, Request

from core.config import Settings
from core.errors import AppError

LOCAL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", "testclient"})


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


def require_api_key(
    settings: SettingsDep,
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """Anahtar tanımlıysa zorunlu. Tanımlı değilse yalnız debug modunda açık."""
    if not settings.api_key:
        if settings.debug:
            return
        raise AppError("API_KEY_NOT_CONFIGURED", "Sunucuda API_KEY tanımlı değil.", 503)
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise AppError("UNAUTHORIZED", "Geçersiz ya da eksik API anahtarı.", 401)


def require_local_client(request: Request) -> None:
    """Debug uçlarını yalnız aynı makineden açar."""
    host = request.client.host if request.client else ""
    if host not in LOCAL_HOSTS:
        raise AppError("FORBIDDEN", "Bu uç yalnız yerel makineden açılır.", 403)
