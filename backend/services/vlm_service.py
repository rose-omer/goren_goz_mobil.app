"""llama-server ile VLM sorusu. OpenAI uyumlu `/v1/chat/completions` + `image_url` (plan D10).

Tek paylaşılan `httpx.AsyncClient`; en fazla bir yeniden deneme (plan E14).
"""

from __future__ import annotations

import base64
import io
import logging
import time
from dataclasses import dataclass

import httpx
from PIL import Image

from core.config import Settings
from services.prompt_templates import FALLBACK_ANSWER, SYSTEM_PROMPT, user_text

logger = logging.getLogger(__name__)

MAX_IMAGE_SIDE = 768


class VlmUnavailableError(Exception):
    """VLM sunucusu cevap vermedi ya da hata döndü."""


@dataclass(frozen=True, slots=True)
class VlmAnswer:
    answer: str
    model: str
    elapsed_ms: float


def to_data_uri(image_bytes: bytes, max_side: int = MAX_IMAGE_SIDE) -> str:
    """Görüntüyü küçültüp JPEG data URI yapar."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        rgb = img.convert("RGB")
        rgb.thumbnail((max_side, max_side))
        out = io.BytesIO()
        rgb.save(out, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def build_payload(settings: Settings, image_uri: str, question: str, summary: str) -> dict:
    return {
        "model": settings.vlm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_uri}},
                    {"type": "text", "text": user_text(question, summary)},
                ],
            },
        ],
        "max_tokens": settings.vlm_max_tokens,
        "temperature": settings.vlm_temperature,
        "stream": False,
    }


class VlmService:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        headers = {"Authorization": f"Bearer {settings.vlm_api_key}"} if settings.vlm_api_key else {}
        self._client = client or httpx.AsyncClient(
            base_url=settings.vlm_server_url.rstrip("/"),
            timeout=settings.vlm_timeout_s,
            headers=headers,
        )
        self.last_ready: bool | None = None

    @property
    def model(self) -> str:
        return self._settings.vlm_model

    async def aclose(self) -> None:
        await self._client.aclose()

    async def check_ready(self) -> bool:
        """llama-server `/health` açık uçtur; anahtar istemez."""
        try:
            response = await self._client.get("/health", timeout=3.0)
            self.last_ready = response.status_code == 200
        except httpx.HTTPError:
            self.last_ready = False
        return self.last_ready

    async def ask(self, image_bytes: bytes, question: str, summary: str) -> VlmAnswer:
        payload = build_payload(self._settings, to_data_uri(image_bytes), question, summary)
        start = time.perf_counter()
        response = await self._post_with_one_retry(payload)
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise VlmUnavailableError("Beklenmeyen VLM cevabı") from exc
        answer = " ".join(str(content).split()) or FALLBACK_ANSWER
        self.last_ready = True
        return VlmAnswer(answer, self.model, (time.perf_counter() - start) * 1000)

    async def _post_with_one_retry(self, payload: dict) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in (1, 2):
            try:
                response = await self._client.post("/v1/chat/completions", json=payload)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                logger.warning("VLM isteği başarısız (deneme %d): %s", attempt, type(exc).__name__)
                continue
            if response.status_code >= 500:
                last_error = VlmUnavailableError(f"HTTP {response.status_code}")
                logger.warning("VLM %d döndü (deneme %d)", response.status_code, attempt)
                continue
            if response.status_code >= 400:
                # 4xx yeniden denenmez: istek ya da anahtar hatalı.
                self.last_ready = False
                raise VlmUnavailableError(f"HTTP {response.status_code}")
            return response
        self.last_ready = False
        raise VlmUnavailableError("VLM cevap vermedi") from last_error
