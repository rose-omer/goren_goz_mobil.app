"""Uyarı kuralı, histerezis ve TTC testleri."""

from __future__ import annotations

import pytest

from core.config import Settings
from services.alert_service import AlertLevel, LevelHysteresis, ObjectHazard, assess, object_level
from services.detection import Detection
from services.proximity import RegionProximity
from services.tracking import Tracker

S = Settings(_env_file=None)


def hazard(region="center", ttc=None, dist=None, name="insan", priority=10) -> ObjectHazard:
    return ObjectHazard(name, region, priority, ttc, dist)


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        (hazard(ttc=1.5), AlertLevel.DANGER),
        (hazard(dist=0.8), AlertLevel.DANGER),
        (hazard(region="left", ttc=1.5), AlertLevel.NEAR),
        (hazard(ttc=3.0), AlertLevel.NEAR),
        (hazard(dist=1.5), AlertLevel.NEAR),
        (hazard(ttc=8.0, dist=5.0), AlertLevel.INFO),
        (hazard(), AlertLevel.INFO),
    ],
    ids=["ttc-danger", "dist-danger", "side-capped", "ttc-near", "dist-near", "far", "no-signal"],
)
def test_object_level(obj, expected):
    assert object_level(obj, S) == expected


def test_near_band_is_reachable():
    """Eski D2 hatası: orta bant maskesi hep boştu. Yeni kural NEAR'a ulaşır."""
    result = assess([hazard(dist=1.9)], None, S)
    assert result.level == AlertLevel.NEAR
    assert result.message == "Dikkat. İnsan, önde, 2 metre."


def test_message_puts_action_first():
    assert assess([hazard(ttc=1.0)], None, S).message == "Dur. İnsan, önde."
    side = assess([hazard(region="right", ttc=3.0, name="direk")], None, S)
    assert side.message == "Dikkat. Direk, sağda."


def test_clear_path_only_when_depth_is_known():
    regions = {r: RegionProximity(0.2, 0.0, "uzak") for r in ("left", "center", "right")}
    assert assess([], regions, S).message == "Yol açık."
    # Derinlik yoksa "Yol açık" denmez: yanlış güven riski.
    assert assess([], None, S).message == ""


def test_no_clear_path_without_detector():
    """Tespit modeli yoksa boş nesne listesi "yol açık" demek değildir (plan 9)."""
    regions = {r: RegionProximity(0.2, 0.0, "uzak") for r in ("left", "center", "right")}
    result = assess([], regions, S, detector_ok=False)
    assert result.level == AlertLevel.CLEAR
    assert result.message == ""


def test_close_depth_in_center_raises_to_near():
    regions = {
        "left": RegionProximity(0.2, 0.0, "uzak"),
        "center": RegionProximity(0.95, 0.3, "çok yakın"),
        "right": RegionProximity(0.2, 0.0, "uzak"),
    }
    result = assess([], regions, S)
    assert result.level == AlertLevel.NEAR
    assert result.message == "Dikkat. Önde engel."


def test_highest_level_object_wins():
    result = assess([hazard(region="left", name="bank"), hazard(ttc=1.0, name="araç")], None, S)
    assert result.top is not None and result.top.name_tr == "araç"


def test_hysteresis_raises_after_two_and_lowers_after_five():
    h = LevelHysteresis(raise_after=2, lower_after=5)
    assert h.update(AlertLevel.DANGER) == AlertLevel.CLEAR
    assert h.update(AlertLevel.DANGER) == AlertLevel.DANGER
    for _ in range(4):
        assert h.update(AlertLevel.CLEAR) == AlertLevel.DANGER
    assert h.update(AlertLevel.CLEAR) == AlertLevel.CLEAR


def test_hysteresis_ignores_single_spike():
    h = LevelHysteresis()
    h.update(AlertLevel.DANGER)
    assert h.update(AlertLevel.CLEAR) == AlertLevel.CLEAR


def test_hysteresis_raises_to_lowest_level_in_streak():
    h = LevelHysteresis()
    h.update(AlertLevel.DANGER)
    assert h.update(AlertLevel.NEAR) == AlertLevel.NEAR


def test_ttc_from_growing_box():
    tracker = Tracker(max_age_s=5.0)
    infos = []
    for step in range(6):
        h = 100 + 50 * step
        det = Detection("person", 0.9, (300.0, 400.0 - h, 340.0, 400.0), "center")
        infos = tracker.update([det], now=float(step))
    last = infos[0]
    # Son kare: h = 350, dh/dt = 50 px/s → TTC ≈ 7 s.
    assert last.is_approaching
    assert last.ttc_s == pytest.approx(7.0, rel=0.05)


def test_static_box_is_not_approaching():
    tracker = Tracker()
    det = Detection("chair", 0.8, (100.0, 100.0, 200.0, 300.0), "left")
    tracker.update([det], now=0.0)
    info = tracker.update([det], now=0.5)[0]
    assert not info.is_approaching
    assert info.ttc_s is None


def test_tracker_keeps_two_same_class_objects_apart():
    """Eski D8 hatası: aynı sınıftan iki nesne aynı track_id alıyordu."""
    tracker = Tracker()
    a = Detection("person", 0.9, (10.0, 10.0, 60.0, 200.0), "left")
    b = Detection("person", 0.9, (500.0, 10.0, 560.0, 200.0), "right")
    first = tracker.update([a, b], now=0.0)
    second = tracker.update([a, b], now=0.5)
    assert first[0].track_id != first[1].track_id
    assert [i.track_id for i in second] == [i.track_id for i in first]
