"""Görüntü çözme ve kodlama. Yeniden boyutlandırma yok; YOLO kendi letterbox'ını yapar."""

from __future__ import annotations

import base64
import io

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from core.errors import AppError

DARK_MEAN_THRESHOLD = 60.0


def decode_image(data: bytes, max_pixels: int) -> np.ndarray:
    """JPEG/PNG baytını BGR diziye çevirir. Piksel sınırını çözmeden önce denetler."""
    if not data:
        raise AppError("EMPTY_IMAGE", "Görüntü boş.", 400)
    try:
        with Image.open(io.BytesIO(data)) as probe:
            width, height = probe.size
    except (UnidentifiedImageError, OSError) as exc:
        raise AppError("INVALID_IMAGE", "Görüntü çözülemedi.", 400) from exc
    if width * height > max_pixels:
        raise AppError("IMAGE_TOO_LARGE", "Görüntü çözünürlüğü sınırı aşıyor.", 413)

    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise AppError("INVALID_IMAGE", "Görüntü çözülemedi.", 400)
    return image


def enhance_if_dark(image: np.ndarray) -> np.ndarray:
    """Karanlık karede CLAHE uygular; aydınlık kareyi olduğu gibi döner."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if float(gray.mean()) >= DARK_MEAN_THRESHOLD:
        return image
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    light, a, b = cv2.split(lab)
    light = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(light)
    return cv2.cvtColor(cv2.merge((light, a, b)), cv2.COLOR_LAB2BGR)


def proximity_to_jpeg_base64(proximity: np.ndarray, quality: int = 70) -> str:
    """0–1 yakınlık haritasını renkli JPEG data URI'ye çevirir (yardımcı görünümü için)."""
    gray = np.clip(proximity * 255.0, 0, 255).astype(np.uint8)
    colored = cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
    ok, buf = cv2.imencode(".jpg", colored, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise AppError("ENCODE_FAILED", "Derinlik görüntüsü üretilemedi.", 500)
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")
