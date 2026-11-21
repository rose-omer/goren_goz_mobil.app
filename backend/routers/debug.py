"""Debug uçları. Yalnız `DEBUG=true` iken eklenir ve yalnız yerelden açılır (plan G1, G2, G10)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from core.security import require_local_client
from routers.assistant import HISTORY

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

router = APIRouter(dependencies=[Depends(require_local_client)], include_in_schema=False)


@router.get("/monitor")
async def monitor_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "monitor.html", media_type="text/html; charset=utf-8")


@router.get("/api/ask_context_history")
async def ask_history() -> dict:
    items = list(HISTORY)
    return {"success": True, "count": len(items), "history": items}
