"""Türkçe sınıf adları, öncelik ve gerçek boy tablosu."""

from __future__ import annotations

TURKISH_LABELS: dict[str, str] = {
    "person": "insan",
    "bicycle": "bisiklet",
    "car": "araç",
    "motorcycle": "motosiklet",
    "bus": "otobüs",
    "truck": "kamyon",
    "train": "tren",
    "traffic light": "trafik ışığı",
    "fire hydrant": "yangın musluğu",
    "stop sign": "dur levhası",
    "parking meter": "park sayacı",
    "bench": "bank",
    "dog": "köpek",
    "cat": "kedi",
    "chair": "sandalye",
    "couch": "kanepe",
    "bed": "yatak",
    "dining table": "masa",
    "potted plant": "saksı",
    "backpack": "sırt çantası",
    "umbrella": "şemsiye",
    "handbag": "el çantası",
    "suitcase": "valiz",
    "refrigerator": "buzdolabı",
    "tv": "televizyon",
    "toilet": "klozet",
    "sink": "lavabo",
    "bottle": "şişe",
    "skateboard": "kaykay",
    "sports ball": "top",
    # 12 sınıflı Türkiye modeli (training/configs/dataset.yaml).
    "vehicle": "araç",
    "pole": "direk",
    "stairs": "merdiven",
    "pothole": "çukur",
    "obstacle": "engel",
    "traffic_sign_tr": "levha",
    "crosswalk": "yaya geçidi",
    "curb": "bordür",
    "construction": "inşaat alanı",
}

PRIORITY: dict[str, int] = {
    "person": 10,
    "car": 10,
    "vehicle": 10,
    "construction": 9,
    "obstacle": 9,
    "truck": 10,
    "bus": 10,
    "motorcycle": 10,
    "bicycle": 9,
    "stairs": 10,
    "pothole": 10,
    "curb": 9,
    "pole": 9,
    "fire hydrant": 8,
    "bench": 8,
    "chair": 8,
    "dining table": 8,
    "parking meter": 8,
    "traffic light": 7,
    "stop sign": 7,
    "dog": 7,
    "couch": 7,
    "bed": 7,
    "refrigerator": 7,
    "potted plant": 6,
    "backpack": 6,
    "suitcase": 6,
    "umbrella": 6,
    "cat": 5,
    "skateboard": 5,
}
DEFAULT_PRIORITY = 4

# Nesne boyuyla mesafe için ortalama gerçek yükseklik (metre). Direk gibi değişken boylu
# sınıflar bilerek yok (plan 4.2).
REAL_HEIGHT_M: dict[str, float] = {
    "person": 1.70,
    "car": 1.50,
    "vehicle": 1.50,
    "bicycle": 1.05,
    "motorcycle": 1.10,
    "bus": 3.00,
    "truck": 3.00,
    "dog": 0.55,
    "chair": 0.90,
}

DIRECTION_TR: dict[str, str] = {"left": "solda", "center": "önde", "right": "sağda"}


def turkish_name(name: str) -> str:
    return TURKISH_LABELS.get(name, name)


def priority_of(name: str) -> int:
    return PRIORITY.get(name, DEFAULT_PRIORITY)


def capitalize_tr(text: str) -> str:
    """Türkçe ilk harf büyütme: "insan" -> "İnsan" (str.capitalize "Insan" yapar)."""
    if not text:
        return text
    first = {"i": "İ", "ı": "I"}.get(text[0], text[0].upper())
    return first + text[1:]
