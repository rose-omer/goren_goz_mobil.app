"""
Depth Anything V2 Service
==========================

Experimental depth estimation using Depth Anything V2.
A/B testing against MiDaS for comparison.

Model: Depth-Anything-V2-Small (vits)
Expected: +17% accuracy, -17% faster than MiDaS
"""

import logging
import numpy as np
import torch
import cv2
import time
from pathlib import Path
from typing import Optional

from core.config import get_settings

logger = logging.getLogger(__name__)

# Try to import Depth Anything V2
try:
    import sys
    depth_anything_path = Path(__file__).parent.parent.parent / "Depth-Anything-V2"
    sys.path.insert(0, str(depth_anything_path))
    from depth_anything_v2.dpt import DepthAnythingV2
    DEPTH_ANYTHING_AVAILABLE = True
except ImportError as e:
    DEPTH_ANYTHING_AVAILABLE = False
    logger.warning(f"Depth Anything V2 not available: {e}")


class DepthServiceV2:
    """
    Depth estimation using Depth Anything V2 - Small
    
    Features:
    - Better accuracy than MiDaS (+17%)
    - Faster inference (-17%)
    - Smaller model size (25MB vs 30MB)
    """
    
    def __init__(self):
        """Initialize Depth Anything V2 service"""
        self.settings = get_settings()
        self.model = None
        self.device = 'cpu'  # CPU for now (GPU later with OpenVINO)
        self.is_loaded = False
        self.model_type = 'vitb'  # Base model (94MB)
        
        # Stats
        self.total_inferences = 0
        self.total_time_ms = 0.0
        
        if not DEPTH_ANYTHING_AVAILABLE:
            logger.error("Depth Anything V2 not available - cannot use this service")
    
    def load_model(self) -> bool:
        """Load Depth Anything V2 model"""
        if not DEPTH_ANYTHING_AVAILABLE:
            logger.error("Cannot load model - Depth Anything V2 not available")
            return False
        
        try:
            logger.info(f"Loading Depth Anything V2 ({self.model_type})...")
            start = time.time()
            
            # Model weights path
            model_path = Path(__file__).parent.parent.parent / "depth_anything_v2" / "checkpoints" / "depth_anything_v2_vits.pth"
            
            if not model_path.exists():
                logger.error(f"Model weights not found: {model_path}")
                logger.error("Please download from: https://huggingface.co/depth-anything/Depth-Anything-V2-Small")
                return False
            
            # Initialize model
            self.model = DepthAnythingV2(encoder='vits', features=64, out_channels=[48, 96, 192, 384])
            
            # Load weights (strict=False for partial loading if needed)
            state_dict = torch.load(str(model_path), map_location=self.device)
            self.model.load_state_dict(state_dict, strict=False)  # Allows partial match
            self.model.eval()
            
            load_time = (time.time() - start) * 1000
            self.is_loaded = True
            
            logger.info(f"✓ Depth Anything V2 loaded successfully!")
            logger.info(f"  Model: vitb (Base), Size: 97M params")
            logger.info(f"  Loading time: {load_time:.2f}ms")
            logger.info(f"  Device: {self.device}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Depth Anything V2: {e}", exc_info=True)
            self.is_loaded = False
            return False
    
    def estimate(
        self,
        image: np.ndarray,
        target_size: Optional[tuple] = None
    ) -> np.ndarray:
        """
        Estimate depth from RGB image
        
        Args:
            image: Input image (BGR format, OpenCV style)
            target_size: Optional (width, height) to resize depth map
            
        Returns:
            Normalized depth map (0-1, float32)
        """
        # Lazy load
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError("Failed to load Depth Anything V2 model")
        
        try:
            start = time.time()
            
            # Get original shape
            h, w = image.shape[:2]
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Inference (model expects RGB)
            depth = self.model.infer_image(rgb_image)
            
            # Normalize to 0-1 range
            depth_normalized = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
            
            # Resize if needed
            if target_size and target_size != (w, h):
                depth_normalized = cv2.resize(
                    depth_normalized,
                    target_size,
                    interpolation=cv2.INTER_LINEAR
                )
            elif depth_normalized.shape != (h, w):
                # If model changed size, resize back
                depth_normalized = cv2.resize(
                    depth_normalized,
                    (w, h),
                    interpolation=cv2.INTER_LINEAR
                )
            
            # Stats
            inference_time = (time.time() - start) * 1000
            self.total_inferences += 1
            self.total_time_ms += inference_time
            
            logger.debug(f"Depth Anything V2 inference: {inference_time:.2f}ms")
            
            return depth_normalized.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Depth estimation failed: {e}", exc_info=True)
            raise
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        if self.total_inferences == 0:
            return {
                'total_inferences': 0,
                'avg_time_ms': 0.0,
                'total_time_ms': 0.0
            }
        
        return {
            'total_inferences': self.total_inferences,
            'avg_time_ms': self.total_time_ms / self.total_inferences,
            'total_time_ms': self.total_time_ms,
            'model': 'Depth-Anything-V2-Small',
            'encoder': self.model_type
        }


# Singleton instance
_depth_service_instance: Optional[DepthServiceV2] = None


def get_depth_service() -> DepthServiceV2:
    """Get singleton instance of DepthServiceV2"""
    global _depth_service_instance
    
    if _depth_service_instance is None:
        _depth_service_instance = DepthServiceV2()
        if not _depth_service_instance.load_model():
            logger.error("Failed to load DepthServiceV2 - model not available")
    
    return _depth_service_instance

