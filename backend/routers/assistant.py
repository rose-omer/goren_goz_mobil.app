"""VLM sorusu: `POST /api/ask_context`, `GET /api/preset_questions`."""

from __future__ import annotations

import time
from collections import deque
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from core.deps import ServicesDep, check_content_length, read_limited
from core.errors import AppError
from core.limiter import ask_limit, limiter
from core.security import require_api_key
from models.response import AskResponse, ErrorResponse, PresetQuestionsResponse
from services.image_service import decode_image
from services.prompt_templates import PRESET_QUESTIONS, summarize_objects
from services.vlm_service import VlmUnavailableError

router = APIRouter(dependencies=[Depends(require_api_key)])

# Yalnız debug modunda dolar; görüntü saklanmaz (plan G2).
HISTORY: deque[dict] = deque(maxlen=50)
MAX_QUESTION_CHARS = 300
_PRESET_TEXTS = frozenset(PRESET_QUESTIONS.values())


def masked_question(question: str) -> str:
    """Hazır soru olduğu gibi kalır; serbest soru kişisel bilgi taşıyabilir, saklanmaz."""
    text = question.strip()
    return text if text in _PRESET_TEXTS else f"[serbest soru, {len(text)} karakter]"


@router.post(
    "/ask_context",
    response_model=AskResponse,
    dependencies=[Depends(check_content_length)],
    responses={503: {"model": ErrorResponse}, 413: {"model": ErrorResponse}},
    summary="Kare hakkında Türkçe soru sor",
)
@limiter.limit(ask_limit)
async def ask_context(
    request: Request,
    services: ServicesDep,
    image: Annotated[UploadFile, File()],
    question: Annotated[str, Form(min_length=1, max_length=MAX_QUESTION_CHARS)],
) -> AskResponse:
    start = time.perf_counter()
    data = await read_limited(image, services.settings.max_upload_bytes)
    frame = decode_image(data, services.settings.max_image_pixels)

    # Önbellek yok: aynı karede YOLO (plan D13).
    detections = []
    if services.detector is not None:
        detections = await run_in_threadpool(services.detector.detect, frame)
    summary = summarize_objects((d.name_tr, d.region, None) for d in detections)

    try:
        result = await services.vlm.ask(data, question, summary)
    except VlmUnavailableError as exc:
        raise AppError("VLM_UNAVAILABLE", "Soru sorma şu an kullanılamıyor.", 503) from exc

    elapsed = round((time.perf_counter() - start) * 1000, 1)
    now = datetime.now(UTC).isoformat()
    if services.settings.debug:
        HISTORY.append(
            {
                "timestamp": now,
                "question": masked_question(question),
                "answer": result.answer,
                "processing_time_ms": elapsed,
            }
        )
    return AskResponse(
        answer=result.answer,
        model=result.model,
        processing_time_ms=elapsed,
        detections_count=len(detections),
        timestamp=now,
    )


@router.get("/preset_questions", response_model=PresetQuestionsResponse)
async def preset_questions() -> PresetQuestionsResponse:
    return PresetQuestionsResponse(preset_questions=PRESET_QUESTIONS)
