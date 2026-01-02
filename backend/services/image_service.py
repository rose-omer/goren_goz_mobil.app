"""
Image Processing Service
=========================

Handles image encoding/decoding and colormap visualization.
Adapted from src/visualizer.py for API usage.
"""

import io
import base64
import logging
import cv2
import numpy as np
from typing import Optional, Tuple
from PIL import Image

from core.config import get_settings

logger = logging.getLogger(__name__)


class ImageService:
    """Service for image processing operations."""
    
    # OpenCV colormap mapping
    COLORMAPS = {
        "JET": cv2.COLORMAP_JET,
        "VIRIDIS": cv2.COLORMAP_VIRIDIS,
        "PLASMA": cv2.COLORMAP_PLASMA,
        "MAGMA": cv2.COLORMAP_MAGMA,
        "TURBO": cv2.COLORMAP_TURBO,
        "HOT": cv2.COLORMAP_HOT,
        "INFERNO": cv2.COLORMAP_INFERNO
    }
    
    def __init__(self):
        """Initialize image service."""
        self.settings = get_settings()
        self.target_width = self.settings.target_width
        self.target_height = self.settings.target_height
        logger.info(f"ImageService initialized: target size {self.target_width}x{self.target_height}")
    
    def decode_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Decode image from bytes with optional enhancement.
        
        Args:
            image_bytes: Image data as bytes
        
        Returns:
            Optional[np.ndarray]: BGR image or None on error
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            
            # Decode image
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Failed to decode image")
                return None
            
            # Resize to target size for consistent processing
            if image.shape[1] != self.target_width or image.shape[0] != self.target_height:
                image = cv2.resize(
                    image,
                    (self.target_width, self.target_height),
                    interpolation=cv2.INTER_LINEAR
                )
                logger.debug(f"Resized image to {self.target_width}x{self.target_height}")
            
            # Apply CLAHE for low-light enhancement
            image = self._enhance_low_light(image)
            
            return image
        
        except Exception as e:
            logger.error(f"Image decode error: {e}", exc_info=True)
            return None
    
    def _enhance_low_light(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image for low-light conditions using CLAHE.
        
        Args:
            image: BGR image
            
        Returns:
            Enhanced BGR image
        """
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Check if image is dark (needs enhancement)
            mean_brightness = np.mean(l)
            
            if mean_brightness < 100:  # Dark image threshold
                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                
                # Merge back
                lab = cv2.merge([l, a, b])
                enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                
                logger.debug(f"Applied CLAHE enhancement (brightness: {mean_brightness:.1f})")
                return enhanced
            
            return image
            
        except Exception as e:
            logger.warning(f"CLAHE enhancement failed: {e}")
            return image
    
    def encode_image_to_base64(
        self,
        image: np.ndarray,
        format: str = "JPEG",
        quality: int = 85
    ) -> Optional[str]:
        """
        Encode image to base64 string.
        
        Args:
            image: BGR image
            format: Image format (JPEG, PNG)
            quality: JPEG quality (1-100)
        
        Returns:
            Optional[str]: Base64 encoded string with data URI prefix
        """
        try:
            # Encode to JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            success, buffer = cv2.imencode('.jpg', image, encode_param)
            
            if not success:
                logger.error("Failed to encode image")
                return None
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Add data URI prefix
            data_uri = f"data:image/jpeg;base64,{image_base64}"
            
            return data_uri
        
        except Exception as e:
            logger.error(f"Image encode error: {e}", exc_info=True)
            return None
    
    def apply_colormap(
        self,
        depth_map: np.ndarray,
        colormap: str = "JET"
    ) -> Optional[np.ndarray]:
        """
        Apply colormap to depth map for visualization.
        
        Args:
            depth_map: Depth map in meters (float32)
            colormap: Colormap name (JET, VIRIDIS, etc.)
        
        Returns:
            Optional[np.ndarray]: Colored BGR image or None on error
        """
        if depth_map is None or depth_map.size == 0:
            logger.warning("Empty depth map")
            return None
        
        try:
            # Normalize depth map
            depth_min = depth_map.min()
            depth_max = depth_map.max()
            
            if depth_max - depth_min > 0:
                # Invert normalization (close = red/hot, far = blue/cold)
                depth_normalized = 1.0 - ((depth_map - depth_min) / (depth_max - depth_min))
            else:
                depth_normalized = np.zeros_like(depth_map)
            
            # Convert to uint8
            depth_uint8 = (depth_normalized * 255).astype(np.uint8)
            
            # Apply colormap
            colormap_cv = self.COLORMAPS.get(colormap.upper(), cv2.COLORMAP_JET)
            depth_colored = cv2.applyColorMap(depth_uint8, colormap_cv)
            
            return depth_colored
        
        except Exception as e:
            logger.error(f"Colormap error: {e}", exc_info=True)
            return None
    
    def create_visualization(
        self,
        depth_map: np.ndarray,
        alert_level: str,
        distance_stats: dict,
        colormap: str = "JET"
    ) -> Optional[np.ndarray]:
        """
        Create a visualization with depth map and overlay information.
        
        Args:
            depth_map: Depth map in meters
            alert_level: Alert level string
            distance_stats: Distance statistics dict
            colormap: Colormap name
        
        Returns:
            Optional[np.ndarray]: Visualization image
        """
        # Apply colormap
        depth_colored = self.apply_colormap(depth_map, colormap)
        
        if depth_colored is None:
            return None
        
        # Add text overlay
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        color = (255, 255, 255)
        
        # Alert level
        y_offset = 30
        cv2.putText(
            depth_colored,
            f"Alert: {alert_level}",
            (10, y_offset),
            font,
            font_scale,
            color,
            thickness
        )
        
        # Distance stats
        y_offset += 30
        cv2.putText(
            depth_colored,
            f"Min: {distance_stats['min']:.2f}m",
            (10, y_offset),
            font,
            font_scale,
            color,
            thickness
        )
        
        y_offset += 30
        cv2.putText(
            depth_colored,
            f"Avg: {distance_stats['avg']:.2f}m",
            (10, y_offset),
            font,
            font_scale,
            color,
            thickness
        )
        
        return depth_colored


# Singleton instance
_image_service: Optional[ImageService] = None


def get_image_service() -> ImageService:
    """Get or create image service singleton."""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
