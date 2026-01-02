"""
Backend Configuration Management
=================================

Manages application settings from environment variables and config.yaml.
Uses Pydantic BaseSettings for validation.
"""

import os
import yaml
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["*"],  # Allow all origins in development
        env="CORS_ORIGINS"
    )
    
    # Rate limiting
    rate_limit_per_second: int = Field(default=5, env="RATE_LIMIT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Model settings (from config.yaml)
    model_type: str = "MiDaS_small"
    model_device: str = "auto"
    use_openvino: bool = False  # ✅ OpenVINO optimization
    openvino_device: str = "GPU"  # GPU, CPU, AUTO
    use_depth_anything_v2: bool = False  # ✅ Feature flag
    min_depth: float = 0.5
    max_depth: float = 5.0
    
    # Alert settings - CALIBRATED for better detection
    alert_min_distance: float = 0.5       # 0.7 -> 0.5m (only very close = danger)
    alert_warning_distance: float = 1.2   # 1.5 -> 1.2m (warning zone)
    warning_area_threshold: float = 0.10  # 0.05 -> 0.10 (10% less sensitive, fewer false positives)
    
    # Image processing
    target_width: int = 640
    target_height: int = 480
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_yaml_config()
    
    def _load_yaml_config(self):
        """Load additional settings from config.yaml."""
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        
        if not config_path.exists():
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            # Override with YAML values if present
            if yaml_data:
                # Model settings
                model_config = yaml_data.get('depth_model', {})
                if model_config:
                    self.model_type = model_config.get('model_type', self.model_type)
                    self.model_device = model_config.get('device', self.model_device)
                    self.use_openvino = model_config.get('use_openvino', self.use_openvino)
                    self.openvino_device = model_config.get('openvino_device', self.openvino_device)
                    self.min_depth = model_config.get('min_depth', self.min_depth)
                    self.max_depth = model_config.get('max_depth', self.max_depth)
                
                # Alert settings
                alert_config = yaml_data.get('alerts', {})
                if alert_config:
                    self.alert_min_distance = alert_config.get('min_distance', self.alert_min_distance)
                    self.alert_warning_distance = alert_config.get('warning_distance', self.alert_warning_distance)
                    self.warning_area_threshold = alert_config.get('warning_area_threshold', self.warning_area_threshold)
                
                # Camera settings for image processing
                camera_config = yaml_data.get('camera', {})
                if camera_config:
                    self.target_width = camera_config.get('width', self.target_width)
                    self.target_height = camera_config.get('height', self.target_height)
        
        except Exception as e:
            print(f"Warning: Failed to load config.yaml: {e}")


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
