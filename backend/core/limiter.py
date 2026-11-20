"""Tek hız sınırlayıcı. Anahtar: API anahtarı > IP.

`X-Session-Id` anahtar olmaz: istemci her istekte yeni değer gönderip sınırı atlayabilir.
"""

from __future__ import annotations

import hashlib

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from core.config import Settings

limiter = Limiter(key_func=lambda request: rate_key(request))
_limits = {"analyze": "300/minute", "ask": "10/minute"}


def rate_key(request: Request) -> str:
    api_key = request.headers.get("x-api-key")
    if api_key:
        # Anahtarın kendisini sayaç anahtarı olarak bellekte tutma.
        return "k:" + hashlib.sha256(api_key.encode()).hexdigest()[:16]
    return "ip:" + get_remote_address(request)


def configure_limiter(settings: Settings) -> None:
    """Sınırları ayardan alır. 0 değeri sınırı kapatır."""
    _limits["analyze"] = f"{max(settings.rate_limit_per_minute, 1)}/minute"
    _limits["ask"] = f"{max(settings.ask_rate_limit_per_minute, 1)}/minute"
    limiter.enabled = settings.rate_limit_per_minute > 0


def analyze_limit() -> str:
    return _limits["analyze"]


def ask_limit() -> str:
    return _limits["ask"]
