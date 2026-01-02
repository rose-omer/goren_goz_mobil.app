"""
Alert Service
=============

Analyzes depth maps and generates collision warnings.
Adapted from src/alert_system.py for API usage.
"""

import logging
import numpy as np
from enum import Enum
from typing import Dict, List, Optional

from core.config import get_settings

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels."""
    SAFE = "SAFE"
    FAR = "FAR"
    MEDIUM = "MEDIUM"
    NEAR = "NEAR"
    DANGER = "DANGER"


class AlertService:
    """
    Service for analyzing depth maps and generating alerts.
    
    Stateless design for API usage - each call is independent.
    """
    
    def __init__(self):
        """Initialize alert service."""
        self.settings = get_settings()
        self.min_distance = self.settings.alert_min_distance
        self.warning_distance = self.settings.alert_warning_distance
        self.warning_area_threshold = self.settings.warning_area_threshold
        
        logger.info(
            f"AlertService initialized: "
            f"min={self.min_distance}m, warning={self.warning_distance}m, "
            f"threshold={self.warning_area_threshold*100}%"
        )
    
    def analyze_depth(self, depth_map: np.ndarray) -> Dict:
        """
        Analyze depth map and generate alert response with regional zones.
        
        Args:
            depth_map: Depth map in meters (float32)
        
        Returns:
            Dict containing:
                - alert_level: AlertLevel enum
                - distance_stats: {min, max, avg}
                - warnings: List of warning messages
                - area_percentages: Dict of area ratios per level
                - regional_alerts: {left, center, right} zone analysis
        """
        if depth_map is None or depth_map.size == 0:
            return self._safe_response()
        
        try:
            # Filter invalid values
            valid_depth = depth_map[np.isfinite(depth_map)]
            if valid_depth.size == 0:
                return self._safe_response()
            
            # Calculate distance statistics
            min_dist = float(np.min(valid_depth))
            max_dist = float(np.max(valid_depth))
            avg_dist = float(np.mean(valid_depth))
            
            # Regional analysis (divide into left, center, right)
            regional_alerts = self._analyze_regions(depth_map)
            
            # Analyze danger zones
            total_pixels = depth_map.size
            danger_mask = depth_map < self.min_distance
            near_mask = (depth_map >= self.min_distance) & (depth_map < self.warning_distance)
            medium_mask = (depth_map >= self.warning_distance) & (depth_map < 2.0)
            
            danger_ratio = float(np.sum(danger_mask) / total_pixels)
            near_ratio = float(np.sum(near_mask) / total_pixels)
            medium_ratio = float(np.sum(medium_mask) / total_pixels)
            
            # Determine alert level and generate warnings
            warnings = []
            
            if danger_ratio > self.warning_area_threshold:
                alert_level = AlertLevel.DANGER
                warnings.append({
                    "message": f"DANGER! Object detected at {min_dist:.2f}m",
                    "level": "DANGER",
                    "distance": min_dist,
                    "area_percentage": danger_ratio * 100
                })
                logger.warning(f"⚠️ DANGER alert: {min_dist:.2f}m ({danger_ratio*100:.1f}% area)")
            
            elif near_ratio > self.warning_area_threshold:
                alert_level = AlertLevel.NEAR
                warnings.append({
                    "message": f"WARNING! Near object at {min_dist:.2f}m",
                    "level": "NEAR",
                    "distance": min_dist,
                    "area_percentage": near_ratio * 100
                })
                logger.info(f"⚠️ NEAR alert: {min_dist:.2f}m ({near_ratio*100:.1f}% area)")
            
            elif medium_ratio > self.warning_area_threshold:
                alert_level = AlertLevel.MEDIUM
                warnings.append({
                    "message": f"CAUTION! Medium distance {min_dist:.2f}m",
                    "level": "MEDIUM",
                    "distance": min_dist,
                    "area_percentage": medium_ratio * 100
                })
            
            elif avg_dist < 3.0:
                alert_level = AlertLevel.FAR
            
            else:
                alert_level = AlertLevel.SAFE
            
            return {
                "alert_level": alert_level,
                "distance_stats": {
                    "min": min_dist,
                    "max": max_dist,
                    "avg": avg_dist
                },
                "warnings": warnings,
                "area_percentages": {
                    "danger": danger_ratio * 100,
                    "near": near_ratio * 100,
                    "medium": medium_ratio * 100
                },
                "regional_alerts": regional_alerts
            }
        
        except Exception as e:
            logger.error(f"Alert analysis error: {e}", exc_info=True)
            return self._safe_response()
    
    def _analyze_regions(self, depth_map: np.ndarray) -> Dict:
        """
        Analyze depth map by regions (left, center, right).
        
        Args:
            depth_map: Depth map in meters
            
        Returns:
            Dict with regional analysis
        """
        height, width = depth_map.shape
        third = width // 3
        
        # Split into regions
        left_region = depth_map[:, :third]
        center_region = depth_map[:, third:2*third]
        right_region = depth_map[:, 2*third:]
        
        # Analyze each region
        regions = {
            "left": self._analyze_single_region(left_region, "left"),
            "center": self._analyze_single_region(center_region, "center"),
            "right": self._analyze_single_region(right_region, "right")
        }
        
        return regions
    
    def _analyze_single_region(self, region: np.ndarray, region_name: str) -> Dict:
        """
        Analyze a single region for obstacles.
        
        Args:
            region: Depth map region
            region_name: Name of the region
            
        Returns:
            Dict with region analysis
        """
        valid_depth = region[np.isfinite(region)]
        if valid_depth.size == 0:
            return {
                "alert_level": "SAFE",
                "min_distance": 5.0,
                "has_obstacle": False,
                "message": ""
            }
        
        min_dist = float(np.min(valid_depth))
        avg_dist = float(np.mean(valid_depth))
        
        # Calculate danger ratio in this region
        total_pixels = region.size
        danger_mask = region < self.min_distance
        near_mask = (region >= self.min_distance) & (region < self.warning_distance)
        
        danger_ratio = float(np.sum(danger_mask) / total_pixels)
        near_ratio = float(np.sum(near_mask) / total_pixels)
        
        # Determine alert level for this region
        if danger_ratio > self.warning_area_threshold * 0.5:  # Lower threshold for regions
            alert_level = "DANGER"
            has_obstacle = True
            message = f"{min_dist:.1f}m"
        elif near_ratio > self.warning_area_threshold * 0.5:
            alert_level = "NEAR"
            has_obstacle = True
            message = f"{min_dist:.1f}m"
        elif avg_dist < 2.0:
            alert_level = "MEDIUM"
            has_obstacle = True
            message = f"{avg_dist:.1f}m"
        else:
            alert_level = "SAFE"
            has_obstacle = False
            message = ""
        
        return {
            "alert_level": alert_level,
            "min_distance": min_dist,
            "avg_distance": avg_dist,
            "has_obstacle": has_obstacle,
            "message": message,
            "danger_percentage": danger_ratio * 100,
            "near_percentage": near_ratio * 100
        }
    
    def _safe_response(self) -> Dict:
        """Return a safe/default response."""
        return {
            "alert_level": AlertLevel.SAFE,
            "distance_stats": {
                "min": 5.0,
                "max": 5.0,
                "avg": 5.0
            },
            "warnings": [],
            "area_percentages": {
                "danger": 0.0,
                "near": 0.0,
                "medium": 0.0
            },
            "regional_alerts": {
                "left": {"alert_level": "SAFE", "min_distance": 5.0, "has_obstacle": False, "message": ""},
                "center": {"alert_level": "SAFE", "min_distance": 5.0, "has_obstacle": False, "message": ""},
                "right": {"alert_level": "SAFE", "min_distance": 5.0, "has_obstacle": False, "message": ""}
            }
        }


# Singleton instance
_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    """Get or create alert service singleton."""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
