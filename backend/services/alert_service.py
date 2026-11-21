"""Uyarı motoru: seviye kuralı, histerezis ve Türkçe mesaj.

Mobildeki `lib/core/hazard_engine.dart` ile aynı kural (plan 4.4).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from core.config import Settings
from services.labels import DIRECTION_TR, capitalize_tr
from services.proximity import RegionProximity


class AlertLevel(IntEnum):
    """Sıra önemli: büyük değer = ciddi."""

    CLEAR = 0
    INFO = 1
    NEAR = 2
    DANGER = 3


@dataclass(frozen=True, slots=True)
class ObjectHazard:
    """Uyarı kuralının bir nesneden okuduğu alanlar."""

    name_tr: str
    region: str
    priority: int
    ttc_s: float | None
    distance_m: float | None


@dataclass(frozen=True, slots=True)
class Assessment:
    level: AlertLevel
    message: str
    top: ObjectHazard | None
    depth_close: bool


def object_level(obj: ObjectHazard, settings: Settings) -> AlertLevel:
    """Tek nesnenin seviyesi. DANGER yalnız orta bölgede."""
    ttc, dist = obj.ttc_s, obj.distance_m
    danger = (ttc is not None and ttc < settings.danger_ttc_s) or (
        dist is not None and dist < settings.danger_distance_m
    )
    near = (ttc is not None and ttc < settings.near_ttc_s) or (
        dist is not None and dist < settings.near_distance_m
    )
    if danger and obj.region == "center":
        return AlertLevel.DANGER
    if danger or near:
        return AlertLevel.NEAR
    return AlertLevel.INFO


def assess(
    objects: list[ObjectHazard],
    regions: dict[str, RegionProximity] | None,
    settings: Settings,
    *,
    detector_ok: bool = True,
) -> Assessment:
    """Bir karenin ham seviyesi ve konuşma metni.

    `detector_ok=False`: tespit modeli yok; boş nesne listesi "nesne yok" demek değildir.
    """
    level = AlertLevel.CLEAR
    top: ObjectHazard | None = None
    for obj in objects:
        obj_level = object_level(obj, settings)
        if top is None or obj_level > level or (obj_level == level and obj.priority > top.priority):
            level, top = max(level, obj_level), obj

    center = regions.get("center") if regions else None
    depth_close = center is not None and center.close_area >= settings.proximity_area_threshold
    if depth_close and level < AlertLevel.NEAR:
        level = AlertLevel.NEAR

    message = build_message(level, top, regions, depth_close, detector_ok=detector_ok)
    return Assessment(level, message, top, depth_close)


def build_message(
    level: AlertLevel,
    top: ObjectHazard | None,
    regions: dict[str, RegionProximity] | None,
    depth_close: bool,
    *,
    detector_ok: bool = True,
) -> str:
    """Önce eylem, sonra nesne, sonra yön. Örnek: "Dur. İnsan, önde."."""
    if top is not None:
        subject = f"{capitalize_tr(top.name_tr)}, {DIRECTION_TR.get(top.region, 'önde')}"
        if top.distance_m is not None:
            subject += f", {round(top.distance_m)} metre"
        if level == AlertLevel.DANGER:
            return f"Dur. {subject}."
        if level == AlertLevel.NEAR:
            return f"Dikkat. {subject}."
        return f"{subject}."
    if depth_close:
        return "Dikkat. Önde engel."
    # "Yol açık" yalnız tespit ve derinlik ikisi de temizse (plan 9). Biri yoksa sus.
    if detector_ok and regions is not None and level == AlertLevel.CLEAR:
        return "Yol açık."
    return ""


class LevelHysteresis:
    """Seviye `raise_after` ardışık karede görülmeden yükselmez, `lower_after` karede düşmez."""

    def __init__(self, raise_after: int = 2, lower_after: int = 5) -> None:
        self.raise_after = raise_after
        self.lower_after = lower_after
        self.level = AlertLevel.CLEAR
        self._up = 0
        self._down = 0
        self._up_min = AlertLevel.DANGER
        self._down_max = AlertLevel.CLEAR

    def update(self, raw: AlertLevel) -> AlertLevel:
        if raw > self.level:
            self._down = 0
            self._up += 1
            self._up_min = min(self._up_min, raw) if self._up > 1 else raw
            if self._up >= self.raise_after:
                self.level, self._up = self._up_min, 0
        elif raw < self.level:
            self._up = 0
            self._down += 1
            self._down_max = max(self._down_max, raw) if self._down > 1 else raw
            if self._down >= self.lower_after:
                self.level, self._down = self._down_max, 0
        else:
            self._up = self._down = 0
        return self.level
