"""API yanıt şemaları (Pydantic v2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Level = Literal["CLEAR", "INFO", "NEAR", "DANGER"]
Region = Literal["left", "center", "right"]


class ErrorInfo(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorInfo


class RegionInfo(BaseModel):
    proximity: float = Field(..., ge=0, le=1, description="Göreli yakınlık; metre değildir")
    close_area: float = Field(..., ge=0, le=1, description='"Çok yakın" piksel oranı')
    label: Literal["çok yakın", "yakın", "uzak"]


class DetectedObject(BaseModel):
    name: str
    name_tr: str
    confidence: float
    bbox: list[float] = Field(..., min_length=4, max_length=4, description="[x1, y1, x2, y2]")
    center: list[float] = Field(..., min_length=2, max_length=2)
    priority: int
    region: Region
    track_id: str
    is_approaching: bool
    distance_m: float | None = Field(None, description="Nesne boyundan; odak uzaklığı verilmezse boş")
    ttc_s: float | None = Field(None, description="Çarpışmaya kalan süre (saniye)")
    proximity_label: str | None = None


class AnalysisData(BaseModel):
    alert_level: Level
    raw_level: Level
    message: str = Field(..., description="Konuşulacak Türkçe cümle; boş olabilir")
    detector_ok: bool = Field(
        ..., description='Tespit modeli çalıştı mı. False ise boş nesne listesi "yol açık" demek değildir'
    )
    objects: list[DetectedObject]
    regions: dict[Region, RegionInfo] | None = Field(
        None, description="Derinlik ısınınca dolar (ilk 10 kare boş)"
    )
    depth_image_base64: str | None = None
    timings_ms: dict[str, float] = Field(default_factory=dict)


class AnalyzeResponse(BaseModel):
    success: Literal[True] = True
    timestamp: str
    processing_time_ms: float
    data: AnalysisData


class AskResponse(BaseModel):
    success: Literal[True] = True
    answer: str
    model: str
    processing_time_ms: float
    detections_count: int
    timestamp: str


class PresetQuestionsResponse(BaseModel):
    success: Literal[True] = True
    preset_questions: dict[str, str]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    depth_loaded: bool
    detector_loaded: bool
    vlm_ready: bool | None
    vlm_model: str
    active_sessions: int
