"""MiDaS ön işleme ve yakınlık testleri (plan D1, D3, D6)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from services.depth.base import IMAGENET_MEAN, IMAGENET_STD, crop_letterbox, preprocess_midas
from services.proximity import ProximityNormalizer, analyze_regions, box_proximity


def test_preprocess_shape_and_imagenet_norm():
    bgr = np.zeros((480, 640, 3), dtype=np.uint8)
    bgr[..., 2] = 255  # saf kırmızı (BGR)
    tensor, box = preprocess_midas(bgr)
    assert tensor.shape == (1, 3, 256, 256)
    assert tensor.dtype == np.float32
    image = tensor[0, :, box.top : box.top + box.height, box.left : box.left + box.width]
    expected_r = (1.0 - IMAGENET_MEAN[0]) / IMAGENET_STD[0]
    expected_g = (0.0 - IMAGENET_MEAN[1]) / IMAGENET_STD[1]
    assert image[0].mean() == pytest.approx(expected_r, abs=1e-4)
    assert image[1].mean() == pytest.approx(expected_g, abs=1e-4)


@pytest.mark.parametrize(("h", "w"), [(480, 640), (640, 480), (300, 300)])
def test_preprocess_keeps_aspect_ratio(h, w):
    """Dikey 3:4 kare ezilmez: görüntü alanı girdi oranını korur, dolgu ImageNet ortalaması."""
    tensor, box = preprocess_midas(np.full((h, w, 3), 200, dtype=np.uint8))
    assert max(box.height, box.width) == 256
    assert box.width / box.height == pytest.approx(w / h, rel=0.01)
    if box.top:
        assert np.all(tensor[0, :, : box.top] == 0)
    if box.left:
        assert np.all(tensor[0, :, :, : box.left] == 0)


def test_crop_letterbox_removes_padding():
    _, box = preprocess_midas(np.zeros((640, 480, 3), dtype=np.uint8))
    prediction = np.zeros((256, 256), dtype=np.float32)
    prediction[:, box.left : box.left + box.width] = 1.0
    cropped = crop_letterbox(prediction, box)
    assert cropped.shape == (box.height, box.width)
    assert np.all(cropped == 1.0)


def test_preprocess_matches_torch_style_reference():
    """Tek fonksiyon, PyTorch `small_transform` normuyla aynı tensörü üretir."""
    rng = np.random.default_rng(0)
    bgr = rng.integers(0, 256, (256, 256, 3), dtype=np.uint8)
    rgb = bgr[..., ::-1].astype(np.float32) / 255.0
    reference = ((rgb - IMAGENET_MEAN) / IMAGENET_STD).transpose(2, 0, 1)[None]
    np.testing.assert_allclose(preprocess_midas(bgr)[0], reference, atol=1e-5)


def test_window_does_not_stretch_every_frame():
    """Eski D1 hatası: her kare min-max ile yayılıyordu. Uzak sahne uzak kalmalı."""
    norm = ProximityNormalizer(window=30, warmup=1)
    near_scene = np.linspace(0, 10, 100, dtype=np.float32).reshape(10, 10)
    norm.normalize(near_scene)
    far_scene = np.full((10, 10), 1.0, dtype=np.float32) + np.linspace(0, 0.1, 100).reshape(10, 10)
    proximity = norm.normalize(far_scene.astype(np.float32))
    assert proximity.max() < 0.3


def test_regions_and_box_percentile():
    proximity = np.zeros((300, 300), dtype=np.float32)
    proximity[150:, 100:200] = 1.0  # orta-alt yakın
    regions = analyze_regions(proximity, danger=0.85, near=0.6)
    assert regions["center"].label == "çok yakın"
    assert regions["left"].label == "uzak"
    # Delikli nesne: kutunun kenarı arka plan, iç kısmı yakın.
    assert box_proximity(proximity, (100.0, 150.0, 200.0, 300.0)) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("backend", "file_name"),
    [("openvino_midas", "MiDaS_small.xml"), ("depth_anything", "depth_anything_v2_small.xml")],
)
def test_backend_selection_reports_missing_file(tmp_path, backend, file_name):
    """İki arka uç da ayardan seçilir; dosya yoksa OpenVINO yüklenmeden açık hata verir."""
    from core.config import Settings
    from services.depth import build_depth_estimator
    from services.depth.openvino_midas import ModelFileMissingError

    settings = Settings(_env_file=None, depth_backend=backend, models_dir=tmp_path)
    with pytest.raises(ModelFileMissingError, match=file_name):
        build_depth_estimator(settings)


def test_backend_none_disables_depth():
    from core.config import Settings
    from services.depth import build_depth_estimator

    assert build_depth_estimator(Settings(_env_file=None, depth_backend="none")) is None


@pytest.mark.parametrize("size", [256, 518])
def test_preprocess_supports_backend_input_sizes(size):
    tensor, box = preprocess_midas(np.zeros((640, 480, 3), dtype=np.uint8), size)
    assert tensor.shape == (1, 3, size, size)
    assert box.height == size


@pytest.mark.requires_model
def test_openvino_midas_real_model():
    from core.config import Settings
    from services.depth.openvino_midas import OpenVinoMidas

    xml = Settings(_env_file=None).midas_xml
    if not Path(xml).exists():
        pytest.skip("model indirilmemiş")
    out = OpenVinoMidas(xml, "CPU").estimate(np.zeros((240, 320, 3), dtype=np.uint8))
    assert out.shape == (240, 320)
