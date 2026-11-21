"""Uygulama ayarları: tek kaynak pydantic-settings v2.

Öncelik sırası: ortam değişkeni > `.env` > `config.yaml` > varsayılan.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import (
    BaseSettings,
    NoDecode,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
YAML_PATH = BACKEND_DIR / "config.yaml"

# Planın önerdiği aday setin ilki. Türkçe ölçümden sonra VLM_MODEL ile değiştir.
DEFAULT_VLM_MODEL = "SmolVLM2-500M-Video-Instruct"


class Settings(BaseSettings):
    """Bütün çalışma ayarları. Alan adı = ortam değişkeni adı (büyük harf)."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        yaml_file=YAML_PATH,
        yaml_file_encoding="utf-8",
    )

    # Sunucu
    host: str = "127.0.0.1"
    port: int = 8110
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Güvenlik
    api_key: str = ""
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(
        default=300,
        validation_alias=AliasChoices("rate_limit_per_minute", "RATE_LIMIT_PER_MINUTE", "RATE_LIMIT"),
    )
    ask_rate_limit_per_minute: int = 10
    max_upload_bytes: int = 5 * 1024 * 1024
    max_image_pixels: int = 4_000_000

    # Modeller
    models_dir: Path = BACKEND_DIR / "model_files"
    depth_backend: Literal["openvino_midas", "depth_anything", "none"] = "openvino_midas"
    openvino_device: str = "AUTO"
    midas_model_name: str = "MiDaS_small"
    depth_anything_model_name: str = "depth_anything_v2_small"
    yolo_model_path: Path | None = None
    detection_confidence: float = 0.5
    max_objects: int = 10

    # Uyarı motoru
    danger_ttc_s: float = 2.0
    near_ttc_s: float = 4.0
    danger_distance_m: float = 1.0
    near_distance_m: float = 2.0
    proximity_danger: float = 0.85
    proximity_near: float = 0.6
    proximity_area_threshold: float = 0.10
    raise_after_frames: int = 2
    lower_after_frames: int = 5
    session_ttl_s: float = 60.0
    max_sessions: int = Field(256, ge=1)

    # VLM (llama-server, OpenAI uyumlu uç)
    vlm_server_url: str = "http://127.0.0.1:8120"
    vlm_api_key: str = ""
    vlm_model: str = DEFAULT_VLM_MODEL
    vlm_timeout_s: float = 30.0
    vlm_max_tokens: int = 48
    vlm_temperature: float = 0.2

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """`CORS_ORIGINS=a,b` biçimini listeye çevirir."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def midas_xml(self) -> Path:
        return self.models_dir / "openvino" / f"{self.midas_model_name}.xml"

    @property
    def depth_anything_xml(self) -> Path:
        return self.models_dir / "openvino" / f"{self.depth_anything_model_name}.xml"

    @property
    def yolo_path(self) -> Path:
        return self.yolo_model_path or self.models_dir / "yolo26n.pt"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Süreç başına tek ayar nesnesi."""
    return Settings()
