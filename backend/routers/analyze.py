"""`POST /api/analyze`: tek kare analizi."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from core.deps import ServicesDep, SessionIdDep, check_content_length, read_limited
from core.errors import AppError
from core.limiter import analyze_limit, limiter
from core.security import require_api_key
from models.response import AnalysisData, AnalyzeResponse, DetectedObject, ErrorResponse, RegionInfo
from services.image_service import decode_image
from services.pipeline import FrameResult, analyze_frame

router = APIRouter(dependencies=[Depends(require_api_key), Depends(check_content_length)])


def to_schema(result: FrameResult) -> AnalysisData:
    objects = [
        DetectedObject(
            name=o.detection.name,
            name_tr=o.detection.name_tr,
            confidence=o.detection.confidence,
            bbox=list(o.detection.bbox),
            center=list(o.detection.center),
            priority=o.detection.priority,
            region=o.detection.region,
            track_id=o.track.track_id,
            is_approaching=o.track.is_approaching,
            distance_m=o.distance_m,
            ttc_s=None if o.track.ttc_s is None else round(o.track.ttc_s, 2),
            proximity_label=o.proximity_label,
        )
        for o in result.objects
    ]
    regions = None
    if result.regions is not None:
        regions = {
            name: RegionInfo(
                proximity=round(r.proximity, 3), close_area=round(r.close_area, 3), label=r.label
            )
            for name, r in result.regions.items()
        }
    return AnalysisData(
        alert_level=result.level.name,
        raw_level=result.raw_level.name,
        message=result.message,
        detector_ok=result.detector_ok,
        objects=objects,
        regions=regions,
        depth_image_base64=result.depth_image_base64,
        timings_ms={k: round(v, 1) for k, v in result.timings_ms.items()},
    )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Tek kareyi analiz et",
)
@limiter.limit(analyze_limit)
async def analyze_image(
    request: Request,
    services: ServicesDep,
    session: SessionIdDep,
    image: Annotated[UploadFile, File(description="JPEG/PNG, oranı korunmuş, uzun kenar ≤ 640")],
    focal_px: Annotated[float | None, Form(gt=0, description="Gönderilen karede odak uzaklığı (px)")] = None,
    include_depth_image: Annotated[bool, Form()] = False,
) -> AnalyzeResponse:
    start = time.perf_counter()
    if services.depth is None and services.detector is None:
        raise AppError("MODELS_UNAVAILABLE", "Modeller yüklenmedi. Sunucu logunu inceleyin.", 503)
    data = await read_limited(image, services.settings.max_upload_bytes)
    frame = decode_image(data, services.settings.max_image_pixels)
    state = services.sessions.get(session)
    # Çıkarım senkron; event loop'u bloke etmesin (plan E1).
    result = await run_in_threadpool(
        analyze_frame,
        services,
        state,
        frame,
        focal_px=focal_px,
        include_depth_image=include_depth_image,
    )
    return AnalyzeResponse(
        timestamp=datetime.now(UTC).isoformat(),
        processing_time_ms=round((time.perf_counter() - start) * 1000, 1),
        data=to_schema(result),
    )
