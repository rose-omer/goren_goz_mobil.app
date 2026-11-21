"""Oturum başına nesne takibi ve çarpışmaya kalan süre (TTC).

TTC metre gerektirmez: kutu yüksekliği h için TTC ≈ h / (dh/dt) (plan 4.4).
"""

from __future__ import annotations

import itertools
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from services.alert_service import LevelHysteresis
from services.detection import Detection
from services.proximity import ProximityNormalizer

EMA_ALPHA = 0.5
MIN_GROWTH_PER_S = 0.02  # h'nin saniyede %2'sinden az büyüme yaklaşma sayılmaz
MAX_TTC_S = 30.0


@dataclass(slots=True)
class _Track:
    track_id: str
    name: str
    bbox: tuple[float, float, float, float]
    height: float
    last_t: float
    hits: int = 1
    growth: float = 0.0  # dh/dt, piksel/saniye (üstel düzleştirilmiş)


@dataclass(frozen=True, slots=True)
class TrackInfo:
    track_id: str
    ttc_s: float | None
    is_approaching: bool
    hits: int


def iou(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter <= 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


class Tracker:
    """Basit IoU eşleştirmeli takipçi. Çıktı sırası girdi sırasıdır (plan D8)."""

    def __init__(self, iou_threshold: float = 0.3, max_age_s: float = 2.0) -> None:
        self.iou_threshold = iou_threshold
        self.max_age_s = max_age_s
        self._tracks: list[_Track] = []
        self._ids = itertools.count(1)

    def update(self, detections: list[Detection], now: float) -> list[TrackInfo]:
        self._tracks = [t for t in self._tracks if now - t.last_t <= self.max_age_s]
        free = set(range(len(self._tracks)))
        infos: list[TrackInfo] = []

        for det in detections:
            best, best_iou = None, self.iou_threshold
            for idx in free:
                track = self._tracks[idx]
                if track.name != det.name:
                    continue
                score = iou(track.bbox, det.bbox)
                if score >= best_iou:
                    best, best_iou = idx, score
            height = max(det.bbox[3] - det.bbox[1], 1.0)

            if best is None:
                track = _Track(f"t{next(self._ids)}", det.name, det.bbox, height, now)
                self._tracks.append(track)
            else:
                free.discard(best)
                track = self._tracks[best]
                dt = now - track.last_t
                if dt > 1e-3:
                    rate = (height - track.height) / dt
                    track.growth = EMA_ALPHA * rate + (1 - EMA_ALPHA) * track.growth
                track.bbox, track.height, track.last_t = det.bbox, height, now
                track.hits += 1
            infos.append(_info(track))
        return infos


def _info(track: _Track) -> TrackInfo:
    ttc = None
    approaching = track.hits >= 2 and track.growth > MIN_GROWTH_PER_S * track.height
    if approaching:
        ttc = min(track.height / track.growth, MAX_TTC_S)
    return TrackInfo(track.track_id, ttc, approaching, track.hits)


@dataclass(slots=True)
class SessionState:
    """Bir istemcinin takip, yakınlık ve histerezis durumu."""

    tracker: Tracker
    proximity: ProximityNormalizer
    hysteresis: LevelHysteresis
    last_seen: float = field(default_factory=time.monotonic)
    # Aynı oturumdan eşzamanlı iki kare durumu bozmasın.
    lock: threading.Lock = field(default_factory=threading.Lock)


class SessionStore:
    """`X-Session-Id` başına durum. TTL dolan oturum silinir (plan E3).

    `X-Session-Id` istemci denetimlidir. Sözlük `max_sessions` ile sınırlı; dolunca en uzun
    süredir görülmeyen oturum atılır.
    """

    def __init__(
        self, factory: Callable[[], SessionState], ttl_s: float = 60.0, max_sessions: int = 256
    ) -> None:
        self._factory = factory
        self._ttl_s = ttl_s
        self._max_sessions = max(max_sessions, 1)
        self._sessions: dict[str, SessionState] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> SessionState:
        now = time.monotonic()
        with self._lock:
            expired = [k for k, v in self._sessions.items() if now - v.last_seen > self._ttl_s]
            for key in expired:
                del self._sessions[key]
            state = self._sessions.get(session_id)
            if state is None:
                if len(self._sessions) >= self._max_sessions:
                    oldest = min(self._sessions, key=lambda k: self._sessions[k].last_seen)
                    del self._sessions[oldest]
                state = self._factory()
                self._sessions[session_id] = state
            state.last_seen = now
            return state

    def __len__(self) -> int:
        return len(self._sessions)
