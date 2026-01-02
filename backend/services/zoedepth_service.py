"""
ZoeDepth Service - Metric Depth Estimation
===========================================

Absolute distance measurement in meters.
Best accuracy for visually impaired navigation.

Model: ZoeDepth-NK (NYU + KITTI trained)
Output: Real metric depth (meters)
"""

import logging
import numpy as np
import torch
import cv2
import time
from typing import Optional

from core.config import get_settings

logger = logging.getLogger(__name__)


class ZoeDepthService:
    """
    Metric depth estimation using ZoeDepth
    
    Features:
    - Absolute depth (meters, not normalized!)
    - Better accuracy than MiDaS (+10%)
    - Indoor + Outdoor capable
    - PyTorch Hub integration (easy!)
    """
    
    def __init__(self):
        """Initialize ZoeDepth service"""
        self.settings = get_settings()
        self.model = None
        self.device = 'cpu'  # CPU for now
        self.is_loaded = False
        self.model_name = 'ZoeD_NK'  # NK = NYU + KITTI
        
        # Stats
        self.total_inferences = 0
        self.total_time_ms = 0.0
    
    def load_model(self) -> bool:
        """Load ZoeDepth model from PyTorch Hub"""
        try:
            logger.info("Loading ZoeDepth model (Metric Depth)...")
            start = time.time()
            
            # Load from PyTorch Hub (automatic download!)
            repo = "isl-org/ZoeDepth"
            
            logger.info(f"  Downloading from PyTorch Hub: {repo}")
            logger.info("  This may take a few minutes on first run (~100MB)")
            
            self.model = torch.hub.load(
                repo,
                "ZoeD_NK",  # Indoor + Outdoor hybrid
                pretrained=True,
                verbose=False
            )
            
            self.model.to(self.device)
            self.model.eval()
            
            load_time = (time.time() - start) * 1000
            self.is_loaded = True
            
            logger.info(f"✓ ZoeDepth loaded successfully!")
            logger.info(f"  Model: {self.model_name} (NYU + KITTI)")
            logger.info(f"  Loading time: {load_time:.2f}ms")
            logger.info(f"  Device: {self.device}")
            logger.info(f"  Output: METRIC DEPTH (meters)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load ZoeDepth: {e}", exc_info=True)
            self.is_loaded = False
            return False
    
    def estimate(
        self,
        image: np.ndarray,
        target_size: Optional[tuple] = None
    ) -> np.ndarray:
        """
        Estimate metric depth from RGB image
        
        Args:
            image: Input image (BGR format, OpenCV style)
            target_size: Optional (width, height) to resize depth map
            
        Returns:
            Depth map in METERS (absolute distance, not normalized!)
            Example: 2.5 means 2.5 meters away
        """
        # Lazy load
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError("Failed to load ZoeDepth model")
        
        try:
            start = time.time()
            
            # Get original shape
            h, w = image.shape[:2]
            
            # Convert BGR to RGB (ZoeDepth expects RGB)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Inference - returns METRIC DEPTH (meters!)
            with torch.no_grad():
                depth_metric = self.model.infer(rgb_image)
            
            # depth_metric is already in meters (no normalization needed!)
            
            # Resize if needed
            if target_size and target_size != (w, h):
                depth_metric = cv2.resize(
                    depth_metric,
                    target_size,
                    interpolation=cv2.INTER_LINEAR
                )
            elif depth_metric.shape != (h, w):
                # If model changed size, resize back
                depth_metric = cv2.resize(
                    depth_metric,
                    (w, h),
                    interpolation=cv2.INTER_LINEAR
                )
            
            # Stats
            inference_time = (time.time() - start) * 1000
            self.total_inferences += 1
            self.total_time_ms += inference_time
            
            logger.debug(f"ZoeDepth inference: {inference_time:.2f}ms")
            logger.debug(f"  Depth range: {depth_metric.min():.2f}m - {depth_metric.max():.2f}m")
            
            return depth_metric.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Depth estimation failed: {e}", exc_info=True)
            raise
    
    def get_distance_at_point(self, depth_map: np.ndarray, x: int, y: int) -> float:
        """
        Get absolute distance in meters at specific pixel
        
        Args:
            depth_map: Depth map from estimate()
            x, y: Pixel coordinates
            
        Returns:
            Distance in meters (e.g., 2.5 means 2.5m)
        """
        h, w = depth_map.shape
        x = int(np.clip(x, 0, w-1))
        y = int(np.clip(y, 0, h-1))
        
        distance_m = depth_map[y, x]
        return float(distance_m)
    
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
            'model': 'ZoeDepth-NK',
            'depth_type': 'metric (meters)',
            'accuracy': 'SOTA (NYU-Depth V2)'
        }
