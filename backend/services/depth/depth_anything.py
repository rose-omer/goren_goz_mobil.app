"""Depth Anything V2 Small, OpenVINO IR arka ucu (plan 4.5). Yeni bağımlılık yok.

Çıktı MiDaS gibi göreli ters derinliktir (büyük = yakın); ön işleme aynıdır (ImageNet normu,
oran korunur). Girdi kenarı 14'ün katıdır (genelde 518) ve IR'den okunur. Small modeli
Apache-2.0; Base/Large CC-BY-NC, kullanma (docs/MODELS.md).
"""

from __future__ import annotations

from services.depth.openvino_midas import OpenVinoMidas


class OpenVinoDepthAnything(OpenVinoMidas):
    name = "depth_anything"
    default_input_size = 518
