"""Ortak FastAPI bağımlılıkları."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, Request

from core.errors import AppError
from services.container import Services

MAX_SESSION_ID = 64


def get_services(request: Request) -> Services:
    return request.app.state.services


ServicesDep = Annotated[Services, Depends(get_services)]


def session_id(x_session_id: Annotated[str | None, Header()] = None) -> str:
    """İstemci oturumu. Başlık yoksa ortak "default" oturumu kullanılır."""
    value = (x_session_id or "default").strip()[:MAX_SESSION_ID]
    return value or "default"


SessionIdDep = Annotated[str, Depends(session_id)]


def check_content_length(request: Request) -> None:
    """Gövde tümüyle okunmadan boyutu denetler (plan E5)."""
    limit = request.app.state.settings.max_upload_bytes
    raw = request.headers.get("content-length")
    if raw is not None and raw.isdigit() and int(raw) > limit + 64 * 1024:
        raise AppError("IMAGE_TOO_LARGE", "Görüntü boyut sınırını aşıyor.", 413)


async def read_limited(upload, limit: int) -> bytes:
    """Yüklemeyi sınırı aşmadan okur."""
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise AppError("IMAGE_TOO_LARGE", "Görüntü boyut sınırını aşıyor.", 413)
    return data
